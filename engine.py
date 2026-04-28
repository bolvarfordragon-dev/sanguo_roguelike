"""
三国文字Roguelike - 主引擎 v2
集成：掷骰子战斗 + 地图移动 + 事件系统
"""
import os
import sys
import random
import config
from state import GameState
from character import Character, NPC, NPC_PRESETS
from combat import CombatSession, start_combat, format_combat_intro, COMBAT_ACTIONS
from narrative import (
    narrate_death_report, format_character_info,
    narrate_event, format_choice
)
from world import (
    format_map, format_location_info, get_adjacent_cities,
    get_move_info, travel_narrative, REGIONS
)
from events.mandatory import get_mandatory_events, trigger_mandatory_event
from events.conditional import (
    get_default_conditional_events,
    taoyuan_oath_event, huarong_road_event, three_visits_to_zhuge_event
)
from progression import Progression
from npc_schedule import get_npc_location, is_npc_active, is_faction_leader
from skills import get_skill, SKILLS, can_learn_skill

# NPC赠送技能
NPC_GIFT_SKILLS = {
    "刘备": {"skill_id": "brotherhood_oath", "type": "passive"},
    "赵云": {"skill_id": "dragon_valor", "type": "active"},
    "诸葛亮": {"skill_id": "longzhong_strategy", "type": "passive"},
    "曹操": {"skill_id": "wei_strategy", "type": "passive"},
}


class SanguoEngine:
    """游戏主引擎"""

    def __init__(self):
        self.state = None
        self.progression = None
        self.running = False
        self.pending_combat = None   # 待处理的战斗
        self.pending_npc_encounter = None  # 待处理的NPC遭遇
        self.pending_choice = None   # 待处理的选择
        self._init_progression()

    def _init_progression(self):
        os.makedirs(os.path.dirname(config.UNLOCK_FILE), exist_ok=True)
        self.progression = Progression(config.UNLOCK_FILE, config.HISTORY_FILE)

    def new_game(self):
        """开始新游戏"""
        self.state = GameState()
        player = Character(is_player=True)
        self.state.set_player(player)
        self._init_npcs()
        self.running = True
        self._print_intro()

    def _init_npcs(self):
        for name, preset in NPC_PRESETS.items():
            npc = NPC(
                name=name,
                preset_stats=preset["stats"],
                rank=preset.get("rank", "武将"),
                location=preset.get("location", "未知"),
            )
            self.state.npcs[name] = npc

    def _print_intro(self):
        intro = f"""
{'='*50}
⚔️  三国文字Roguelike ⚔️
{'='*50}

{"中平元年（184年）春".center(40)}

黄巾之乱席卷天下。

你是一名{self.state.player.rank}，
身处颍川，正是这场风暴的中心。

乱世之中，英雄四起，枭雄并立。
你的命运，将走向何方？
"""
        print(intro)

    # ============ 战斗系统 ============

    def trigger_combat(self, enemy, ctx_override=None):
        """触发一场战斗"""
        ctx = ctx_override or {
            "attacker_troops": 100,
            "defender_troops": 100,
            "terrain": "平原",
            "weather": "晴",
            "location": self.state.player.location,
            "attacker_morale": self.state.player.morale,
            "defender_morale": 80,
        }
        ctx["attacker_troops"] = max(10, self.state.player.food // 2 + 30)
        self.pending_combat = {
            "enemy": enemy,
            "ctx": ctx,
        }
        return format_combat_intro(enemy, ctx)

    def resolve_combat_action(self, choice):
        """
        处理玩家战斗选择（1-4）
        返回: str — 完整战斗叙事
        """
        if not self.pending_combat:
            return "当前没有战斗。"

        action_map = {"1": "进攻", "2": "坚守", "3": "撤退", "4": "用计"}
        action = action_map.get(str(choice).strip())

        if not action:
            return "无效选择，请输入 1-4。"

        enemy = self.pending_combat["enemy"]
        ctx = self.pending_combat["ctx"]

        session = start_combat(self.state.player, enemy, ctx)
        session.simulate(player_action=action)

        # 更新玩家状态
        costs = session.get_cost(action)
        self.state.player.morale = max(10, min(100,
            self.state.player.morale + costs.get("morale", 0)))
        self.state.player.stamina = max(0, min(100,
            self.state.player.stamina + costs.get("stamina", 0)))

        # 处理战斗结果
        if session.fled:
            # 撤退成功，扣减兵力
            self.state.player.food = max(0, self.state.player.food - session.attacker_damage)
            self.state.player.morale = max(20, self.state.player.morale - 8)
            self.state.player.exp += 5
        elif session.winner == self.state.player:
            # 胜利
            self.state.player.food = max(0, self.state.player.food - session.attacker_damage)
            self.state.player.exp += 20 + session.defender_damage // 10
            self.state.player.modify_stat("名", 2)
        else:
            # 战败
            self.state.player.food = max(0, self.state.player.food - session.attacker_damage)
            self.state.player.morale = max(10, self.state.player.morale - 15)
            if session.attacker_damage > session.defender_damage * 2:
                self.state.player.take_damage(random.randint(10, 30))

        narrative = session.get_full_narrative()
        self.pending_combat = None
        return narrative

    # ============ 移动系统 ============

    def show_map(self):
        """显示地图信息"""
        p = self.state.player
        current = p.location
        region = None
        for reg, data in REGIONS.items():
            if current in data["cities"]:
                region = reg
                break

        parts = []
        parts.append(format_map())
        parts.append(format_location_info(current, region))

        adj = get_adjacent_cities(current)
        if adj:
            parts.append(f"\n🚶 从{current}可前往：{', '.join(adj)}")
            parts.append("输入 'move [城市名]' 进行移动（如: move 洛阳）")
        else:
            parts.append(f"\n⚠️ {current}没有已知的向外道路")

        return "\n".join(parts)

    def move_to(self, target_city):
        """移动到某城市"""
        current = self.state.player.location

        if current == target_city:
            return f"你已在{target_city}。"

        move_info = get_move_info(current, target_city)
        if not move_info["can"]:
            return move_info["narrative"]

        # 检查金钱
        cost = move_info["cost"]
        if self.state.player.gold < cost:
            return f"盘缠不足，需要{cost}金，你只有{self.state.player.gold}金。"

        # 执行移动
        self.state.player.gold -= cost
        travel_text = travel_narrative(current, target_city)
        self.state.player.location = target_city

        # 时间推进
        self.state.advance_time(move_info["time"])

        # 消耗体力
        self.state.player.stamina = max(0, self.state.player.stamina - 15)

        # 触发随机遭遇
        encounter = self._check_travel_encounter(target_city)

        result = [
            travel_text,
            f"你于{self.state.get_time_str()}抵达{target_city}。",
            f"（消耗金{self.state.player.gold + cost}→{self.state.player.gold}，消耗体力15）",
        ]
        if encounter:
            result.append(f"\n{encounter}")

        return "\n".join(result)

    def _check_travel_encounter(self, target_city):
        """检查旅途遭遇"""
        roll = random.randint(1, 100)
        if roll <= 30:
            encounter_types = ["流民", "散兵", "商队", "山贼", "游侠"]
            enc = random.choice(encounter_types)
            narratives = {
                "流民": f"途中见一群流民扶老携幼，你施舍了些许钱粮。",
                "散兵": f"遇一队散兵，你盘问后得知是某路诸侯的溃卒。",
                "商队": f"路遇商队，商人为你指点了沿途的情况。",
                "山贼": f"林中杀出一伙山贼，你奋勇击退之，获得些许财物。",
                "游侠": f"遇一道人打扮的游侠，擦肩而过，似是高人。",
            }
            if enc in ["山贼"]:
                gold_gain = random.randint(5, 15)
                self.state.player.gold += gold_gain
                return narratives[enc] + f"（金+{gold_gain}）"
            elif enc in ["流民"]:
                morale_change = -3 if self.state.player.gold > 20 else 0
                if morale_change:
                    self.state.player.gold = max(0, self.state.player.gold - 5)
                    self.state.player.morale = min(100, self.state.player.morale + morale_change)
                return narratives[enc]
            else:
                return narratives[enc]
        return None

    # ============ 时间推进 ============

    def tick(self):
        """推进一个月"""
        self.state.tick()
        year, month = self.state.year, self.state.month

        # 检查必然事件
        mandatory_result = trigger_mandatory_event(self.state, year, month)

        # 检查条件事件
        conditional_results = []
        for evt in get_default_conditional_events():
            r = evt.check_and_trigger(self.state)
            if r:
                conditional_results.append(r)

        # 检查特殊事件
        for evt in [taoyuan_oath_event(), huarong_road_event(), three_visits_to_zhuge_event()]:
            r = evt.check_and_trigger(self.state)
            if r:
                conditional_results.append(r)

        # 自然恢复
        self._natural_recovery()

        # ============ NPC 遭遇检查 ============
        encounter = self._check_npc_encounter()

        if self.state.is_game_over():
            self.running = False
            return None

        if encounter:
            self.pending_npc_encounter = encounter
            return {
                "time": f"{year}年{month}月",
                "mandatory": mandatory_result,
                "conditionals": conditional_results,
                "npc_encounter": encounter,
            }

        return {
            "time": f"{year}年{month}月",
            "mandatory": mandatory_result,
            "conditionals": conditional_results,
        }

        return {
            "time": f"{year}年{month}月",
            "mandatory": mandatory_result,
            "conditionals": conditional_results,
        }

    def _check_npc_encounter(self):
        """检查是否触发 NPC 遭遇"""
        if not self.state or not self.state.player:
            return None

        current_year = self.state.year
        player_location = self.state.player.location

        candidates = []
        for npc_name, npc in self.state.npcs.items():
            if npc.hp <= 0:
                continue
            if not is_npc_active(npc_name, current_year):
                continue
            if self.state.event_flags.get(f"已招募_{npc_name}", False):
                continue

            # 检查 CD（同一NPC 3个月内不重复触发）
            cd_key = f"encounter_cd_{npc_name}"
            cd_year = self.state.event_flags.get(cd_key)
            if cd_year == current_year:
                continue

            # 获取 NPC 当前位置
            npc_loc = get_npc_location(npc_name, current_year)
            if npc_loc != player_location:
                continue

            candidates.append((npc_name, npc))

        if not candidates:
            return None

        # 随机选择一个 NPC 遭遇
        npc_name, npc = random.choice(candidates)
        return {
            "type": "npc_encounter",
            "npc_name": npc_name,
            "npc": npc,
        }

    def _natural_recovery(self):
        p = self.state.player
        if not p:
            return
        p.stamina = min(100, p.stamina + 15)
        if p.morale < 50:
            p.morale = min(100, p.morale + 5)
        elif p.morale > 85:
            p.morale = max(20, p.morale - 2)
        p.food = max(0, p.food - 5)
        p.gold = max(0, p.gold - 2)
        if p.food == 0:
            p.morale -= 15
            p.add_effect("饥饿")
        else:
            if "饥饿" in p.effects:
                p.effects.remove("饥饿")

    def show_status(self):
        """显示当前状态"""
        p = self.state.player
        time_str = self.state.get_time_str()
        print(f"\n{'─'*40}")
        print(f"📅 {time_str} | 📍 {p.location}")
        print(format_character_info(p))
        print(f"{'─'*40}")

    def handle_npc_encounter(self, choice):
        """处理 NPC 遭遇对话选项"""
        if not self.pending_npc_encounter:
            return
        npc = self.pending_npc_encounter["npc"]
        npc_name = self.pending_npc_encounter["npc_name"]

        if choice == "7":
            # 离开，设置 CD
            self.state.event_flags[f"encounter_cd_{npc_name}"] = self.state.year
            self.pending_npc_encounter = None
            return

        elif choice == "1":  # 诚心相邀
            success, msg = self._try_recruit_npc(npc, "sincere")
            print(msg)
            if success:
                self.state.event_flags[f"encounter_cd_{npc_name}"] = self.state.year

        elif choice == "2":  # 以利诱之
            if self.state.player.gold < 30:
                print("金钱不足！")
                return
            success, msg = self._try_recruit_npc(npc, "bribe")
            print(msg)
            if success:
                self.state.event_flags[f"encounter_cd_{npc_name}"] = self.state.year

        elif choice == "3":  # 晓以大义
            if self.state.player.get_stat("名") < 50:
                print("名望不足，无法以此说动对方！")
                return
            success, msg = self._try_recruit_npc(npc, "righteous")
            print(msg)
            if success:
                self.state.event_flags[f"encounter_cd_{npc_name}"] = self.state.year

        elif choice == "4":  # 威逼利诱
            if self.state.player.gold < 20:
                print("金钱不足！")
                return
            success, msg = self._try_recruit_npc(npc, "coerce")
            print(msg)
            if success:
                self.state.event_flags[f"encounter_cd_{npc_name}"] = self.state.year

        elif choice == "5":  # 交谈
            info = self._get_npc_intel(npc)
            print(info)

        elif choice == "6":  # 索取情报
            intel = self._get_npc_intel(npc, detailed=True)
            print(intel)

        else:
            print("无效选择，请输入 1-7。")

        # 清理 pending（不论成功失败都清理，除非玩家还想继续）
        # （遭遇一次就结束，玩家可以下次再遭遇）
        self.pending_npc_encounter = None

    def _try_recruit_npc(self, npc, strategy):
        """
        尝试招募 NPC，返回 (success: bool, message: str)
        """
        # 已招募检查
        if self.state.event_flags.get(f"已招募_{npc.name}", False):
            return False, f"{npc.name}已在你麾下。"

        # 阵营领袖检查
        leader_mod = -0.40 if is_faction_leader(npc.name) else 0.0

        # 基础成功率
        base_rate = 0.50

        # 好感度修正
        rel = self.state.player.get_relation(npc.name)
        rel_mod = (rel / 100) * 0.20

        # 魅力修正
        charisma_mod = (self.state.player.get_stat("魅") - 50) / 500

        # 对话策略加成
        strategy_mods = {
            "sincere": 0.10,
            "bribe": 0.05,
            "righteous": 0.05,
            "coerce": -0.20,  # 强行挽留反而降低成功率
        }
        strategy_mod = strategy_mods.get(strategy, 0.0)

        # 消耗处理
        cost = 0
        if strategy == "bribe":
            cost = 30
        elif strategy == "coerce":
            cost = 20

        if cost > 0:
            self.state.player.gold -= cost

        final_rate = base_rate + rel_mod + charisma_mod + leader_mod + strategy_mod
        final_rate = max(0.05, min(0.95, final_rate))

        success = random.random() < final_rate

        if success:
            self.state.event_flags[f"已招募_{npc.name}"] = True
            self.state.player.modify_relation(npc.name, 20)
            # NPC赠送技能
            gift = NPC_GIFT_SKILLS.get(npc.name)
            gift_msg = ""
            if gift:
                skill = get_skill(gift["skill_id"])
                if skill:
                    self.state.player.add_skill(gift["skill_id"])
                    gift_msg = f"\n「你我共事，我有一技相赠——」\n「此乃'{skill.name}'，愿你善用之。」\n（获得技能：{skill.name}）"
            return True, f"\n{npc.name}点头应允，愿意加入麾下！\n（{npc.name}已加入队伍，好感度+20）{gift_msg}"
        else:
            # 失败好感度变化
            penalty = -10 if strategy == "coerce" else -5
            self.state.player.modify_relation(npc.name, penalty)
            msgs = {
                "sincere": f"\n{npc.name}摇头拒绝：「容我三思。」",
                "bribe": f"\n{npc.name}冷笑：「这点钱想收买我？」\n（金-{cost}，好感度{penalty}）",
                "righteous": f"\n{npc.name}沉吟不语，最终摇头离去。",
                "coerce": f"\n{npc.name}怒道：「你当我是什么人！」拂袖而去。\n（金-{cost}，好感度{penalty}）",
            }
            return False, msgs.get(strategy, "")

    def _get_npc_intel(self, npc, detailed=False):
        """获取 NPC 提供的情报"""
        intel_list = []
        current_year = self.state.year

        for other_name, other_npc in self.state.npcs.items():
            if other_npc.hp <= 0 or other_name == npc.name:
                continue
            if not is_npc_active(other_name, current_year):
                continue
            loc = get_npc_location(other_name, current_year)
            if loc:
                intel_list.append(f"{other_name}目前在{loc}")

        if not intel_list:
            return f"\n{npc.name}告诉你：「天下纷乱，我亦不知他人下落。」"

        info = [f"\n{npc.name}告诉你："]
        for i, intel in enumerate(intel_list[:6], 1):
            info.append(f"  {i}. {intel}")
        return "\n".join(info)

    def format_npc_encounter_options(self, npc):
        """格式化 NPC 遭遇选项"""
        is_leader = is_faction_leader(npc.name)
        leader_note = "（招募困难）" if is_leader else ""

        options = f"""
{npc.name}（{npc.rank}）打量着你，不知是敌是友。
{leader_note}

请选择行动：
  1. [诚心相邀] 表达敬意，邀其{'共举大事' if is_leader else '加入'}
  2. [以利诱之] 赠金三十，邀其加入（需30金）
  3. [晓以大义] 以天下苍生为由（需名望≥50）
  4. [威逼利诱] 软硬兼施（需20金，有风险）
  5. [交谈] 与{npc.name}交谈
  6. [索取情报] 请其透露天下局势
  7. [离开] 拱手作别
"""
        return options

    def handle_choice(self, choice_id, choices):
        """处理选择"""
        for c in choices:
            if c["id"] == choice_id:
                return c["effect"](self.state)
        return None

    def show_death_screen(self, fragments_earned, months_survived):
        """显示死亡界面（遗产商店）"""
        from skills import SKILLS, can_learn_skill, get_skill

        p = self.state.player
        p.inheritance_fragments += fragments_earned

        print(f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💀 你已陨于乱世

存活时间：{self.state.year - 184}年{months_survived % 12}月
获得传承碎片：+{fragments_earned}枚
当前持有：{p.inheritance_fragments}枚

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📦 传承商店

【传承主动技能】
""")

        # 显示可购买技能
        active_skills = []
        passive_skills = []
        for sid, skill in SKILLS.items():
            if skill.cost == 0:  # 跳过NPC赠送技能
                continue
            can_learn, reason = can_learn_skill(sid, p)
            if skill.skill_type == "active":
                active_skills.append((sid, skill, can_learn, reason))
            else:
                passive_skills.append((sid, skill, can_learn, reason))

        idx = 1
        choices = []
        for sid, skill, can_learn, reason in active_skills:
            if can_learn:
                print(f"  {idx}. {skill.name} - {skill.cost}碎片 - {skill.desc}")
                choices.append(sid)
                idx += 1

        print(f"\n【传承被动技能】")
        for sid, skill, can_learn, reason in passive_skills:
            if can_learn:
                print(f"  {idx}. {skill.name} - {skill.cost}碎片 - {skill.desc}")
                choices.append(sid)
                idx += 1

        print(f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
输入数字购买技能，输入 0 直接开始新游戏
当前碎片：{p.inheritance_fragments}枚
> """, end="")

        try:
            cmd = input().strip()
            if cmd.isdigit():
                choice_idx = int(cmd)
                if choice_idx > 0 and choice_idx <= len(choices):
                    skill_id = choices[choice_idx - 1]
                    skill = get_skill(skill_id)
                    if skill and p.inheritance_fragments >= skill.cost:
                        p.inheritance_fragments -= skill.cost
                        p.add_skill(skill_id)
                        print(f"✅ 习得技能：{skill.name}！剩余碎片：{p.inheritance_fragments}枚")
                    else:
                        print("碎片不足！")
                # 输入0或无效 -> 开始新游戏
        except (ValueError, EOFError):
            pass

        # 开始新游戏
        self.new_game()

    def resolve_ending(self, ending_type):
        """处理结局"""
        p = self.state.player
        if ending_type == "three_kingdoms":
            print("""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
【三国鼎立】结局

三十六年风云，你见证了天下三分。
曹操、刘备、孙权各据一方。
而你，不过是这历史洪流中的一个身影。

是加入某一势力，还是继续独行？
天下未定，英雄犹可为期。
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""")
        else:
            print(f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
【游戏结束】
{self.state.year}年{self.state.month}月。
{p.name}，{p.rank}，陨于乱世。
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""")
        self.running = False

    def save_game(self, path=None):
        if not path:
            path = f"{config.SAVE_DIR}/save_{self.state.year}_{self.state.month}.json"
        os.makedirs(config.SAVE_DIR, exist_ok=True)
        self.state.save(path)
        print(f"✅ 存档已保存: {path}")

    def load_game(self, path):
        self.state = GameState.load(path)
        self.running = True
        print(f"✅ 存档已加载")


# ============ 命令行界面 ============

def print_help():
    print("""
┌──────────────────────┐
│     可用命令          │
├──────────────────────┤
│ status   - 显示状态   │
│ map      - 查看地图   │
│ move [城] - 移动      │
│ tick     - 推进时间   │
│ save     - 保存游戏   │
│ help     - 显示帮助   │
│ quit     - 退出       │
└──────────────────────┘
""")


def main():
    engine = SanguoEngine()
    engine.new_game()

    print("\n📖 输入 'help' 查看命令")
    print("📖 输入 'map' 查看地图")

    while engine.running:
        try:
            # 如果有战斗待处理
            if engine.pending_combat:
                print("\n⚔️ 请选择战术（1-4）：")
                cmd = input("> ").strip()
                if cmd in ["1", "2", "3", "4"]:
                    result = engine.resolve_combat_action(cmd)
                    print(result)
                    engine.show_status()
                elif cmd in ["q", "quit", "escape"]:
                    print("你决定撤出战斗……")
                    engine.pending_combat = None
                continue

            # 如果有 NPC 遭遇待处理
            if engine.pending_npc_encounter:
                encounter = engine.pending_npc_encounter
                npc = encounter["npc"]
                from narrative import narrate_npc_encounter
                print(f"\n🎭 {narrate_npc_encounter(npc)}")
                print(engine.format_npc_encounter_options(npc))
                cmd = input("> ").strip()
                engine.handle_npc_encounter(cmd)
                if engine.pending_npc_encounter is None:
                    # 遭遇已处理，显示状态
                    engine.show_status()
                continue

            cmd = input("\n> ").strip()
            if not cmd:
                continue

            parts = cmd.split(maxsplit=1)
            base_cmd = parts[0].lower()
            arg = parts[1] if len(parts) > 1 else ""

            if base_cmd == "help":
                print_help()
            elif base_cmd == "quit":
                print("再见！")
                break
            elif base_cmd == "status":
                engine.show_status()
            elif base_cmd == "map":
                print(engine.show_map())
            elif base_cmd == "move" and arg:
                print(engine.move_to(arg))
                engine.show_status()
            elif base_cmd == "tick":
                result = engine.tick()
                if result is None and engine.state.is_game_over():
                    months = engine.state.get_elapsed_months()
                    fragments = 5 + ((months + 5) // 6)
                    engine.show_death_screen(fragments, months)
                    continue
                if result:
                    engine.show_status()
                    if result.get("mandatory"):
                        e = result["mandatory"]
                        print(f"\n⚔️ 【必然事件】{e['name']}")
                        print(e["desc"][:200] + "...")
            elif base_cmd == "save":
                engine.save_game()
            else:
                print("未知命令，输入 'help' 查看")

        except KeyboardInterrupt:
            print("\n再见！")
            break
        except Exception as e:
            print(f"错误: {e}")


if __name__ == "__main__":
    main()