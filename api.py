"""
三国文字Roguelike - Web API Layer
Wraps SanguoEngine as a REST API, returns JSON.
"""
import sys
import os
import io
import json
import random
from io import StringIO
from functools import wraps
from contextlib import redirect_stdout

# Add game directory to path
GAME_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, GAME_DIR)

import config
from engine import SanguoEngine
from combat import COMBAT_ACTIONS
from skills import get_skill
from world import get_adjacent_cities, find_path, REGIONS, CITY_CONNECTIONS
from npc_schedule import is_npc_active, get_npc_location, is_faction_leader
from achievements import ACHIEVEMENTS, load_achievements, get_achievement_by_id


def capture_output(func):
    """Decorator: capture stdout from a function call and return it as a string."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        old_stdout = sys.stdout
        sys.stdout = StringIO()
        try:
            result = func(*args, **kwargs)
            output = sys.stdout.getvalue()
        finally:
            sys.stdout = old_stdout
        return output, result
    return wrapper


def capture_all(func):
    """Decorator: also capture print() calls during func execution."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        old = sys.stdout
        sys.stdout = buff = StringIO()
        try:
            result = func(*args, **kwargs)
        finally:
            sys.stdout = old
        return buff.getvalue(), result
    return wrapper


class SanguoAPI:
    """Clean JSON API around SanguoEngine."""

    def __init__(self):
        self.engine = SanguoEngine(silent=True)
        self._history = []  # narrative history for scrollback

    def _add_narrative(self, text):
        if text and text.strip():
            self._history.append(text.strip())

    def new_game(self):
        """Start a new game."""
        self.engine.new_game()
        self._history = []
        self._add_narrative("⚔️  三国文字Roguelike ⚔️\n黄巾乱世，英雄四起。你的命运，将走向何方？")
        return self.get_state()

    def tick(self):
        """Advance one month."""
        old_stdout = sys.stdout
        sys.stdout = StringIO()
        try:
            result = self.engine.tick()
        finally:
            sys.stdout = old_stdout

        if result is None:
            if self.engine.state.is_game_over():
                return self._game_over()
            return self.get_state()

        # Build narrative
        lines = []
        for key in ["mandatory", "conditionals", "random_events"]:
            for evt in (result.get(key) or []):
                    name = evt.get("name", "")
                    desc = evt.get("desc", "")
                    if name and desc:
                        lines.append(f"✨【{name}】{desc}")
            if result.get("combat"):
                enemy = result["combat"]["enemy"]
                lines.append(f"\n⚔️  {enemy.narrative}")
            if result.get("npc_encounter"):
                enc = result["npc_encounter"]
                npc = enc["npc"]
                lines.append(f"\n🎭 {npc.name}（{npc.rank}）正在此处。")

        self._add_narrative("\n".join(lines))
        return self.get_state()

    def _game_over(self):
        """Handle game over state: build death shop data and set ui_state=death."""
        p = self.engine.state.player
        cause = "陨落" if p.hp <= 0 else "三国鼎立"
        if p.hp <= 0:
            self._add_narrative(f"\n💀 你已陨于乱世。存活：{self.engine.state.get_time_str()}")
        else:
            self._add_narrative(f"\n🏯 三国鼎立，乱世收场。你的故事止于{self.engine.state.get_time_str()}。")

        # Build death shop data
        self.engine.pending_death_shop = self._build_death_shop_data()
        return self.get_state()

    def get_state(self):
        """Get current full game state as JSON-serializable dict."""
        if not self.engine.state or not self.engine.state.player:
            return {"game_status": "no_game", "ui_state": "start"}

        p = self.engine.state.player
        state = self.engine.state

        # Determine UI state
        ui_state = "normal"
        combat_data = None
        npc_data = None

        if self.engine.pending_combat:
            ui_state = "combat"
            enemy = self.engine.pending_combat["enemy"]
            ctx = self.engine.pending_combat["ctx"]

            # Combat actions
            actions = []
            for i, (name, data) in enumerate(COMBAT_ACTIONS.items(), 1):
                desc = data["description"]
                intel_req = data.get("requires_intel", 0)
                req_note = f"（需智{int(intel_req)}）" if intel_req else ""
                actions.append({
                    "id": str(i),
                    "label": name,
                    "desc": f"{desc}{req_note}",
                    "win_rate_mod": data["win_rate_mod"],
                })

            # Active skills
            usable_skills = []
            for sid in p.active_skills:
                sk = get_skill(sid)
                if not sk:
                    continue
                if sk.stat_req:
                    if not all(p.get_stat(s) >= r for s, r in sk.stat_req.items()):
                        continue
                usable_skills.append({
                    "id": sid,
                    "name": sk.name,
                    "desc": sk.desc,
                    "skill_type": sk.skill_type,          # "active" | "passive"
                    "cost": sk.cost,                       # 碎片消耗，NPC赠送为0
                    "stat_req": sk.stat_req or {},         # 属性要求
                    "rank_req": sk.rank_req or None,       # 官职要求
                    "prereq": sk.prereq or None,           # 前置技能ID
                })

            combat_data = {
                "enemy": {
                    "name": enemy.name,
                    "troops": enemy.troops,
                    "morale": enemy.morale,
                    "terrain": ctx.get("terrain", "平原"),
                },
                "player_army": ctx.get("attacker_troops", 0),
                "player_morale": ctx.get("attacker_morale", 80),
                "actions": actions,
                "skills": usable_skills,
            }

        elif self.engine.pending_npc_encounter:
            ui_state = "npc"
            enc = self.engine.pending_npc_encounter
            npc = enc["npc"]
            rel = p.get_relation(npc.name)

            # Determine relation tag
            if rel >= 70:
                rel_tag = "【亲密】"
            elif rel >= 40:
                rel_tag = "【友善】"
            elif rel >= 10:
                rel_tag = "【中立】"
            elif rel >= -10:
                rel_tag = "【冷淡】"
            else:
                rel_tag = "【疏远】"

            npc_data = {
                "name": npc.name,
                "rank": npc.rank,
                "relation": rel,
                "relation_tag": rel_tag,
                "options": [
                    {"id": "1", "label": "诚心相邀", "desc": "表达敬意，邀其共举大事"},
                    {"id": "2", "label": "以利诱之", "desc": "赠金三十（需30金）"},
                    {"id": "3", "label": "晓以大义", "desc": "以天下苍生为由（需名望≥50）"},
                    {"id": "4", "label": "威逼利诱", "desc": "软硬兼施（需20金，有风险）"},
                    {"id": "5", "label": "交谈", "desc": "与对方交谈"},
                    {"id": "6", "label": "索取情报", "desc": "请其透露天下局势"},
                    {"id": "7", "label": "离开", "desc": "拱手作别"},
                ],
            }

        elif self.engine.pending_market:
            ui_state = "market"

        elif self.engine.pending_intel:
            ui_state = "intel"

        elif self.engine.pending_death_shop:
            ui_state = "death_shop"

        # Available moves
        current = p.location
        adj = get_adjacent_cities(current)

        return {
            "game_status": "playing",
            "time": state.get_time_str(),
            "year": state.year,
            "month": state.month,
            "player": {
                "name": p.name,
                "rank": p.rank,
                "location": p.location,
                "hp": p.hp,
                "morale": p.morale,
                "stamina": p.stamina,
                "gold": p.gold,
                "food": p.food,
                "exp": p.exp,
                "rank_exp": config.RANK_EXP_REQUIRE.get(p.rank, 0),
                "stats": dict(p.stats),
                "effects": list(p.effects),
                "active_skills": list(p.active_skills),
                "passive_skills": list(p.passive_skills),
                "inheritance_fragments": p.inheritance_fragments,
                "equipment": list(p.equipment),
            },
            "narrative": "\n".join(self._history[-50:]),  # last 50 entries
            "ui_state": ui_state,
            "combat_data": combat_data,
            "npc_data": npc_data,
            "market_data": {
                "player_gold": p.gold,
                "player_food": p.food,
            } if ui_state == "market" else None,
            "available_moves": adj,
            "map": self._get_map_data(),
            "tavern_npcs": getattr(self, '_tavern_npcs', None),
            "achievements": self._get_achievements_data(),
            "city_favorability": self.engine.state.city_favorability,
            "run_stats": dict(self.engine.state.run_stats),
            "run_history": self._get_history_data(),
            "pending_equipment": self._get_pending_equipment(),
            "pending_death_shop": self.engine.pending_death_shop or None,
            "pending_intel": getattr(self.engine, 'pending_intel', None),
        }

    def _get_pending_campaign(self):
        """Return pending campaign data if any."""
        if not self.engine.pending_campaign:
            return None
        c = self.engine.pending_campaign
        return {
            "id": c.id,
            "name": c.name,
            "description": c.description,
            "duration": c.duration,
            "rewards": c.rewards,
            "side_choice": c.side_choice,
            "combat_intro": c.combat_intro,
        }

    def _get_pending_choice(self):
        """Return pending choice event data if any."""
        if not self.engine.pending_choice:
            return None
        e = self.engine.pending_choice
        return {
            "id": e.id,
            "name": e.name,
            "description": e.description,
            "options": [
                {"id": opt["id"], "label": opt["label"], "desc": opt["desc"]}
                for opt in e.options
            ],
        }

    def _get_pending_equipment(self):
        """Return pending equipment drop data if any."""
        if not self.engine.pending_equipment:
            return None
        return dict(self.engine.pending_equipment)

    def _get_achievements_data(self):
        """Return achievements data for the UI panel."""
        unlocked_ids = load_achievements(config.ACHIEVEMENTS_FILE)
        return {
            "total": len(ACHIEVEMENTS),
            "unlocked": len(unlocked_ids),
            "achievements": [
                {
                    "id": ach.id,
                    "name": ach.name,
                    "desc": ach.desc,
                    "icon": ach.icon,
                    "unlocked": ach.id in unlocked_ids,
                }
                for ach in ACHIEVEMENTS
            ],
        }

    def _build_death_shop_data(self):
        """Build death shop data: available skills and player fragments."""
        from skills import SKILLS, can_learn_skill
        p = self.engine.state.player
        months = self.engine.state.get_elapsed_months()
        rs = self.engine.state.run_stats
        fragments_earned = 5 + ((months + 5) // 6)
        p.inheritance_fragments += fragments_earned

        active = []
        passive = []
        for sid, sk in SKILLS.items():
            if sk.cost == 0:
                continue
            can_learn, reason = can_learn_skill(sid, p)
            entry = {
                "id": sid,
                "name": sk.name,
                "type": sk.skill_type,
                "cost": sk.cost,
                "desc": sk.desc,
                "can_learn": can_learn,
                "fail_reason": reason if not can_learn else None,
            }
            if sk.skill_type == "active":
                active.append(entry)
            else:
                passive.append(entry)

        return {
            "fragments_balance": p.inheritance_fragments,
            "fragments_earned": fragments_earned,
            "active_skills": active,
            "passive_skills": passive,
            "death_summary": {
                "months": months,
                "battles": rs.get("battles_this_run", 0),
                "npcs_recruited": len(rs.get("npcs_recruited_this_run", [])),
                "highest_rank": rs.get("highest_rank", p.rank),
                "exp_earned": rs.get("total_exp_earned", 0),
            }
        }

    def _get_history_data(self):
        """Return run history for the history panel."""
        history = self.engine.progression.history
        # Return last 20 records, most recent first
        records = list(reversed(history))[-20:]
        return {
            "records": records,
            "total_runs": len(history),
        }

    def _get_map_data(self):
        """Return map data for current player position."""
        p = self.engine.state.player
        current = p.location
        region = None
        for reg, data in REGIONS.items():
            if current in data["cities"]:
                region = reg
                break
        adj = get_adjacent_cities(current)
        return {
            "current": current,
            "region": region,
            "regions": {reg: {"name": data["name"], "cities": data["cities"]} for reg, data in REGIONS.items()},
            "adjacent_cities": adj,
            "connections": CITY_CONNECTIONS,
        }

    def move_to(self, target):
        """Move to a city."""
        old_stdout = sys.stdout
        sys.stdout = StringIO()
        try:
            result = self.engine.move_to(target)
        finally:
            sys.stdout = old_stdout

        self._add_narrative(result)
        return self.get_state()

    def combat_action(self, choice, skill=None):
        """Execute combat action (1-4) optionally with a skill."""
        old_stdout = sys.stdout
        sys.stdout = StringIO()
        try:
            narrative = self.engine.resolve_combat_action(str(choice), active_skill=skill)
        finally:
            sys.stdout = old_stdout

        self._add_narrative(narrative)
        return self.get_state()

    def npc_action(self, choice):
        """Handle NPC encounter choice."""
        old_stdout = sys.stdout
        sys.stdout = StringIO()
        try:
            self.engine.handle_npc_encounter(str(choice))
        finally:
            output = sys.stdout.getvalue()
            sys.stdout = old_stdout

        if output.strip():
            self._add_narrative(output.strip())
        return self.get_state()

    def market_action(self, cmd):
        """Market buy/sell/leave."""
        old_stdout = sys.stdout
        sys.stdout = StringIO()
        try:
            done = self.engine.handle_market_input(cmd)
        finally:
            sys.stdout = old_stdout

        if done:
            self.engine.pending_market = False
        return self.get_state()

    def show_intel(self):
        """Build intel data: NPC locations + paths (returns structured data)."""
        cost = 20
        p = self.engine.state.player
        if p.gold < cost:
            self._add_narrative(f"盘缠不足，打听消息需要{cost}金，你只有{p.gold}金。")
            return self.get_state()
        p.gold -= cost

        current_year = self.engine.state.year
        from world import find_path

        npc_list = []
        for npc_name, npc in self.engine.state.npcs.items():
            if npc.hp <= 0:
                continue
            if not is_npc_active(npc_name, current_year):
                continue
            loc = get_npc_location(npc_name, current_year)
            npc_type = getattr(npc, 'npc_type', '武将')
            leader = is_faction_leader(npc_name)
            recruited = self.engine.state.event_flags.get(f'已招募_{npc_name}', False)

            if loc == p.location:
                location_hint = "📍当前所在"
            else:
                path = find_path(p.location, loc)
                if path and len(path) <= 4:
                    hops = "→".join(path[1:])
                    location_hint = f"→{hops}（{len(path)-1}步）"
                else:
                    location_hint = f"「{loc}」"

            npc_list.append({
                "name": npc_name,
                "type": npc_type,
                "icon": '⚔️' if npc_type == '武将' else '📚',
                "location_hint": location_hint,
                "city": loc,
                "is_leader": leader,
                "is_recruited": recruited,
                "is_here": loc == p.location,
            })

        self.engine.pending_intel = {
            "cost": cost,
            "gold_left": p.gold,
            "npcs": npc_list,
        }
        self._add_narrative(f"📰 江湖消息（花费{cost}金）")
        return self.get_state()

    def visit_tavern(self):
        """Visit tavern — list NPCs in current city, no random roll."""
        p = self.engine.state.player
        current_year = self.engine.state.year
        current_loc = p.location

        npcs_here = []
        for npc_name, npc in self.engine.state.npcs.items():
            if npc.hp <= 0:
                continue
            if not is_npc_active(npc_name, current_year):
                continue
            npc_loc = get_npc_location(npc_name, current_year)
            if npc_loc == current_loc:
                npcs_here.append(npc)

        if not npcs_here:
            self._add_narrative("🍶 酒馆里冷冷清清，未遇故人。")
            return self.get_state()

        # If only one NPC, trigger encounter directly
        if len(npcs_here) == 1:
            npc = npcs_here[0]
            encounter = {"type": "npc_encounter", "npc_name": npc.name, "npc": npc}
            self.engine.pending_npc_encounter = encounter
            self._add_narrative(f"🎭 {npc.name}（{npc.rank}）正在此处。")
            return self.get_state()

        # Multiple NPCs: list them and let player choose
        lines = ["🍶 酒馆中数人聚坐："]
        for i, npc in enumerate(npcs_here, 1):
            lines.append(f"  {i}. {npc.name}（{npc.rank}）")
        lines.append("点击其中一人开始交谈。")
        self._add_narrative("\n".join(lines))

        # Store NPC list for player choice resolution
        self._tavern_npcs = npcs_here
        state = self.get_state()
        state["ui_state"] = "tavern_choice"
        state["tavern_npcs"] = [{"id": str(i+1), "name": n.name, "rank": n.rank, "npc_type": getattr(n, 'npc_type', '武将')} for i, n in enumerate(npcs_here)]
        return state

    def resolve_tavern_choice(self, choice_idx):
        """Resolve player's choice in tavern (when multiple NPCs present)."""
        if not hasattr(self, '_tavern_npcs') or not self._tavern_npcs:
            self._add_narrative("你离开了酒馆。")
            return self.get_state()
        npcs = self._tavern_npcs
        self._tavern_npcs = None
        try:
            idx = int(choice_idx) - 1
            if idx < 0 or idx >= len(npcs):
                self._add_narrative("你离开了酒馆。")
                return self.get_state()
        except (ValueError, TypeError):
            self._add_narrative("无效输入。")
            return self.get_state()
        npc = npcs[idx]
        encounter = {"type": "npc_encounter", "npc_name": npc.name, "npc": npc}
        self.engine.pending_npc_encounter = encounter
        # Manually set npc_data so get_state() returns proper UI for NPC encounter
        p = self.engine.state.player
        rel = p.get_relation(npc.name)
        if rel >= 70: rel_tag = "【亲密】"
        elif rel >= 40: rel_tag = "【友善】"
        elif rel >= 10: rel_tag = "【中立】"
        elif rel >= -10: rel_tag = "【冷淡】"
        else: rel_tag = "【疏远】"
        self._pending_npc_data = {
            "name": npc.name, "rank": npc.rank,
            "relation": rel, "relation_tag": rel_tag,
            "options": [
                {"id": "1", "label": "诚心相邀", "desc": "表达敬意，邀其共举大事"},
                {"id": "2", "label": "以利诱之", "desc": "赠金三十（需30金）"},
                {"id": "3", "label": "晓以大义", "desc": "以天下苍生为由（需名望≥50）"},
                {"id": "4", "label": "威逼利诱", "desc": "软硬兼施（需20金，有风险）"},
                {"id": "5", "label": "交谈", "desc": "与对方交谈"},
                {"id": "6", "label": "索取情报", "desc": "请其透露天下局势"},
                {"id": "7", "label": "离开", "desc": "拱手作别"},
            ],
        }
        self._add_narrative(f"🎭 {npc.name}（{npc.rank}）正在此处。")
        return self.get_state()

    def show_map(self):
        """Show map."""
        old_stdout = sys.stdout
        sys.stdout = StringIO()
        try:
            self.engine.show_map()
        finally:
            output = sys.stdout.getvalue()
            sys.stdout = old_stdout

        self._add_narrative(output)
        return self.get_state()

    def buy_skill(self, skill_id):
        """Purchase a skill from death shop."""
        from skills import get_skill, can_learn_skill
        if not self.engine.state or not self.engine.state.player:
            return self.get_state()
        p = self.engine.state.player
        shop = self.engine.pending_death_shop
        if not shop:
            return self.get_state()

        skill = get_skill(skill_id)
        if not skill:
            return self.get_state()
        if skill.cost == 0:
            return self.get_state()

        can_learn, _ = can_learn_skill(skill_id, p)
        if not can_learn:
            return self.get_state()
        if p.inheritance_fragments < skill.cost:
            return self.get_state()

        p.inheritance_fragments -= skill.cost
        p.add_skill(skill_id)
        self._add_narrative(f"✅ 习得技能：{skill.name}！剩余碎片：{p.inheritance_fragments}枚")
        return self.get_state()

    def reincarnate(self):
        """Start a new life (reincarnate)."""
        self.engine.pending_death_shop = None
        self.engine.new_game()
        self._history = []
        self._add_narrative("\n🌟 新的命运开始...")
        return self.get_state()

    def show_status(self):
        """Show player status."""
        old_stdout = sys.stdout
        sys.stdout = StringIO()
        try:
            self.engine.show_status()
        finally:
            output = sys.stdout.getvalue()
            sys.stdout = old_stdout

        self._add_narrative(output)
        return self.get_state()


# ── Flask Server ──────────────────────────────────────────
from flask import Flask, jsonify, request, send_from_directory

api = SanguoAPI()
app = Flask(__name__, static_folder="web", static_url_path="")

@app.route("/")
def index():
    return send_from_directory("web", "index.html")

@app.route("/api/state", methods=["GET"])
def get_state():
    return jsonify(api.get_state())

@app.route("/api/new_game", methods=["POST"])
def new_game():
    return jsonify(api.new_game())

@app.route("/api/tick", methods=["POST"])
def tick():
    return jsonify(api.tick())

@app.route("/api/move", methods=["POST"])
def move():
    data = request.json or {}
    target = data.get("target", "")
    return jsonify(api.move_to(target))

@app.route("/api/combat", methods=["POST"])
def combat():
    data = request.json or {}
    choice = data.get("choice", "1")
    skill = data.get("skill")
    return jsonify(api.combat_action(choice, skill))

@app.route("/api/npc", methods=["POST"])
def npc():
    data = request.json or {}
    choice = data.get("choice", "7")
    return jsonify(api.npc_action(choice))

@app.route("/api/market", methods=["POST"])
def market():
    data = request.json or {}
    cmd = data.get("cmd", "leave")
    return jsonify(api.market_action(cmd))

@app.route("/api/intel", methods=["POST"])
def intel():
    return jsonify(api.show_intel())

@app.route("/api/map", methods=["POST"])
def game_map():
    return jsonify(api.show_map())

@app.route("/api/status", methods=["POST"])
def status():
    return jsonify(api.show_status())

@app.route("/api/buy_skill", methods=["POST"])
def buy_skill():
    data = request.json or {}
    skill_id = data.get("skill_id", "")
    return jsonify(api.buy_skill(skill_id))

@app.route("/api/reincarnate", methods=["POST"])
def reincarnate():
    return jsonify(api.reincarnate())

@app.route("/api/enter_market", methods=["POST"])
def enter_market():
    api.engine.pending_market = True
    state = api.get_state()
    return jsonify(state)

@app.route("/api/tavern", methods=["POST"])
def visit_tavern():
    return jsonify(api.visit_tavern())

@app.route("/api/tavern_choice", methods=["POST"])
def tavern_choice():
    data = request.json or {}
    choice = data.get("choice", "0")
    return jsonify(api.resolve_tavern_choice(choice))

@app.route("/api/achievements", methods=["GET"])
def api_achievements():
    """Return full achievements data for the UI panel."""
    return jsonify(api._get_achievements_data())

@app.route("/api/campaign_choice", methods=["POST"])
def campaign_choice():
    data = request.json or {}
    accept = data.get("accept", False)
    side = data.get("side")  # optional, for side-choice campaigns
    api.engine.handle_campaign_choice(bool(accept), side)
    return jsonify(api.get_state())

@app.route("/api/choice", methods=["POST"])
def choice():
    data = request.json or {}
    choice_id = data.get("choice_id", "")
    api.engine.handle_choice_event(str(choice_id))
    return jsonify(api.get_state())

@app.route("/api/equipment", methods=["POST"])
def equipment():
    data = request.json or {}
    action = data.get("action", "")  # "replace" | "drop"
    slot_index = data.get("slot_index")  # 0, 1, 2 or None
    if action == "replace" and slot_index is not None:
        api.engine.handle_equipment_choice(int(slot_index))
    elif action == "drop":
        # Drop currently equipped item at slot
        if slot_index is not None:
            api.engine.state.player.remove_equipment(int(slot_index))
    return jsonify(api.get_state())

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    print(f"三国文字Roguelike API Server — Port {port}")
    app.run(host="0.0.0.0", port=port, debug=False)