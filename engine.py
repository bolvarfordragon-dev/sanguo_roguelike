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
from npc_schedule import get_npc_location, is_npc_active, is_faction_leader, is_major_hero
from skills import get_skill, SKILLS, can_learn_skill

# NPC赠送技能
NPC_GIFT_SKILLS = {
    "刘备": {"skill_id": "brotherhood_oath", "type": "passive"},
    "赵云": {"skill_id": "dragon_valor", "type": "active"},
    "诸葛亮": {"skill_id": "longzhong_strategy", "type": "passive"},
    "曹操": {"skill_id": "wei_strategy", "type": "passive"},
}


class CombatEnemy:
    """战斗中的敌方单位（程序生成的敌人）"""
    def __init__(self, name, stats, troops, morale, terrain, narrative):
        self.name = name
        self.stats = stats
        self.hp = 100
        self.morale = morale
        self.troops = troops
        self.terrain = terrain
        self.narrative = narrative
        self.rank = "杂兵"
        self.location = ""
        self.effects = []
        self.skills = []
        self.active_skills = []
        self.passive_skills = []
    def get_stat(self, stat):
        return self.stats.get(stat, 30)


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

    def resolve_combat_action(self, choice, active_skill=None):
        """
        处理玩家战斗选择（1-4）
        active_skill: str or None — 要使用的主动技能ID
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
        session.simulate(player_action=action, active_skill=active_skill)

        # 更新玩家状态
        costs = session.get_cost(action)
        self.state.player.morale = max(10, min(100,
            self.state.player.morale + costs.get("morale", 0)))

        # 体力消耗（含被动技能加成）
        stamina_cost = costs.get("stamina", 0)
        if "iron_stamina" in self.state.player.passive_skills:
            stamina_cost = int(stamina_cost / 2)
        self.state.player.stamina = max(0, min(100,
            self.state.player.stamina + stamina_cost))

        # 处理战斗结果
        if session.fled:
            # 撤退成功，扣减兵力
            self.state.player.food = max(0, self.state.player.food - session.attacker_damage)
            self.state.player.morale = max(20, self.state.player.morale - 8)
            self.state.player.exp += 5
        elif session.winner == self.state.player:
            # 胜利：经验 + 名望 + 战利品
            self.state.player.food = max(0, self.state.player.food - session.attacker_damage)
            exp_gain = 20 + session.defender_damage // 10
            self.state.player.exp += exp_gain
            self.state.player.modify_stat("名", 2)

            # 战利品：敌人遗落的资源
            gold_loot = random.randint(8, 25)
            food_loot = random.randint(8, 30)
            self.state.player.gold += gold_loot
            self.state.player.food += food_loot

            # 佣兵之道：战斗胜利额外+5金
            if "mercenary_spirit" in self.state.player.passive_skills:
                self.state.player.gold += 5
                merc_msg = "（+5 佣兵奖励）"
            else:
                merc_msg = ""

            # 稀有碎片（15%概率）
            frag_msg = ""
            if random.random() < 0.15:
                frag = 1
                self.state.player.inheritance_fragments += frag
                frag_msg = f"\n拾获战场遗落的传承碎片 ×{frag}！"

            loot_line = f"\n📦 战利品：金+{gold_loot}，粮+{food_loot}{merc_msg}{frag_msg}"
            narrative = session.get_full_narrative() + loot_line
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


    def show_market(self, FOOD_PRICE=10, FOOD_AMOUNT=15):
        """市集：可以用金买粮，每10金换15粮"""
        p = self.state.player
        if p.gold < FOOD_PRICE:
            print(f"盘缠不足，市集交易需要{FOOD_PRICE}金，你只有{p.gold}金。")
            return
        p.gold -= FOOD_PRICE
        p.food += FOOD_AMOUNT
        p.food = min(100, p.food)  # 上限100
        print(f"📦 市集易货：你付出{FOOD_PRICE}金，买入{FOOD_AMOUNT}粮，当前金{p.gold}粮{p.food}。")

    def show_intel(self, cost=20):
        """花钱打听消息，获得所有重要NPC的当前位置"""
        p = self.state.player
        if p.gold < cost:
            print(f"盘缠不足，打听消息需要{cost}金，你只有{p.gold}金。")
            return
        p.gold -= cost
        current_year = self.state.year
        print(f"""
{'─'*40}
📰 江湖消息（花费{cost}金）
{'─'*40}""")
        for npc_name, npc in self.state.npcs.items():
            if npc.hp <= 0:
                continue
            if not is_npc_active(npc_name, current_year):
                continue
            loc = get_npc_location(npc_name, current_year)
            npc_type = getattr(npc, 'npc_type', '武将')
            type_icon = '⚔️' if npc_type == '武将' else ('📚' if npc_type == '文官' else '👑')
            leader_tag = ' [阵营领袖]' if is_faction_leader(npc_name) else ''
            recruited_tag = ' ✅已招募' if self.state.event_flags.get(f'已招募_{npc_name}', False) else ''
            print(f"  {type_icon} {npc_name} — 现身于「{loc}」{leader_tag}{recruited_tag}")
        print()
        print("（移动至该城市可尝试遭遇）")

    def move_to(self, target_city):
        """移动到某城市"""
        current = self.state.player.location

        if current == target_city:
            return f"你已在{target_city}。"

        move_info = get_move_info(current, target_city)
        if not move_info["can"]:
            return move_info["narrative"]

        # 检查金钱（节旅人：移动消耗-3）
        cost = move_info["cost"]
        if "frugal_traveler" in self.state.player.passive_skills:
            cost = max(2, cost - 3)
        if self.state.player.gold < cost:
            return f"盘缠不足，需要{cost}金，你只有{self.state.player.gold}金。"

        # 执行移动
        self.state.player.gold -= cost
        travel_text = travel_narrative(current, target_city)
        self.state.player.location = target_city

        # 时间推进
        self.state.advance_time(move_info["time"])

        # 消耗体力（含铁人效果减半）
        move_cost = 15
        if "iron_stamina" in self.state.player.passive_skills:
            move_cost = 8
        self.state.player.stamina = max(0, self.state.player.stamina - move_cost)

        # 触发随机遭遇
        encounter = self._check_travel_encounter(target_city)

        result = [
            travel_text,
            f"你于{self.state.get_time_str()}抵达{target_city}。",
            f"（消耗金{self.state.player.gold + cost}→{self.state.player.gold}，消耗体力{int(move_cost)}）",
            "",
            f"── {target_city} 城门 ──",
            f"  🏪 市集 — 输入 'market' 10金买15粮",
            f"  🍶 酒馆 — 输入 'intel' 打听消息（20金）",
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

        # ============ 战斗遭遇检查 ============
        combat_result = self._check_combat_encounter()

        # ============ NPC 遭遇检查（本地 + 附近） ============
        encounter = self._check_npc_encounter()  # 仅检查同城

        if self.state.is_game_over():
            self.running = False
            return None

        # 优先处理战斗
        if combat_result:
            return {
                "time": f"{year}年{month}月",
                "mandatory": mandatory_result,
                "conditionals": conditional_results,
                "combat": combat_result,
            }

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

    def _check_npc_encounter(self, max_distance=0):
        """检查是否触发 NPC 遭遇
        max_distance: 0=仅同城，1=同城+相邻城市
        """
        if not self.state or not self.state.player:
            return None

        current_year = self.state.year
        player_location = self.state.player.location

        # 相邻城市列表
        adj_cities = set()
        if max_distance >= 1:
            adj = get_adjacent_cities(player_location)
            adj_cities = set(adj)  # adj 是城市名字符串列表

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
            if npc_loc != player_location and (max_distance < 1 or npc_loc not in adj_cities):
                continue

            candidates.append((npc_name, npc))

        if not candidates:
            return None

        # 基础20%概率遇上有候选的NPC
        if random.random() > 0.20:
            return None

        # 随机选择一个 NPC 遭遇
        npc_name, npc = random.choice(candidates)
        return {
            "type": "npc_encounter",
            "npc_name": npc_name,
            "npc": npc,
        }

    def _check_combat_encounter(self):
        """检查是否触发战斗遭遇"""
        if not self.state or not self.state.player:
            return None

        p = self.state.player

        # 体力不足时不触发战斗
        if p.stamina < 10:
            return None

        # 基础28%概率，随名望提升略微降低（名望越高，匪寇越少主动招惹）
        fame_mod = max(-0.05, -(p.get_stat("名") - 10) / 1000)
        base_chance = 0.20 + fame_mod

        # 已有战斗待处理
        if self.pending_combat:
            return None

        if random.random() > base_chance:
            return None

        # 根据年份和地点生成敌人
        enemy = self._generate_combat_enemy()
        if not enemy:
            return None

        ctx = {
            "attacker_troops": max(10, p.food // 2 + 30),
            "defender_troops": enemy.troops,
            "terrain": enemy.terrain,
            "weather": self._get_season_weather(),
            "location": p.location,
            "attacker_morale": p.morale,
            "defender_morale": enemy.morale,
        }

        self.pending_combat = {"enemy": enemy, "ctx": ctx}
        return {
            "enemy": enemy,
            "ctx": ctx,
        }

    def _generate_combat_enemy(self):
        """根据当前年份和地点生成战斗敌人"""
        year = self.state.year
        loc = self.state.player.location

        # 敌人类型按年份分段
        if year <= 184:
            enemy_pool = [
                {"name": "黄巾乱兵", "troops": 80, "morale": 60, "terrain": "平原", "narrative": "一队黄巾乱兵呼啸而来，拦住了你的去路！", "stats": {"武": 45, "智": 20, "名": 5, "魅": 10, "运": 20}},
                {"name": "黄巾头目", "troops": 120, "morale": 55, "terrain": "山林", "narrative": "一个身披黄巾的悍匪头目，率众截住了你的去路！", "stats": {"武": 60, "智": 30, "名": 10, "魅": 15, "运": 25}},
                {"name": "溃逃官军", "troops": 60, "morale": 30, "terrain": "平原", "narrative": "一队溃散的官军正在劫掠，撞见了你！", "stats": {"武": 40, "智": 25, "名": 5, "魅": 10, "运": 15}},
            ]
        elif year <= 189:
            enemy_pool = [
                {"name": "山贼", "troops": 70, "morale": 50, "terrain": "山林", "narrative": "山林中杀出一伙山贼！", "stats": {"武": 50, "智": 20, "名": 5, "魅": 10, "运": 20}},
                {"name": "散兵游勇", "troops": 55, "morale": 40, "terrain": "平原", "narrative": "一队散兵正在四处劫掠，与你撞个正着！", "stats": {"武": 40, "智": 20, "名": 5, "魅": 10, "运": 15}},
                {"name": "董卓军斥候", "troops": 90, "morale": 65, "terrain": "平原", "narrative": "董卓军的斥候发现了你，领兵杀来！", "stats": {"武": 55, "智": 30, "名": 10, "魅": 15, "运": 25}},
            ]
        elif year <= 200:
            enemy_pool = [
                {"name": "袁绍军", "troops": 100, "morale": 60, "terrain": "平原", "narrative": "袁绍的军队正在这一带活动，与你遭遇！", "stats": {"武": 55, "智": 30, "名": 15, "魅": 15, "运": 30}},
                {"name": "曹操军", "troops": 95, "morale": 65, "terrain": "平原", "narrative": "一队曹操的兵马拦在前方！", "stats": {"武": 58, "智": 35, "名": 15, "魅": 18, "运": 28}},
                {"name": "流寇", "troops": 65, "morale": 45, "terrain": "山林", "narrative": "一伙流寇从林间杀出，意图劫掠！", "stats": {"武": 45, "智": 22, "名": 5, "魅": 10, "运": 18}},
            ]
        else:
            enemy_pool = [
                {"name": "敌国游骑", "troops": 110, "morale": 65, "terrain": "平原", "narrative": "敌国游骑发现了你的踪迹，包围过来！", "stats": {"武": 60, "智": 30, "名": 15, "魅": 15, "运": 28}},
                {"name": "蛮族入侵者", "troops": 95, "morale": 55, "terrain": "山地", "narrative": "一股蛮族军队烧杀劫掠，与你迎面撞上！", "stats": {"武": 65, "智": 20, "名": 10, "魅": 10, "运": 22}},
                {"name": "山贼", "troops": 75, "morale": 50, "terrain": "山林", "narrative": "山贼们设下埋伏，等你踏入陷阱！", "stats": {"武": 52, "智": 22, "名": 5, "魅": 10, "运": 20}},
            ]

        # 根据玩家rank调整敌人强度
        rank_troop_scale = {
            "散兵": 0.8, "什长": 0.9, "伍长": 1.0, "队长": 1.1,
            "曲长": 1.2, "司马": 1.4, "校尉": 1.6, "中郎将": 1.8, "将军": 2.0,
        }
        scale = rank_troop_scale.get(self.state.player.rank, 1.0)

        chosen = random.choice(enemy_pool)

        # 特殊地名地形
        terrain_override = None
        if loc in ["汜水关", "虎牢关", "武关"]:
            terrain_override = "关隘"
        elif loc in ["江陵", "番禺", "广陵"]:
            terrain_override = "水域"

        # 构造一个兼容战斗系统的敌人对象
        enemy_stats = chosen["stats"].copy()
        for stat in enemy_stats:
            enemy_stats[stat] = max(10, int(enemy_stats[stat] * scale))

        enemy = CombatEnemy(
            name=chosen["name"],
            stats=enemy_stats,
            troops=max(20, int(chosen["troops"] * scale)),
            morale=min(95, max(30, chosen["morale"] + int(scale * 5))),
            terrain=terrain_override or chosen["terrain"],
            narrative=chosen["narrative"],
        )
        return enemy

    def get_active_skills_prompt(self):
        """获取玩家当前可用的主动技能列表提示"""
        p = self.state.player
        if not p.active_skills:
            return None
        usable = []
        for sid in p.active_skills:
            from skills import get_skill
            sk = get_skill(sid)
            if not sk:
                continue
            if sk.stat_req:
                if not all(p.get_stat(s) >= r for s, r in sk.stat_req.items()):
                    continue
            usable.append((sid, sk))
        return usable

    def _get_season_weather(self):
        """根据当前月份返回天气"""
        month = self.state.month
        if month in [12, 1, 2]:
            weathers = ["雪", "晴", "大雾"]
        elif month in [3, 4, 5]:
            weathers = ["晴", "大雨", "大雾"]
        elif month in [6, 7, 8]:
            weathers = ["大雨", "晴", "大风"]
        else:
            weathers = ["晴", "大雾", "大风"]
        return random.choice(weathers)

    def _natural_recovery(self):
        p = self.state.player
        if not p:
            return
        p.stamina = min(100, p.stamina + 25)
        p.stamina = max(0, p.stamina)
        if p.morale < 50:
            p.morale = min(100, p.morale + 5)
        elif p.morale > 85:
            p.morale = max(20, p.morale - 2)
        p.morale = max(0, p.morale)
        p.food = max(0, p.food - 3)
        p.gold = max(0, p.gold - 1)
        if p.food == 0:
            if "饥饿" not in p.effects:
                p.effects.append("饥饿")
                p.morale = max(0, p.morale - 15)
            # 饥饿每回合扣血
            p.take_damage(5)
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
        公式：基础率 + 玩家官职/魅力修正 + NPC属性门槛 + 好感度 + 策略
        """
        if self.state.event_flags.get(f"已招募_{npc.name}", False):
            return False, f"{npc.name}已在你麾下。"

        # 阵营领袖（刘备/曹操）永远无法招募
        if is_faction_leader(npc.name):
            return False, f"{npc.name}胸怀大志，非寻常招募可得。"

        p = self.state.player
        rank_idx = config.RANK_ORDER.index(p.rank)

        # ========== 名将分层基础率 ==========
        top_tier = {"刘备", "曹操"}
        mid_tier = {"关羽", "张飞", "赵云", "吕布", "诸葛亮", "周瑜", "司马懿"}
        if npc.name in top_tier:
            base_rate = 0.20
        elif npc.name in mid_tier:
            base_rate = 0.35
        else:
            base_rate = 0.50

        # ========== 玩家官职修正（0~9级官职 -> 0% ~ +27%）==========
        rank_mod = rank_idx * 0.03

        # ========== 玩家魅力修正（50基准，100满魅力 +15%）==========
        charisma_mod = max(-0.20, (p.get_stat("魅") - 50) / 50 * 0.15)

        # ========== NPC 属性门槛（按类型：文官-智魅，武将-武魅，魅力型-只魅）==========
        stat_map = {
            "文官": ["智", "魅"],
            "武将": ["武", "魅"],
            "魅力型": ["魅"],
        }
        relevant_stats = stat_map.get(getattr(npc, 'npc_type', '武将'), ["武", "魅"])
        npc_stat_mod = 0
        for stat in relevant_stats:
            npc_val = npc.get_stat(stat)
            npc_stat_mod -= (npc_val - 50) / 500 * 0.15

        # ========== 好感度修正（0~100 -> 0~+30%）==========
        rel = p.get_relation(npc.name)
        rel_mod = (rel / 100) * 0.30

        # ========== 对话策略 ==========
        strategy_mods = {
            "sincere": 0.10,
            "bribe": 0.05,
            "righteous": 0.05,
            "coerce": -0.20,
        }
        strategy_mod = strategy_mods.get(strategy, 0.0)

        # ========== 消耗处理 ==========
        cost = 30 if strategy == "bribe" else (20 if strategy == "coerce" else 0)
        if cost > 0:
            p.gold -= cost

        final_rate = (base_rate + rank_mod + charisma_mod + npc_stat_mod
                     + rel_mod + strategy_mod)
        final_rate = max(0.05, min(0.90, final_rate))

        success = random.random() < final_rate

        if success:
            self.state.event_flags[f"已招募_{npc.name}"] = True
            p.modify_relation(npc.name, 20)
            gift = NPC_GIFT_SKILLS.get(npc.name)
            gift_msg = ""
            if gift:
                skill = get_skill(gift["skill_id"])
                if skill:
                    p.add_skill(gift["skill_id"])
                    gift_msg = f"\n「你我共事，我有一技相赠——」\n「此乃'{skill.name}'，愿你善用之。」\n（获得技能：{skill.name}）"
            return True, f"\n{npc.name}点头应允，愿意加入麾下！\n（{npc.name}已加入队伍，好感度+20）{gift_msg}"
        else:
            penalty = -10 if strategy == "coerce" else -5
            p.modify_relation(npc.name, penalty)
            msgs = {
                "sincere": f"\n{npc.name}摇头拒绝：「容我三思。」",
                "bribe": f"\n{npc.name}冷笑：「这点钱想收买我？」\n（金-{cost}，好感度{penalty}）",
                "righteous": f"\n{npc.name}沉吟不语，最终摇头离去。",
                "coerce": f"\n{npc.name}怒道：「你当我是什么人！」拂袖而去。\n（金-{cost}，好感度{penalty}）",
            }
            return False, msgs.get(strategy, "")

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

        rel = self.state.player.get_relation(npc.name)
        rel_note = ""
        if "info_network" in self.state.player.passive_skills:
            rel_tags = {
                range(70, 101): "【亲密】",
                range(40, 70): "【友善】",
                range(10, 40): "【中立】",
                range(-10, 10): "【冷淡】",
                range(-40, -9): "【疏远】",
                range(-100, -39): "【敌对】",
            }
            for rng, tag in rel_tags.items():
                if rel in rng:
                    rel_note = f"  {tag} 好感度：{rel}"
                    break

        options = f"""
{npc.name}（{npc.rank}）打量着你，不知是敌是友。
{leader_note}{rel_note}

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
│ market   - 集市买粮   │
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
                usable = engine.get_active_skills_prompt()
                if usable:
                    skill_hints = " ".join([f"[{sid.upper()}]{sk.name}" for sid, sk in usable])
                    print(f"\n⚔️ 选择战术（1-4），或输入技能名使用主动技能：{skill_hints}")
                else:
                    print("\n⚔️ 请选择战术（1-4）：")
                cmd = input("> ").strip()

                # 检查是否是技能键
                chosen_skill = None
                if usable:
                    for sid, sk in usable:
                        if cmd.upper() == sid.upper() or cmd == sk.name:
                            chosen_skill = sid
                            break

                if cmd in ["1", "2", "3", "4"]:
                    result = engine.resolve_combat_action(cmd)
                    print(result)
                    engine.show_status()
                elif chosen_skill:
                    # 选了技能，再选战术
                    skill_name = next(sk.name for s, sk in usable if s == chosen_skill)
                    print(f"\n⚔️ 你选择使用【{skill_name}】\n请选择战术（1-4）：")
                    tactic = input("> ").strip()
                    if tactic in ["1", "2", "3", "4"]:
                        result = engine.resolve_combat_action(tactic, active_skill=chosen_skill)
                        print(result)
                        engine.show_status()
                    else:
                        print("无效选择，战斗取消。")
                        engine.pending_combat = None
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
            elif base_cmd == "intel":
                engine.show_intel()
            elif base_cmd == "move" and arg:
                print(engine.move_to(arg))
                engine.show_status()
            elif base_cmd == "market":
                engine.show_market()
            elif base_cmd == "tick":
                result = engine.tick()
                if result is None and engine.state.is_game_over():
                    months = engine.state.get_elapsed_months()
                    fragments = 5 + ((months + 5) // 6)
                    engine.show_death_screen(fragments, months)
                    continue
                if result:
                    engine.show_status()
                    # 战斗遭遇
                    if result.get("combat"):
                        enemy = result["combat"]["enemy"]
                        ctx = result["combat"]["ctx"]
                        print(f"\n⚔️ {enemy.narrative}")
                        usable = engine.get_active_skills_prompt()
                        print(format_combat_intro(enemy, ctx, usable_skills=usable))
                    # NPC 遭遇
                    if result.get("npc_encounter"):
                        from narrative import narrate_npc_encounter
                        enc = result["npc_encounter"]
                        npc = enc["npc"]
                        print(f"\n🎭 {narrate_npc_encounter(npc)}")
                        print(engine.format_npc_encounter_options(npc))
                    # 必然事件
                    if result.get("mandatory"):
                        e = result["mandatory"]
                        print(f"\n⚔️ 【必然事件】{e['name']}")
                        print(e["desc"][:200] + "...")
                    # 条件事件
                    for ev in result.get("conditionals", []):
                        print(f"\n✨ 【{ev.get('name', '事件')}】{ev.get('desc', '')[:150]}")
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