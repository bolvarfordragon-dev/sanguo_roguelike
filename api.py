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
from world import get_adjacent_cities, find_path, REGIONS


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
        """Handle game over state."""
        p = self.engine.state.player
        if p.hp <= 0:
            self._add_narrative(f"\n💀 你已陨于乱世。存活：{self.engine.state.get_time_str()}")
        else:
            self._add_narrative(f"\n🏯 三国鼎立，乱世收场。你的故事止于{self.engine.state.get_time_str()}。")
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
        return {
            "current": current,
            "region": region,
            "regions": {reg: {"name": data["name"], "cities": data["cities"]} for reg, data in REGIONS.items()},
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
            sys.stdout = old_stdout

        self._add_narrative("")  # narrative already printed by engine
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
        """Show NPC intelligence report."""
        old_stdout = sys.stdout
        sys.stdout = StringIO()
        try:
            self.engine.show_intel()
        finally:
            output = sys.stdout.getvalue()
            sys.stdout = old_stdout

        self._add_narrative(output)
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

@app.route("/api/enter_market", methods=["POST"])
def enter_market():
    api.engine.pending_market = True
    state = api.get_state()
    return jsonify(state)

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    print(f"三国文字Roguelike API Server — Port {port}")
    app.run(host="0.0.0.0", port=port, debug=False)