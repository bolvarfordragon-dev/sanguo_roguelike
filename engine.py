"""
三国文字Roguelike - 主引擎 v2
集成：掷骰子战斗 + 地图移动 + 事件系统
"""
import os
import sys
import random
import config
from config import END_YEAR
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
from events.choices import get_choice_events, check_choice_events
from campaigns import CAMPAIGNS, check_campaign_trigger, get_campaign_by_id
from equipment import DROP_CHANCE, get_random_equipment, EQUIPMENT_SLOTS
from progression import Progression
from achievements import ACHIEVEMENTS, check_achievements, load_achievements, save_achievements, get_achievement_by_id
from npc_schedule import get_npc_location, is_npc_active, is_faction_leader, is_major_hero
from skills import get_skill, SKILLS, can_learn_skill

# NPC赠送技能
NPC_GIFT_SKILLS = {
    "刘备": {"skill_id": "brotherhood_oath", "type": "passive"},
    "赵云": {"skill_id": "dragon_valor", "type": "active"},
    "诸葛亮": {"skill_id": "longzhong_strategy", "type": "passive"},
    "曹操": {"skill_id": "wei_strategy", "type": "passive"},
}

# ============ 羁绊定义 ============
BOND_DEFINITIONS = {
    "桃园三兄弟": {
        "desc": "刘/关/张桃园结义，情同手足",
        "members": ["刘备", "关羽", "张飞"],
        "synergy_bonus": {"武": 5, "名": 3},
        "completion_bonus": {"技能": "义结金兰"},
        "completion_desc": "【义结金兰】满级：全队武力+15，魅力+10",
    },
    "五虎上将": {
        "desc": "蜀汉五虎将，并肩作战天下无敌",
        "members": ["关羽", "张飞", "赵云", "黄忠", "马超"],
        "synergy_bonus": {"武": 4, "运": 2},
        "completion_bonus": {"技能": "龙胆"},
        "completion_desc": "【龙胆】强化：战斗暴击率+15%",
    },
    "诸葛四友": {
        "desc": "诸葛亮与四位好友",
        "members": ["诸葛亮", "庞统", "徐庶"],
        "synergy_bonus": {"智": 5, "魅": 2},
        "completion_bonus": {"技能": "隆中策"},
        "completion_desc": "【隆中策】满级：智谋判定成功率+20%",
    },
    "三顾茅庐": {
        "desc": "刘备三顾茅庐，诸葛亮出山",
        "members": ["刘备", "诸葛亮"],
        "synergy_bonus": {"名": 8, "魅": 5},
        "completion_bonus": {"技能": "三顾茅庐"},
        "completion_desc": "【三顾茅庐】：历史事件触发率+30%",
    },
    "五子良将": {
        "desc": "曹魏五子良将",
        "members": ["张辽", "徐晃", "张郃", "乐进", "于禁"],
        "synergy_bonus": {"武": 3, "名": 2},
        "completion_bonus": {"被动": "兵贵神速"},
        "completion_desc": "【兵贵神速】：移动消耗-30%",
    },
    "颍川双杰": {
        "desc": "荀彧郭嘉，颍川奇士",
        "members": ["荀彧", "郭嘉"],
        "synergy_bonus": {"智": 8, "名": 3},
        "completion_bonus": {"技能": "遗计定辽东"},
        "completion_desc": "【遗计定辽东】：智能判定大吉概率+25%",
    },
    "河北四庭柱": {
        "desc": "袁绍麾下四大名将",
        "members": ["张郃", "颜良", "文丑", "高览"],
        "synergy_bonus": {"武": 4},
        "completion_bonus": {"称号": "河北猛将"},
        "completion_desc": "【河北猛将】：对袁绍势力战斗伤害+20%",
    },
    "襄樊死斗": {
        "desc": "关羽庞德，襄樊之战生死对决",
        "members": ["关羽", "庞德"],
        "synergy_bonus": {"武": 6, "运": 3},
        "completion_bonus": {"被动": "殊死一战"},
        "completion_desc": "【殊死一战】：HP<30%时武力额外+10",
    },
    "江东三代": {
        "desc": "孙坚孙策孙权，江东三代雄主",
        "members": ["孙坚", "孙权", "孙策"],
        "synergy_bonus": {"武": 3, "名": 4, "魅": 3},
        "completion_bonus": {"技能": "江东之主"},
        "completion_desc": "【江东之主】：吴国阵营所有单位属性+10%",
    },
    "江东四杰": {
        "desc": "孙策周瑜鲁肃陆逊，江东四大英杰",
        "members": ["孙策", "周瑜", "鲁肃", "陆逊"],
        "synergy_bonus": {"智": 4, "魅": 3},
        "completion_bonus": {"技能": "火烧赤壁"},
        "completion_desc": "【火烧赤壁】：吴阵营战役伤害+25%",
    },
    "孙策知遇": {
        "desc": "孙策得太史慈，英雄相惜",
        "members": ["孙策", "太史慈"],
        "synergy_bonus": {"武": 5, "名": 4},
        "completion_bonus": {"被动": "知遇之恩"},
        "completion_desc": "【知遇之恩】：每招募一个吴阵营NPC，全属性+1",
    },
    "虎痴恶来": {
        "desc": "典韦许褚，曹操双虎将",
        "members": ["典韦", "许褚"],
        "synergy_bonus": {"武": 6, "运": 3},
        "completion_bonus": {"被动": "护卫神通"},
        "completion_desc": "【护卫神通】：主将存活时，部将阵亡概率-50%",
    },
    "夏侯兄弟": {
        "desc": "夏侯惇夏侯渊，曹操倚重宗族将",
        "members": ["夏侯惇", "夏侯渊"],
        "synergy_bonus": {"武": 5, "名": 3},
        "completion_bonus": {"称号": "宗族虎将"},
        "completion_desc": "【宗族虎将】：魏阵营NPC招募好感度+20",
    },
    "曹氏兄弟": {
        "desc": "曹操曹仁曹氏宗族",
        "members": ["曹操", "曹仁"],
        "synergy_bonus": {"武": 3, "名": 5, "魅": 4},
        "completion_bonus": {"被动": "魏武雄风"},
        "completion_desc": "【魏武雄风】：魏阵营NPC属性+8%",
    },
    "乱世奸雄": {
        "desc": "曹操，乱世之枭雄",
        "members": ["曹操"],
        "synergy_bonus": {"名": 6, "魅": 5, "智": 3},
        "completion_bonus": {"被动": "奸雄本色"},
        "completion_desc": "【奸雄本色】：对非魏阵营NPC招募成功率+15%",
    },
    "鹰视狼顾": {
        "desc": "司马懿鹰视狼顾，厚黑隐忍",
        "members": ["司马懿"],
        "synergy_bonus": {"智": 8, "运": 4},
        "completion_bonus": {"被动": "隐忍待发"},
        "completion_desc": "【隐忍待发】：每亏损一月，智谋+2（最高+20）",
    },
    "黄巾起义": {
        "desc": "张角管亥，黄巾残部",
        "members": ["张角", "管亥"],
        "synergy_bonus": {"名": 5, "魅": 4},
        "completion_bonus": {"技能": "天公将军"},
        "completion_desc": "【天公将军】：名望获取+50%，触发农民起义事件",
    },
    "荆州守将": {
        "desc": "文聘守江夏，关羽为荆州守将",
        "members": ["文聘"],
        "synergy_bonus": {"武": 3, "名": 2},
        "completion_bonus": {"称号": "守土有责"},
        "completion_desc": "【守土有责】：驻守城市时，防御判定+20%",
    },
    "锦帆贼": {
        "desc": "甘宁锦帆贼，水贼出身",
        "members": ["甘宁"],
        "synergy_bonus": {"武": 4, "运": 3},
        "completion_bonus": {"被动": "水战精通"},
        "completion_desc": "【水战精通】：水战场合战斗力+25%",
    },
    "谋士无双": {
        "desc": "陈宫智谋无双",
        "members": ["陈宫"],
        "synergy_bonus": {"智": 6, "名": 3},
        "completion_bonus": {"技能": "陈宫之策"},
        "completion_desc": "【陈宫之策】：战斗中敌方智力降低10%",
    },
    "算无遗策": {
        "desc": "贾诩算无遗策，三国第一毒士",
        "members": ["贾诩"],
        "synergy_bonus": {"智": 8, "魅": 4},
        "completion_bonus": {"被动": "毒士本色"},
        "completion_desc": "【毒士本色】：战斗中对方承受额外智谋伤害15%",
    },
    "董卓之乱": {
        "desc": "董卓，祸乱朝纲",
        "members": ["董卓"],
        "synergy_bonus": {"武": 5, "名": -3, "魅": 5},
        "completion_bonus": {"被动": "暴虐天下"},
        "completion_desc": "【暴虐天下】：城市好感度提升/下降幅度+50%",
    },
    "河北霸主": {
        "desc": "袁绍，河南霸主",
        "members": ["袁绍"],
        "synergy_bonus": {"名": 6, "魅": 4},
        "completion_bonus": {"称号": "诸侯之首"},
        "completion_desc": "【诸侯之首】：群雄NPC招募成功率+20%",
    },
    "汜水虎将": {
        "desc": "华雄汜水虎将",
        "members": ["华雄"],
        "synergy_bonus": {"武": 5, "运": 3},
        "completion_bonus": {"称号": "虎牢先锋"},
        "completion_desc": "【虎牢先锋】：对吕布军伤害+15%",
    },
    "义父子弑": {
        "desc": "吕布弑父，背主求荣",
        "members": ["吕布"],
        "synergy_bonus": {"武": 5, "魅": -5},
        "completion_bonus": {"称号": "三姓家奴"},
        "completion_desc": "【三姓家奴】：可背叛阵营重新加入，每局限1次",
    },
    "反骨天生": {
        "desc": "魏延天生反骨",
        "members": ["魏延"],
        "synergy_bonus": {"武": 5, "魅": -3},
        "completion_bonus": {"称号": "脑后反骨"},
        "completion_desc": "【脑后反骨】：可主动背叛阵营获得额外奖励",
    },
    "蜀中双杰": {
        "desc": "法正蜀中双杰",
        "members": ["法正"],
        "synergy_bonus": {"智": 5, "名": 3},
        "completion_bonus": {"被动": "蜀中智囊"},
        "completion_desc": "【蜀中智囊】：蜀阵营NPC智力+8%",
    },
    "威震逍遥津": {
        "desc": "张辽威震逍遥津",
        "members": ["张辽"],
        "synergy_bonus": {"武": 6, "名": 4},
        "completion_bonus": {"称号": "江东小儿止啼"},
        "completion_desc": "【江东小儿止啼】：对吴阵营战斗力+20%",
    },
    "草莽豪杰": {
        "desc": "江湖游侠，草莽出身",
        "members": ["江湖游侠"],
        "synergy_bonus": {"武": 3, "魅": 4},
        "completion_bonus": {"称号": "绿林好汉"},
        "completion_desc": "【绿林好汉】：野外遭遇有利事件概率+30%",
    },
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

    def __init__(self, silent=False):
        self.state = None
        self.progression = None
        self.running = False
        self.pending_combat = None   # 待处理的战斗
        self.pending_npc_encounter = None  # 待处理的NPC遭遇
        self.pending_market = False  # 待处理的市集交互
        self.pending_choice = None   # 待处理的选择
        self.pending_campaign = None # 待处理的战役（显示介绍界面）
        self.pending_equipment = None  # 待处理的装备掉落替换
        self.pending_death_shop = None  # death shop UI data
        self.pending_intel = None       # intel panel UI data
        self.pending_rank_up = None     # rank-up celebration UI data
        self.pending_monthly_report = None  # monthly financial report UI data
        self.pending_death_review = None   # pre-death battle history review
        self.active_campaign = None  # 当前进行中的战役
        self.campaign_months_left = 0  # 战役剩余月数
        self.silent = silent
        self._init_progression()
        self._unlocked_achievements = load_achievements(config.ACHIEVEMENTS_FILE)
        self._pending_achievement_msgs = []  # queued achievement unlock messages

    def _init_progression(self):
        os.makedirs(os.path.dirname(config.UNLOCK_FILE), exist_ok=True)
        self.progression = Progression(config.UNLOCK_FILE, config.HISTORY_FILE)

    def _load_reincarnation(self):
        """加载转世业力数据"""
        path = config.REINCARNATION_FILE
        if os.path.exists(path):
            try:
                import json
                with open(path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass
        return {"karma": {}, "total_deaths": 0, "total_exp_earned": 0}

    def _save_reincarnation(self, data):
        """保存转世业力数据"""
        os.makedirs(os.path.dirname(config.REINCARNATION_FILE), exist_ok=True)
        import json
        with open(config.REINCARNATION_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def new_game(self):
        """开始新游戏"""
        self.state = GameState()
        player = Character(is_player=True)

        # 转世加成：将累积的业力加到初始属性上
        reinc_data = self._load_reincarnation()
        karma = reinc_data.get("karma", {})
        if karma:
            reinc_msg = []
            for stat, bonus in karma.items():
                if bonus > 0:
                    player.stats[stat] = player.stats.get(stat, 0) + bonus
                    reinc_msg.append(f"{stat}+{bonus}")
            if reinc_msg:
                player.reincarnation_karma = karma
                self._reinc_msg = f"【转世】前世修为：{"、".join(reinc_msg)}"
        else:
            player.reincarnation_karma = {}
            self._reinc_msg = None

        player._engine_ref = self  # 供 Character.check_level_up 更新最高官职
        self.state.set_player(player)
        self.state.visited_cities = [player.location]  # Track explored cities
        self._init_npcs()
        self.running = True
        # 同步转世数据到本局状态（成就系统使用）
        self.state.run_stats["total_deaths"] = reinc_data.get("total_deaths", 0)
        self.state.run_stats["battles_this_run"] = 0
        self.state.run_stats["npcs_recruited_this_run"] = []
        self.state.run_stats["events_triggered_this_run"] = 0
        self.state.run_stats["highest_rank"] = config.INITIAL_RANK
        self.state.run_stats["highest_rank_idx"] = 0
        self.state.run_stats["total_exp_earned"] = 0
        self.state._reset_runtime_state()
        self._print_intro()

    def _init_npcs(self):
        for name, preset in NPC_PRESETS.items():
            npc = NPC(
                name=name,
                preset_stats=preset["stats"],
                rank=preset.get("rank", "武将"),
                location=preset.get("location", "未知"),
                faction=preset.get("faction", "群雄"),
                bonds=preset.get("bonds", []),
            )
            self.state.npcs[name] = npc

    def _print_intro(self):
        p = self.state.player
        karma_part = getattr(p, 'reincarnation_karma', {}) or {}
        karma_str = ""
        if karma_part:
            parts = [f"{k}+{v}" for k, v in karma_part.items() if v > 0]
            if parts:
                karma_str = f"\n【转世】前世修为：{'、'.join(parts)}\n"

        intro = f"""{'─'*50}
⚔️  三国文字Roguelike ⚔️
{'─'*50}
📅 {p.rank} | 📍 颍川
{karma_str}
黄巾乱世，英雄四起。
你的命运，将走向何方？
"""
        if not self.silent:
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

        # NPC战斗光环
        wu_bonus = 0
        zhi_bonus = 0
        ming_bonus = 0
        recruited_types = set()
        for name, flag in self.state.event_flags.items():
            if flag and name.startswith("NPC类型_"):
                recruited_types.add(flag)
        if "君主" in recruited_types:
            wu_bonus += 5
            zhi_bonus += 3
        if "武将" in recruited_types:
            wu_bonus += 5
        if "文官" in recruited_types:
            zhi_bonus += 3
        if recruited_types:
            ming_bonus = 2

        # NPC战斗光环加成（临时应用）
        if wu_bonus > 0:
            self.state.player.stats["武"] += wu_bonus
        if zhi_bonus > 0:
            self.state.player.stats["智"] += zhi_bonus
        if ming_bonus > 0:
            self.state.player.stats["名"] += ming_bonus

        session = start_combat(self.state.player, enemy, ctx, engine=self)
        session.simulate(player_action=action, active_skill=active_skill)

        # 移除临时光环加成
        if wu_bonus > 0:
            self.state.player.stats["武"] -= wu_bonus
        if zhi_bonus > 0:
            self.state.player.stats["智"] -= zhi_bonus
        if ming_bonus > 0:
            self.state.player.stats["名"] -= ming_bonus

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
            exp_gain = 30 + session.defender_damage // 8
            self.state.player.exp += exp_gain
            self.state.player.modify_stat("名", 2)

            # 战利品：敌人遗落的资源
            gold_loot = random.randint(8, 25)
            food_loot = random.randint(15, 45)
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

            # 装备掉落（20%概率）
            equip_drop_msg = ""
            if random.random() < DROP_CHANCE:
                eq = get_random_equipment()
                if len(self.state.player.equipment) < EQUIPMENT_SLOTS:
                    self.state.player.add_equipment(eq)
                    equip_drop_msg = f"\n⚙️ 拾获装备「{eq['name']}」！{eq['desc']}"
                else:
                    # Slots full — set pending equipment choice
                    self.pending_equipment = eq
                    equip_drop_msg = f"\n⚙️ 可选择替换装备「{eq['name']}」（装备槽已满）"

            loot_line = f"\n📦 战利品：金+{gold_loot}，粮+{food_loot}{merc_msg}{frag_msg}{equip_drop_msg}"
            narrative = session.get_full_narrative() + loot_line
            # Mark crit/fumble for UI effects
            self.pending_combat = self.pending_combat or {}
            self.pending_combat["crit"] = session.is_crit
            self.pending_combat["fumble"] = session.is_fumble
            # 战斗中胜利 +3 城市好感度
            self._modify_city_favorability(self.state.player.location, config.CITY_FAVORABILITY["battle_win_gain"])
            self.state.run_stats["wins"] = self.state.run_stats.get("wins", 0) + 1
            self.state.run_stats["karma_wins"] = self.state.run_stats.get("karma_wins", 0) + 1
            # 记录战斗历史
            self.state.battle_history.append({
                "year": self.state.year, "month": self.state.month,
                "enemy": enemy.name, "result": "win",
                "exp_gain": exp_gain, "gold": gold_loot, "food": food_loot,
            })
            # 战斗质量bonus：打赢比自己强 → 武业力额外奖励
            player_wu = self.state.player.get_stat("武")
            enemy_wu = enemy.get_stat("武")
            diff = enemy_wu - player_wu
            if diff > 0:
                # upset bonus: 额外+0.1~0.5（差值越大bonus越多）
                bonus = min(0.5, int(diff / 40) * 0.1)
                self.state.run_stats["karma_wins"] += bonus
            self.state.run_stats["win_streak"] = self.state.run_stats.get("win_streak", 0) + 1
            self.state.run_stats["lose_streak"] = 0
        else:
            # 战败
            self.state.run_stats["losses"] = self.state.run_stats.get("losses", 0) + 1
            self.state.run_stats["lose_streak"] = self.state.run_stats.get("lose_streak", 0) + 1
            self.state.run_stats["win_streak"] = 0
            self.state.player.food = max(0, self.state.player.food - session.attacker_damage)
            # 战斗中失败 -5 城市好感度
            self._modify_city_favorability(self.state.player.location, -config.CITY_FAVORABILITY["battle_loss_penalty"])
            self.state.player.morale = max(10, self.state.player.morale - 15)
            if session.attacker_damage > session.defender_damage * 2:
                self.state.player.take_damage(random.randint(10, 30))
            narrative = session.get_full_narrative()
            self.pending_combat = self.pending_combat or {}
            self.pending_combat["crit"] = False
            self.pending_combat["fumble"] = session.is_fumble
            self.state.battle_history.append({
                "year": self.state.year, "month": self.state.month,
                "enemy": enemy.name, "result": "loss",
                "exp_gain": 0, "gold": 0, "food": 0,
            })
        self.state.run_stats["battles_this_run"] = self.state.run_stats.get("battles_this_run", 0) + 1
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


    def show_market(self, FOOD_PRICE=10, FOOD_AMOUNT=15, FOOD_SELL_PRICE=8, FOOD_SELL_AMOUNT=15):
        """市集：可以用金买粮，也可以卖粮换金
        买：10金 → 15粮
        卖：15粮 → 8金
        """
        p = self.state.player
        print(f"""━━━ {p.location} 市集 ━━━
  🏪 粮食交易
  • 买入：{FOOD_PRICE}金 → {FOOD_AMOUNT}粮
  • 卖出：{FOOD_SELL_AMOUNT}粮 → {FOOD_SELL_PRICE}金
  你当前：金={p.gold} 粮={p.food}
  输入 'buy' 买入粮食，输入 'sell' 卖出粮食，输入 'leave' 离开""")

    def handle_market_input(self, cmd):
        """处理市集内的买卖命令"""
        p = self.state.player
        FOOD_PRICE = 10
        FOOD_AMOUNT = 15
        FOOD_SELL_PRICE = 8
        FOOD_SELL_AMOUNT = 15

        if cmd == "buy":
            if p.gold < FOOD_PRICE:
                print(f"盘缠不足，需要{FOOD_PRICE}金，你只有{p.gold}金。")
                return False
            p.gold -= FOOD_PRICE
            p.food = min(100, p.food + FOOD_AMOUNT)
            print(f"📦 买入：你付出{FOOD_PRICE}金，获得{FOOD_AMOUNT}粮。当前金{p.gold}粮{p.food}。")
            return True
        elif cmd == "sell":
            if p.food < FOOD_SELL_AMOUNT:
                print(f"粮食不足，需要{FOOD_SELL_AMOUNT}粮，你只有{p.food}粮。")
                return False
            p.food -= FOOD_SELL_AMOUNT
            p.gold += FOOD_SELL_PRICE
            print(f"💰 卖出：你付出{FOOD_SELL_AMOUNT}粮，获得{FOOD_SELL_PRICE}金。当前金{p.gold}粮{p.food}。")
            return True
        elif cmd == "leave":
            print("你离开了市集。")
            return True
        else:
            print("请输入 'buy' 或 'sell' 或 'leave'。")
            return False

    def _get_city_danger(self, city, year):
        """计算城市危险等级（1-4：低/中/高/极危），考虑年份和地点"""
        # 危险城市列表（关隘、高战乱地区）
        high_danger_cities = {"汜水关", "虎牢关", "武关", "黎阳", "仓亭", "白马"}
        mid_danger_cities = {"洛阳", "长安", "陈留", "邺城", "濮阳", "酸枣"}
        low_danger_cities = {"颍川", "南阳", "汝南", "谯郡", "建业", "吴郡", "成都", "绵竹"}

        if city in high_danger_cities:
            base = 4
        elif city in mid_danger_cities:
            base = 3
        elif city in low_danger_cities:
            base = 1
        else:
            base = 2  # 中等

        # 年份修正：190年后战争加剧
        if year >= 200:
            year_mod = 1
        elif year >= 195:
            year_mod = 0
        elif year >= 190:
            year_mod = -1
        else:
            year_mod = -2

        danger = max(1, min(4, base + year_mod))
        return danger

    def show_intel(self, cost=20):
        """花钱打听消息，获得所有重要NPC的当前位置、路线，以及城市危险等级"""
        p = self.state.player
        if p.gold < cost:
            print(f"盘缠不足，打听消息需要{cost}金，你只有{p.gold}金。")
            return
        p.gold -= cost
        current_year = self.state.year
        from world import find_path
        danger_labels = {1: "🟢低", 2: "🟡中", 3: "🟠高", 4: "🔴极危"}
        my_danger = self._get_city_danger(p.location, current_year)
        print(f"""
{'─'*40}
📰 江湖消息（花费{cost}金）
{'─'*40}
  📍当前所在: {p.location} {danger_labels.get(my_danger,'🟡中')}""")
        # 显示附近城市危险等级
        from world import get_adjacent_cities
        adj = get_adjacent_cities(p.location)
        if adj:
            adj_dangers = [f"{c}{danger_labels.get(self._get_city_danger(c, current_year),'🟡中')}" for c in adj[:5]]
            print(f"  🗺️ 邻近城市: {"  ".join(adj_dangers)}")
        print()
        for npc_name, npc in self.state.npcs.items():
            if npc.hp <= 0:
                continue
            if not is_npc_active(npc_name, current_year):
                continue
            loc = get_npc_location(npc_name, current_year)
            npc_type = getattr(npc, 'npc_type', '武将')
            type_icon = '⚔️' if npc_type == '武将' else ('📚' if npc_type == '文官' else '👑')
            faction = getattr(npc, 'faction', '群雄')
            faction_icon = {'蜀': '🟡', '魏': '🔵', '吴': '🟢', '群雄': '⚪', '民间': '⬜'}.get(faction, '⚪')
            leader_tag = ' [阵营领袖]' if is_faction_leader(npc_name) else ''
            recruited_tag = ' ✅已招募' if self.state.event_flags.get(f'已招募_{npc_name}', False) else ''

            if loc == p.location:
                location_hint = f"📍当前所在"
            else:
                path = find_path(p.location, loc)
                if path and len(path) <= 4:
                    hops = "→".join(path[1:])
                    location_hint = f"→{hops}（{len(path)-1}步）"
                else:
                    location_hint = f"「{loc}」"

            print(f"  {faction_icon}{type_icon} {npc_name} {location_hint}{leader_tag}{recruited_tag}")
        # 显示阵营协同加成
        synergy = self.get_faction_synergy_bonus()
        if synergy > 0:
            print(f"  🏅 阵营协同: 武+{synergy*2}（同阵营≥2人加成中）")
        # 显示已招募阵营统计
        factions = self.get_recruited_factions()
        if factions:
            faction_desc = "、".join([f"{k}{v}人" for k, v in factions.items()])
            print(f"  已招募: {faction_desc}")
        print()

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

        # Track visited cities for exploration progress
        if target_city not in self.state.visited_cities:
            self.state.visited_cities.append(target_city)
            # Explorer 专属奖励：首次到达新城市 → +1 传承碎片
            self.state.player.inheritance_fragments += 1
            self.state.run_stats["exploration_rewards"] = self.state.run_stats.get("exploration_rewards", 0) + 1

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
            f"  🏪 市集 — 输入 'market' 买卖粮食",
            f"  🍶 酒馆 — 输入 'intel' 打听消息（20金）",
        ]
        if encounter:
            result.append(f"\n{encounter}")

        # 设置待处理市集状态（进城时提示）
        self.pending_market = True

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

    def _check_campaign(self):
        """Check if a campaign should trigger this tick. Returns Campaign or None."""
        # If already active, handle campaign tick
        if self.active_campaign:
            self.campaign_months_left -= 1
            if self.campaign_months_left <= 0:
                # Campaign ended — award reward
                campaign = self.active_campaign
                self.active_campaign = None
                self.campaign_months_left = 0
                flag = f"campaign_{campaign.id}_resolved"
                self.state.event_flags[flag] = True
                self.state.event_flags[f"campaign_{campaign.id}_completed"] = True
                # Award one of the rewards
                if campaign.rewards:
                    reward = campaign.rewards[0]
                    if reward["type"] == "equipment":
                        eq = dict(reward)
                        eq.pop("type")
                        if self.state.player.add_equipment(eq):
                            pass
                    elif reward["type"] == "skill":
                        skill_id = reward.get("skill_id")
                        if skill_id:
                            self.state.player.add_skill(skill_id)
                return None
            return None

        # Check for new campaign trigger
        campaign = check_campaign_trigger(self.state)
        if campaign:
            self.pending_campaign = campaign
        return campaign

    def _process_campaign_combat(self, enemy, ctx):
        """Wrap a combat encounter with campaign modifiers."""
        campaign = self.active_campaign
        if campaign:
            for stat in enemy.stats:
                enemy.stats[stat] = int(enemy.stats[stat] * 1.3)
            enemy.troops = int(enemy.troops * 1.3)
        return {"enemy": enemy, "ctx": ctx}

    def _tick_campaign(self):
        """Tick active campaign state (extra food consumption)."""
        if not self.active_campaign:
            return
        # Double food consumption during campaign
        self.state.player.food = max(0, self.state.player.food - 3)

    def _on_rank_up(self, old_rank, new_rank):
        """Called by Character.check_level_up when player is promoted."""
        self.pending_rank_up = {
            "old_rank": old_rank,
            "new_rank": new_rank,
        }


    def tick(self):
        """推进一个月"""
        self.state.tick()
        year, month = self.state.year, self.state.month

        # 检查战役状态
        self._tick_campaign()

        # 检查选择事件
        choice_event = check_choice_events(self.state)
        if choice_event:
            self.pending_choice = choice_event
            return {
                "time": f"{year}年{month}月",
                "choice_event": {
                    "id": choice_event.id,
                    "name": choice_event.name,
                    "description": choice_event.description,
                    "options": [
                        {"id": opt["id"], "label": opt["label"], "desc": opt["desc"]}
                        for opt in choice_event.options
                    ],
                },
            }

        # 检查战役触发
        campaign = self._check_campaign()
        if campaign:
            self.pending_campaign = campaign
            return {
                "time": f"{year}年{month}月",
                "campaign_pending": {
                    "id": campaign.id,
                    "name": campaign.name,
                    "description": campaign.description,
                    "duration": campaign.duration,
                    "rewards": campaign.rewards,
                    "side_choice": campaign.side_choice,
                    "combat_intro": campaign.combat_intro,
                },
            }

        # 检查必然事件
        mandatory_result = trigger_mandatory_event(self.state, year, month)
        if mandatory_result:
            self.state.run_stats["karma_history_events"] = self.state.run_stats.get("karma_history_events", 0) + 1
            self.state.run_stats["events_triggered_this_run"] = self.state.run_stats.get("events_triggered_this_run", 0) + 1
            self.state.history_log.append({"year": year, "month": month, "name": mandatory_result["name"], "type": "mandatory"})

        # 检查条件事件
        conditional_results = []
        for evt in get_default_conditional_events():
            r = evt.check_and_trigger(self.state)
            if r:
                conditional_results.append(r)
                self.state.run_stats["karma_history_events"] = self.state.run_stats.get("karma_history_events", 0) + 1
                self.state.run_stats["events_triggered_this_run"] = self.state.run_stats.get("events_triggered_this_run", 0) + 1
                self.state.history_log.append({"year": year, "month": month, "name": r.get("name", "未知事件"), "type": "conditional"})

        # 检查特殊事件
        for evt in [taoyuan_oath_event(), huarong_road_event(), three_visits_to_zhuge_event()]:
            r = evt.check_and_trigger(self.state)
            if r:
                conditional_results.append(r)
                self.state.run_stats["karma_history_events"] = self.state.run_stats.get("karma_history_events", 0) + 1
                self.state.run_stats["events_triggered_this_run"] = self.state.run_stats.get("events_triggered_this_run", 0) + 1

        # 自然恢复
        self._natural_recovery()

        # ============ 城市好感度每月变化 ============  
        self._tick_favorability_monthly()

        # ============ NPC 位置同步（Timeline → 实际位置）============
        self._sync_npc_locations()

        # 随机事件（单挑/舌战/奇遇/凶兆）
        random_results = []
        try:
            from random_events import trigger_random_events
            random_results = trigger_random_events(self.state)
            # 统计舌战胜和稀有奇遇
            for r in random_results:
                if r.get("name") == "舌战" and r.get("type") == "positive":
                    # 舌战胜：智+0.5业力（需统计胜败）
                    self.state.run_stats["karma_speech_wins"] = self.state.run_stats.get("karma_speech_wins", 0) + 1
                if r.get("name") in ("山洞奇遇", "秘笈传承", "老兵传授", "商队赠礼", "名师指点"):
                    self.state.run_stats["karma_rare_encounters"] = self.state.run_stats.get("karma_rare_encounters", 0) + 1
        except Exception:
            pass

        # ============ 战斗遭遇检查 ============
        combat_result = self._check_combat_encounter()

        # ============ NPC 遭遇检查（本地 + 附近） ============
        encounter = self._check_npc_encounter()  # 仅检查同城

        if self.state.is_game_over():
            self.running = False
            return None

        # 优先处理战役介绍
        if self.pending_campaign:
            self._check_achievements()
            return {
                "time": f"{year}年{month}月",
                "pending_campaign": {
                    "id": self.pending_campaign.id,
                    "name": self.pending_campaign.name,
                    "description": self.pending_campaign.description,
                    "duration": self.pending_campaign.duration,
                    "rewards": self.pending_campaign.rewards,
                    "side_choice": self.pending_campaign.side_choice,
                },
            }

        # 优先处理选择事件
        if self.pending_choice:
            self._check_achievements()
            return {
                "time": f"{year}年{month}月",
                "choice_event": {
                    "id": self.pending_choice.id,
                    "name": self.pending_choice.name,
                    "description": self.pending_choice.description,
                    "options": [
                        {"id": opt["id"], "label": opt["label"], "desc": opt["desc"]}
                        for opt in self.pending_choice.options
                    ],
                },
            }

        # 优先处理战斗
        if combat_result:
            self._check_achievements()
            return {
                "time": f"{year}年{month}月",
                "mandatory": mandatory_result,
                "conditionals": conditional_results,
                "random_events": random_results,
                "combat": combat_result,
            }

        if encounter:
            self.pending_npc_encounter = encounter
            self._check_achievements()
            return {
                "time": f"{year}年{month}月",
                "mandatory": mandatory_result,
                "conditionals": conditional_results,
                "random_events": random_results,
                "npc_encounter": encounter,
            }

        self._check_achievements()
        return {
            "time": f"{year}年{month}月",
            "mandatory": mandatory_result,
            "conditionals": conditional_results,
            "random_events": random_results,
        }

    def _check_achievements(self):
        """检查所有成就是否满足解锁条件，打印并保存"""
        newly = check_achievements(self.state, self._unlocked_achievements)
        for ach in newly:
            self._unlocked_achievements.add(ach.id)
            # 打印成就解锁消息
            msg = f"\n🏆 成就解锁：「{ach.name}」- {ach.desc}"
            if ach.karma_reward > 0:
                msg += f" (+{ach.karma_reward}业力)"
            if not self.silent:
                print(msg)
            self._pending_achievement_msgs.append(msg)
            # 应用业力奖励
            if ach.karma_reward > 0:
                karma_data = self._load_reincarnation()
                player_karma = karma_data.setdefault("karma", {})
                # 分配到随机一项属性
                stat = ["武", "智", "名", "魅", "运"][self.state.turn_count % 5]
                player_karma[stat] = player_karma.get(stat, 0) + ach.karma_reward
                self._save_reincarnation(karma_data)
        if newly:
            save_achievements(config.ACHIEVEMENTS_FILE, self._unlocked_achievements)

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

        # 基础25%概率遇上有候选的NPC
        if random.random() > 0.25:
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
        base_chance = 0.32 + fame_mod

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
        # 官职月俸
        salary = config.RANK_SALARY.get(p.rank, 5)
        p.gold += salary
        # 月度收支报告（粮草-3，体力恢复+25，金扣除+俸禄）
        campaign_penalty = 3 if self.active_campaign else 0
        self.pending_monthly_report = {
            "food_cost": 3 + campaign_penalty,
            "gold_spent": 1,
            "salary": salary,
            "food_before": p.food + 3 + campaign_penalty,
            "food_after": p.food,
            "gold_before": p.gold - salary + 1,
            "gold_after": p.gold,
            "campaign_active": bool(self.active_campaign),
        }
        if p.food == 0:
            if "饥饿" not in p.effects:
                p.effects.append("饥饿")
                p.morale = max(0, p.morale - 15)
            # 饥饿每回合扣血
            p.take_damage(5)
        else:
            if "饥饿" in p.effects:
                p.effects.remove("饥饿")

    def _get_equipment_karma_cap_bonus(self, stat):
        """获取装备提供的业力上限加成（额外+20每件传奇装备）"""
        if not self.state or not self.state.player:
            return 0
        bonus = 0
        for eq in self.state.player.equipment:
            if eq.get("tier") == "传奇":
                tier_bonus = eq.get("stat_bonus", {})
                # 传奇装备对武额外+20，其他属性+10
                if stat == "武":
                    bonus += 20
                else:
                    bonus += 10
        return bonus

    def _sync_npc_locations(self):
        """每月同步 NPC 实际位置为 timeline 位置"""
        if not self.state or not self.state.npcs:
            return
        year = self.state.year
        for name, npc in self.state.npcs.items():
            if npc.hp <= 0:
                continue
            new_loc = get_npc_location(name, year)
            if new_loc and new_loc != npc.location:
                npc.location = new_loc

    def get_bond_synergy_bonus(self):
        """计算羁绊协同加成（同羁绊≥2人触发，按比例计算加成）"""
        if not self.state:
            return {}
        bond_stat_bonus = {}
        for bond_id, bond_def in BOND_DEFINITIONS.items():
            members = bond_def["members"]
            recruited = [m for m in members if self.state.event_flags.get(f"已招募_{m}", False)]
            if len(recruited) < 2:
                continue
            # 按比例计算加成（2/3桃园三兄弟 → 获得66%的羁绊加成）
            ratio = len(recruited) / len(members)
            for stat, val in bond_def.get("synergy_bonus", {}).items():
                bond_stat_bonus[stat] = bond_stat_bonus.get(stat, 0) + val * ratio
        return bond_stat_bonus

    def get_total_synergy_bonus(self):
        """阵营+羁绊总协同加成，返回总百分比"""
        if not self.state:
            return 0
        # 阵营协同
        faction_counts = {"蜀": 0, "魏": 0, "吴": 0, "群雄": 0, "民间": 0}
        for name, npc in self.state.npcs.items():
            if self.state.event_flags.get(f"已招募_{name}", False):
                faction = getattr(npc, 'faction', '群雄')
                if faction in faction_counts:
                    faction_counts[faction] += 1
        faction_synergy = 0
        for count in faction_counts.values():
            if count >= 2:
                faction_synergy += (count - 1) * 2
        # 羁绊协同（百分比加成的百分比估算）
        bond_bonus = self.get_bond_synergy_bonus()
        bond_pct = sum(bond_bonus.values())  # 把属性加成估算为百分比
        return faction_synergy + int(bond_pct)

    def get_faction_synergy_bonus(self):
        """计算阵营协同加成（招募的NPC中同阵营的人数）"""
        if not self.state:
            return 0
        faction_counts = {"蜀": 0, "魏": 0, "吴": 0, "群雄": 0, "民间": 0}
        for name, npc in self.state.npcs.items():
            if self.state.event_flags.get(f"已招募_{name}", False):
                faction = getattr(npc, 'faction', '群雄')
                if faction in faction_counts:
                    faction_counts[faction] += 1
        total = 0
        for count in faction_counts.values():
            if count >= 2:
                total += (count - 1) * 2
        return total

    def get_recruited_factions(self):
        """返回已招募NPC的阵营统计"""
        faction_counts = {"蜀": 0, "魏": 0, "吴": 0, "群雄": 0, "民间": 0}
        for name, npc in self.state.npcs.items():
            if self.state.event_flags.get(f"已招募_{name}", False):
                faction = getattr(npc, 'faction', '群雄')
                if faction in faction_counts:
                    faction_counts[faction] += 1
        return {k: v for k, v in faction_counts.items() if v > 0}

    def _check_and_trigger_bond_discovery(self, npc_name):
        """检测并触发羁绊发现提示"""
        if npc_name not in NPC_PRESETS:
            return
        bonds = NPC_PRESETS[npc_name].get("bonds", [])
        discovered = []
        completed = []
        for bond_id in bonds:
            if bond_id not in BOND_DEFINITIONS:
                continue
            bond = BOND_DEFINITIONS[bond_id]
            members = bond["members"]
            # 统计当前已招募的成员数
            recruited = sum(1 for m in members if self.state.event_flags.get(f"已招募_{m}", False))
            # 当前招募后会是几人
            after_recruit = recruited + 1
            if after_recruit == len(members):
                completed.append(bond_id)
            elif after_recruit >= 2:
                discovered.append(bond_id)
        # 显示提示
        if completed:
            msg = f"\n🌟✨ 【{npc_name}】加入，【{completed[0]}】羁绊满员！\n  → {BOND_DEFINITIONS[completed[0]]['completion_desc']}"
            self._add_narrative(msg)
            self.state.event_flags[f"羁绊满员_{completed[0]}"] = True
            self.apply_completion_bonus(completed[0])
        elif discovered:
            msg = f"\n🌸 【{npc_name}】加入，发现【{discovered[0]}】羁绊！\n  → {BOND_DEFINITIONS[discovered[0]]['desc']}"
            self._add_narrative(msg)

    def apply_completion_bonus(self, bond_id):
        """应用羁绊满员效果"""
        if bond_id not in BOND_DEFINITIONS:
            return
        bond = BOND_DEFINITIONS[bond_id]
        bonus = bond.get("completion_bonus", {})
        p = self.state.player
        if "技能" in bonus:
            skill_id = bonus["技能"]
            skill = get_skill(skill_id)
            if skill:
                # 给玩家满级或解锁该技能
                if skill.skill_type == "passive":
                    if skill_id not in p.passive_skills:
                        p.passive_skills.append(skill_id)
                else:
                    if skill_id not in p.active_skills:
                        p.active_skills.append(skill_id)
                self._add_narrative(f"  🎯 解锁【{skill.name}】！")
        if "被动" in bonus:
            passive_id = bonus["被动"]
            if passive_id not in p.passive_skills:
                p.passive_skills.append(passive_id)
            self._add_narrative(f"  🎯 获得被动【{passive_id}】！")
        if "称号" in bonus:
            title = bonus["称号"]
            self.state.event_flags[f"称号_{title}"] = True
            self._add_narrative(f"  🎯 获得称号【{title}】！")

        cf = self.state.city_favorability
        if not cf:
            cf = {}
        player_city = self.state.player.location
        cf[player_city] = cf.get(player_city, config.CITY_FAVORABILITY["neutral"]) + config.CITY_FAVORABILITY["monthly_gain"]
        cf[player_city] = min(100, cf[player_city])
        self.state.city_favorability = cf

    def _modify_city_favorability(self, city, delta):
        """增减城市好感度"""
        cf = self.state.city_favorability
        if not cf:
            cf = {}
        cf[city] = cf.get(city, config.CITY_FAVORABILITY["neutral"]) + delta
        cf[city] = max(0, min(100, cf[city]))
        self.state.city_favorability = cf

    def _tick_favorability_monthly(self):
        """每月城市好感度自然变化（所有城市+1）"""
        cf = self.state.city_favorability
        if not cf:
            return
        for city in list(cf.keys()):
            # 每月自然+1，但有上限
            cf[city] = min(100, cf[city] + 1)
        self.state.city_favorability = cf

    def _add_narrative(self, msg):
        """添加叙事文本（silent模式下忽略）"""
        if not self.silent:
            print(msg)

    def get_city_favorability(self, city):
        """获取城市好感度（未设置则返回中立50）"""
        return self.state.city_favorability.get(city, config.CITY_FAVORABILITY["neutral"])

    def get_market_price_mod(self, city):
        """根据城市好感度返回市场价格修正（负数=折扣）"""
        fav = self.get_city_favorability(city)
        cfg = config.CITY_FAVORABILITY
        if fav >= cfg["allied_threshold"]:
            return -0.20
        elif fav >= cfg["friendly_threshold"]:
            return -0.10
        elif fav <= cfg["hostile_threshold"]:
            return 0.15
        return 0.0

    def get_recruit_bonus(self, city):
        """根据城市好感度返回招募加成（正数=成功率提升）"""
        fav = self.get_city_favorability(city)
        cfg = config.CITY_FAVORABILITY
        if fav >= cfg["allied_threshold"]:
            return 0.20
        elif fav >= cfg["friendly_threshold"]:
            return 0.10
        elif fav <= cfg["hostile_threshold"]:
            return -0.20
        return 0.0

    def show_status(self):
        """显示当前状态"""
        p = self.state.player
        time_str = self.state.get_time_str()
        print(f"\n─────────────")
        print(f"📅 {time_str} | 📍 {p.location}")
        print(format_character_info(p))
        print(f"─────────────")

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
            # 交谈后：下次招募该NPC时+10%成功率
            self.state.event_flags[f"talked_{npc_name}"] = True
            self.state.run_stats["karma_conversation"] = self.state.run_stats.get("karma_conversation", 0) + 0.2
            self.pending_npc_encounter = None
            return  # 保持遭遇状态，可以继续选择其他选项

        elif choice == "6":  # 索取情报
            intel = self._get_npc_intel(npc, detailed=True)
            print(intel)
            # 索取情报后：下次招募该NPC时+10%成功率
            self.state.event_flags[f"intel_{npc_name}"] = True
            self.state.run_stats["karma_intel"] = self.state.run_stats.get("karma_intel", 0) + 0.3
            self.pending_npc_encounter = None
            return  # 保持遭遇状态，可以继续选择其他选项

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
            base_rate = 0.30
        elif npc.name in mid_tier:
            base_rate = 0.45
        else:
            base_rate = 0.60

        # ========== 玩家官职修正（0~9级官职 -> 0% ~ +27%）==========
        rank_mod = rank_idx * 0.03

        # ========== 玩家魅力修正（50基准，100满魅力 +15%）==========
        charisma_mod = max(-0.15, (p.get_stat("魅") - 30) / 60 * 0.15)

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

        # ========== 多轮互动加成（交谈/索取情报后，下次招募+10%）==========
        interaction_bonus = 0.0
        if self.state.event_flags.get(f"talked_{npc.name}", False):
            interaction_bonus += 0.10
        if self.state.event_flags.get(f"intel_{npc.name}", False):
            interaction_bonus += 0.10

        # ========== 对话策略 ==========
        strategy_mods = {
            "sincere": 0.10,
            "bribe": 0.05,
            "righteous": 0.05,
            "coerce": -0.20,
        }
        strategy_mod = strategy_mods.get(strategy, 0.0)

        # 招募成功后的行为业力bonus（对话方式决定额外加成）
        strategy_bonus = {
            "sincere": {"魅": 0.3},
            "bribe": {"魅": 0.5},
            "righteous": {"名": 0.5, "智": 0.3},
            "coerce": {"魅": 1.0},
        }

        # NPC类型bonus
        npc_type_bonus = {
            "武将": {"武": 0.3},
            "文官": {"智": 0.5},
            "君主": {"名": 1.0, "魅": 0.5},
        }

        # ========== 消耗处理 ==========
        cost = 30 if strategy == "bribe" else (20 if strategy == "coerce" else 0)
        if cost > 0:
            p.gold -= cost

        final_rate = (base_rate + rank_mod + charisma_mod + npc_stat_mod
                     + rel_mod + strategy_mod + interaction_bonus)
        final_rate = max(0.05, min(0.90, final_rate))

        success = random.random() < final_rate

        if success:
            self.state.event_flags[f"已招募_{npc.name}"] = True
            self.state.event_flags[f"NPC类型_{npc.name}"] = npc.npc_type
            p.modify_relation(npc.name, 20)

            # 记录招募 + 行为业力奖励
            if npc.name not in self.state.run_stats.get("npcs_recruited_this_run", []):
                self.state.run_stats.setdefault("npcs_recruited_this_run", []).append(npc.name)
                base_bonus = 1.0

                # NPC类型额外奖励
                if npc.npc_type in npc_type_bonus:
                    for stat, val in npc_type_bonus[npc.npc_type].items():
                        self.state.run_stats[f"karma_npc_recruited"] = self.state.run_stats.get("karma_npc_recruited", 0) + val

                # 策略难度额外奖励
                if strategy in strategy_bonus:
                    for stat, val in strategy_bonus[strategy].items():
                        self.state.run_stats[f"karma_npc_recruited"] = self.state.run_stats.get("karma_npc_recruited", 0) + val

            # 在该城市招募 +5 好感度
            self._modify_city_favorability(self.state.player.location, config.CITY_FAVORABILITY["recruit_gain"])
            # 主线预告：首次加入曹操或孙权阵营
            if npc.name in ("曹操", "孙权") and not self.state.event_flags.get(f"主线预告_{npc.name}", False):
                self.state.event_flags[f"主线预告_{npc.name}"] = True
                preview_texts = {
                    "曹操": "你投身曹操麾下，操已席卷中原，挟天子以令诸侯。然而袁绍才是眼前大敌，官渡之战一触即发——你的谋略将决定天下的走向。",
                    "孙权": "你归入孙权帐下，江东基业有待稳固。然而曹操已定荆州，虎视江东，赤壁之战迫在眉睫——这便是你的第一个考验。",
                }
                self.state.active_events.append({
                    "name": "主线预告",
                    "desc": preview_texts.get(npc.name, ""),
                })
            gift = NPC_GIFT_SKILLS.get(npc.name)
            gift_msg = ""
            if gift:
                skill = get_skill(gift["skill_id"])
                if skill:
                    p.add_skill(gift["skill_id"])
                    gift_msg = f"\n「你我共事，我有一技相赠——」\n「此乃'{skill.name}'，愿你善用之。」\n（获得技能：{skill.name}）"
            # 羁绊发现检测
            self._check_and_trigger_bond_discovery(npc.name)
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

    def handle_campaign_choice(self, accept, side=None):
        """Handle player's accept/decline for a pending campaign."""
        campaign = self.pending_campaign
        if not campaign:
            return
        self.pending_campaign = None
        flag = f"campaign_{campaign.id}_resolved"
        self.state.event_flags[flag] = True
        if not accept:
            self.state.event_flags[f"campaign_{campaign.id}_skipped"] = True
            return
        # Accept: start campaign
        self.active_campaign = campaign
        self.campaign_months_left = campaign.duration
        self.state.event_flags[f"campaign_{campaign.id}_active"] = True
        if side and campaign.side_choice:
            self.state.event_flags[f"campaign_{campaign.id}_side"] = side

    def handle_campaign_retreat(self):
        """Player retreats from active campaign (with penalty)."""
        if not self.active_campaign:
            return
        campaign = self.active_campaign
        flag = f"campaign_{campaign.id}_resolved"
        self.state.event_flags[flag] = True
        self.state.event_flags[f"campaign_{campaign.id}_retreated"] = True
        self.active_campaign = None
        self.campaign_months_left = 0
        # 名望惩罚
        self.state.player.modify_stat("名", -20)

    def handle_equipment_choice(self, slot_index):
        """Replace equipment at slot_index with pending equipment drop."""
        if self.pending_equipment is None:
            return
        if slot_index is not None:
            self.state.player.remove_equipment(slot_index)
        self.state.player.add_equipment(self.pending_equipment)
        self.pending_equipment = None

    def handle_choice_event(self, choice_id):
        """Handle player's choice selection from a choice_event."""
        if not self.pending_choice:
            return
        evt = self.pending_choice
        for opt in evt.options:
            if opt["id"] == choice_id:
                opt["effect"](self.state)
                flag = f"choice_{evt.id}_resolved"
                self.state.event_flags[flag] = True
                break
        self.pending_choice = None

    def show_death_screen(self, fragments_earned, months_survived,
                          battles=0, npcs_recruited=None,
                          highest_rank=None, events_triggered=0,
                          exp_earned=0):
        """显示死亡界面（遗产商店 + 本局结算 + 转世叙事）"""
        from skills import SKILLS, can_learn_skill, get_skill

        if npcs_recruited is None:
            npcs_recruited = []
        if highest_rank is None:
            highest_rank = self.state.player.rank if self.state.player else "散兵"

        p = self.state.player
        p.inheritance_fragments += fragments_earned

        years_survived = months_survived // 12
        months_remain = months_survived % 12
        npc_list = ', '.join(npcs_recruited) if npcs_recruited else '无'

        print(f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💀 你已陨于乱世
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 【本局总结】
  ⏱️  存活时间：{years_survived}年{months_remain}月
  ⚔️  战斗次数：{battles}次
  👥  招募NPC：{len(npcs_recruited)}人（{npc_list}）
  🏅  最高官职：{highest_rank}
  🎁  获得传承碎片：+{fragments_earned}枚
  📈  本局获得经验值：{exp_earned}
  📜  触发历史事件：{events_triggered}次

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📦 【传承商店】
  当前碎片余额：{p.inheritance_fragments}枚

【传承主动技能】
""")

        # 显示可购买技能（带描述）
        active_skills = []
        passive_skills = []
        for sid, skill in SKILLS.items():
            if skill.cost == 0:
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
                print(f"  {idx}. {skill.name} [{skill.cost}碎片] - {skill.desc}")
                choices.append(sid)
                idx += 1

        print(f"\n【传承被动技能】")
        for sid, skill, can_learn, reason in passive_skills:
            if can_learn:
                print(f"  {idx}. {skill.name} [{skill.cost}碎片] - {skill.desc}")
                choices.append(sid)
                idx += 1

        if not choices:
            print("  （暂无可购买技能）")

        print(f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
输入数字购买技能，输入 0 直接开始新游戏
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
        except (ValueError, EOFError):
            pass

        # ========== 转世叙事强化 ==========
        karma_data = self._load_reincarnation()
        karma_data["total_deaths"] = karma_data.get("total_deaths", 0) + 1
        total_lives = karma_data["total_deaths"]
        player_karma = karma_data.setdefault("karma", {})

        carry_rates = config.REINCARNATION_CARRY_RATES
        caps = config.REINCARNATION_CAPS
        rs = self.state.run_stats
        karma_gain_display = []
        karma_gain_values = {}

        # 行为业力贡献（主要来源）
        # 行为业力贡献（主要来源）
        # 武: 战斗胜利基础0.3/场 + upset bonus(差值/40*0.1)，结果取整
        # 其他: 直接取整
        behavior_karma = {
            "武": round(rs.get("karma_wins", 0) * 0.3, 1),
            "魅": round(rs.get("karma_npc_recruited", 0) + rs.get("karma_conversation", 0) * 0.2, 1),
            "名": int(rs.get("karma_history_events", 0) * 0.5),
            "智": int(rs.get("karma_speech_wins", 0) * 0.5 + rs.get("karma_intel", 0) * 0.3),
            "运": int(rs.get("karma_rare_encounters", 0) * 0.5),
        }

        # 死亡属性微调（5%，作为行为贡献的补充）
        death_karma = {
            stat: int(p.stats.get(stat, 0) * 0.05)
            for stat in ["武", "智", "名", "魅", "运"]
        }

        for stat in ["武", "智", "名", "魅", "运"]:
            carry = int(behavior_karma.get(stat, 0) + death_karma.get(stat, 0))
            if carry > 0:
                cap = caps.get(stat, 20)
                before = player_karma.get(stat, 0)
                eq_bonus = self._get_equipment_karma_cap_bonus(stat)
                total_cap = cap + eq_bonus
                player_karma[stat] = min(total_cap, before + carry)
                karma_gain_values[stat] = carry
                parts = []
                if behavior_karma.get(stat, 0) > 0:
                    parts.append(f"行{behavior_karma[stat]}")
                if death_karma.get(stat, 0) > 0:
                    parts.append(f"死{death_karma[stat]}")
                karma_gain_display.append(f"{stat}+{' + '.join(parts)}")

        self._save_reincarnation(karma_data)

        # 业力来源映射
        karma_sources = {
            "武": {"战斗胜利": rs.get("karma_wins", 0),
                   "挑战强敌": rs.get("karma_upsets", 0)},
            "魅": {"招募NPC": rs.get("karma_npc_recruited", 0),
                    "深入交谈": rs.get("karma_conversation", 0) * 0.2},
            "名": {"触发历史事件": rs.get("karma_history_events", 0)},
            "智": {"舌战胜": rs.get("karma_speech_wins", 0) * 0.5,
                   "索取情报": rs.get("karma_intel", 0) * 0.3},
            "运": {"稀有遭遇": rs.get("karma_rare_encounters", 0) * 0.5},
        }

        def progress_bar(current, cap, width=10):
            if cap <= 0:
                return "▓" * width
            filled = min(width, int(current / cap * width))
            return "▓" * filled + "░" * (width - filled)

        def next_threshold(current, step=20):
            return (current // step + 1) * step

        print(f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🌀 你的灵魂在乱世中游荡...
   轮回之力将你重新投入193年的风暴中。
""")

        # 本局来源明细
        print("📜 【本局业力来源】")
        has_any = False
        for stat in ["武", "智", "名", "魅", "运"]:
            b_val = behavior_karma.get(stat, 0)
            d_val = death_karma.get(stat, 0)
            total_val = b_val + d_val
            if total_val > 0:
                has_any = True
                parts_src = []
                for label, val in karma_sources.get(stat, {}).items():
                    if val > 0:
                        parts_src.append(f"{label}+{int(val)}")
                src_str = " / ".join(parts_src) if parts_src else "（无记录）"
                print(f"  {stat}：+{int(total_val)}  （{src_str}）")
        if not has_any:
            print("  本局无业力累积")

        print(f"""

🌅 你已完成 {total_lives} 次轮回。当前总业力：
""")

        # 进度条展示
        for stat in ["武", "智", "名", "魅", "运"]:
            val = player_karma.get(stat, 0)
            cap_stat = caps.get(stat, 20)
            eq_bonus = self._get_equipment_karma_cap_bonus(stat)
            total_cap = cap_stat + eq_bonus
            if val > 0 or total_cap > 0:
                bar = progress_bar(val, total_cap)
                next_val = next_threshold(val)
                remaining = max(0, next_val - val)
                print(f"  {stat}：{val:>4} / {total_cap:<4}  {bar}  （距下级 {remaining}）")
            else:
                print(f"  {stat}：0 / {total_cap}  {"░" * 10}  （距下级 20）")

        print(f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✨【转世成功】✨
   轮回数：{total_lives}世
   本次转世加成：{', '.join(karma_gain_display) if karma_gain_display else '无'}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""")

        # 成就系统：检查死亡相关成就
        self._check_achievements()

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

    def show_final_score(self):
        """显示结局分数，统计本局成就"""
        p = self.state.player
        months = (self.state.year - 184) * 12 + self.state.month
        years = months // 12
        remaining_months = months % 12

        # 评分维度
        rank_score = {
            "散兵": 1, "什长": 2, "伍长": 3, "队长": 4,
            "曲长": 5, "司马": 7, "校尉": 10, "中郎将": 15,
            "牙门将": 20, "偏将军": 30, "裨将军": 40,
            "镇北将军": 60, "安南将军": 80, "车骑将军": 100,
            "大将军": 150, "诸侯": 200
        }
        rank_pts = rank_score.get(p.rank, 1)

        # 技能数
        skill_pts = (len(p.active_skills) + len(p.passive_skills)) * 10

        # 招募NPC
        npc_pts = len([k for k, v in self.state.event_flags.items() if k.startswith("已招募_") and v]) * 15

        # 属性
        attr_pts = (p.get_stat("武") + p.get_stat("智") + p.get_stat("名") + p.get_stat("魅") + p.get_stat("运")) * 2

        total = rank_pts + skill_pts + npc_pts + attr_pts + months

        print(f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
【本局评价】

📅 游戏时长：{years}年{remaining_months}月
🏅 最高官职：{p.rank} (+{rank_pts})
⚔️ 习得技能：{len(p.active_skills)}主动 + {len(p.passive_skills)}被动 (+{skill_pts})
👥 招募武将：{npc_pts // 15}人 (+{npc_pts})
📊 属性总和：{p.get_stat("武")+p.get_stat("智")+p.get_stat("名")+p.get_stat("魅")+p.get_stat("运")} (+{attr_pts})
🎯 存活回合：+{months}

★ 总分：{total}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""")
        return total

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
📖 命令帮助
─────────────
1/2/3/4  - 战斗选择（进攻/坚守/撤退/用计）
t        - 推进时间（1个月）
s        - 查看状态
m        - 查看地图
move [城]- 移动到某城市
market   - 集市买卖
int      - NPC情报
h        - 显示帮助
q        - 退出
─────────────
""")


def main():
    engine = SanguoEngine()
    engine.new_game()

    print("\n📖 输入 'h' 查看命令 | 'm' 查看地图")

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

            # 如果在市集中
            if engine.pending_market:
                engine.show_market()
                cmd = input("> ").strip()
                done = engine.handle_market_input(cmd)
                if done:
                    engine.pending_market = False
                    engine.show_status()
                continue

            cmd = input("\n> ").strip()
            if not cmd:
                continue

            parts = cmd.split(maxsplit=1)
            base_cmd = parts[0].lower()
            arg = parts[1] if len(parts) > 1 else ""

            # 别名映射
            alias_map = {
                "t": "tick", "tick": "tick",
            }
            if base_cmd in alias_map:
                base_cmd = alias_map[base_cmd]
            # 处理单字符别名
            if base_cmd in ["s", "st"]:  # status
                base_cmd = "status"
            elif base_cmd in ["m", "mp"]:  # map
                base_cmd = "map"
            elif base_cmd in ["i", "int"]:  # intel
                base_cmd = "intel"
            elif base_cmd in ["h", "?", "help"]:  # help
                base_cmd = "help"
            elif base_cmd in ["q", "quit", "exit"]:  # quit
                base_cmd = "quit"

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
                # 进入市集（设置pending状态进入交互循环）
                engine.pending_market = True
                engine.show_market()
                cmd = input("> ").strip()
                done = engine.handle_market_input(cmd)
                if done:
                    engine.pending_market = False
            elif base_cmd == "tick":
                result = engine.tick()
                if result is None and engine.state.is_game_over():
                    months = engine.state.get_elapsed_months()
                    # 到达220年 = 结局，不是死亡
                    if engine.state.year >= END_YEAR and engine.state.player.hp > 0:
                        engine.resolve_ending("three_kingdoms")
                        # 结局后计算分数，重开新游戏
                        engine.show_final_score()
                        engine.new_game()
                    else:
                        # 死亡：记录历史并显示死亡界面
                        fragments = 5 + ((months + 5) // 6)
                        rs = engine.state.run_stats
                        # 写入史籍
                        engine.progression.record_death(
                            player=engine.state.player,
                            cause="陨落",
                            context={
                                "year": engine.state.year,
                                "month": engine.state.month,
                                "kills": rs.get("battles_this_run", 0),
                            }
                        )
                        engine.show_death_screen(
                            fragments_earned=fragments,
                            months_survived=months,
                            battles=rs.get("battles_this_run", 0),
                            npcs_recruited=rs.get("npcs_recruited_this_run", []),
                            highest_rank=rs.get("highest_rank", engine.state.player.rank),
                            events_triggered=rs.get("events_triggered_this_run", 0),
                            exp_earned=rs.get("total_exp_earned", 0),
                        )
                    continue
                if result:
                    engine.show_status()
                    # 随机事件（单挑/舌战/奇遇/凶兆）
                    for evt in result.get("random_events", []):
                        if evt.get("type") == "positive":
                            print(f"\n✨【{evt['name']}】{evt['desc']}")
                        elif evt.get("type") == "negative":
                            print(f"\n💥【{evt['name']}】{evt['desc']}")
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