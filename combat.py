"""
战斗系统 v2 - 基于掷骰子的玩家决策战斗
"""
import random
import config
from narrative import get_number_desc


# ============ 战斗选项定义 ============
COMBAT_ACTIONS = {
    "进攻": {
        "description": "全军压上，奋勇向前",
        "win_rate_mod": +0.12,
        "morale_mod": -5,
        "stamina_mod": -12,
        "damage_mod": 1.3,
        "risk_mod": 1.2,     # 承受更多伤害
    },
    "坚守": {
        "description": "以逸待劳，消耗敌军",
        "win_rate_mod": +0.05,
        "morale_mod": +3,
        "stamina_mod": -3,
        "damage_mod": 0.7,
        "risk_mod": 0.6,     # 承受较少伤害
    },
    "撤退": {
        "description": "保存实力，争取脱离",
        "win_rate_mod": -0.15,
        "morale_mod": -10,
        "stamina_mod": -8,
        "damage_mod": 0.4,
        "risk_mod": 1.5,
        "special": "can_flee",  # 可以选择撤退成功脱离
    },
    "用计": {
        "description": "施计取胜，智取敌军",
        "win_rate_mod": +0.20,
        "morale_mod": 0,
        "stamina_mod": -8,
        "damage_mod": 1.5,
        "risk_mod": 0.5,
        "requires_intel": 55,
    },
}


class CombatSession:
    """一次完整的战斗会话"""

    def __init__(self, attacker, defender, ctx):
        self.attacker = attacker
        self.defender = defender
        self.ctx = ctx
        self.round_results = []
        self.narrative_log = []
        self.winner = None
        self.loser = None
        self.attacker_damage = 0
        self.defender_damage = 0
        self.fled = False
        self.used_action = None

    def add_narrative(self, text):
        self.narrative_log.append(text)

    def simulate(self, player_action=None, active_skill=None):
        """执行战斗模拟，返回结果"""
        # ===== 主动技能效果 =====
        skill_damage_mod = 1.0
        skill_crit_bonus = 0
        skill_risk_mod = 1.0
        skill_winrate_mod = 0.0
        skill_morale_mod = 0

        if active_skill:
            if active_skill == "sneak_attack":
                # 暗箭：必定暴击
                skill_crit_bonus = 100  # 100%额外暴击率
            elif active_skill == "feint":
                # 佯攻：-10%胜率，但必定先手（已通过先攻逻辑处理）
                skill_winrate_mod = -0.10
            elif active_skill == "rally_cry":
                # 呐喊：己方士气+15
                skill_morale_mod = 15
                self.ctx["attacker_morale"] = min(100, self.ctx.get("attacker_morale", 100) + 15)
            elif active_skill == "counter_stance":
                # 反制：承受伤害-30%
                skill_risk_mod = 0.7
            elif active_skill == "decisive_strike":
                # 绝技：伤害x1.5，暴击率+20%
                skill_damage_mod = 1.5
                skill_crit_bonus = 20
            elif active_skill == "reckless_charge":
                # 破釜沉舟：伤害x2，承受伤害x1.5
                skill_damage_mod = 2.0
                skill_risk_mod = 1.5
            elif active_skill == "dragon_valor":
                # 龙胆：HP>50时武力+15（通过get_effective_stat处理，不在这里做额外操作）
                pass

        action_info = self._get_action_info(player_action)
        atk_power = self._calc_power(self.attacker, side="attacker")
        def_power = self._calc_power(self.defender, side="defender")

        # 基础胜率
        power_diff = atk_power - def_power
        base_win_rate = 0.5 + (power_diff / 200)
        base_win_rate = max(0.05, min(0.95, base_win_rate))

        # 动作修正
        win_rate = base_win_rate + action_info.get("win_rate_mod", 0) + skill_winrate_mod
        win_rate = max(0.05, min(0.95, win_rate))

        # ============ 掷骰子 ============
        dice = random.randint(1, 100)
        luck_mod = (self.attacker.get_stat("运") - 50) / 200  # ±0.25 based on luck
        effective_roll = dice / 100 + luck_mod

        # 暴击判定
        # 条件：骰出100，或 (骰出95+减暴击惩罚 且 攻击方运气>80)
        # 特殊：skill_crit_bonus >= 100 时（暗箭），视为"必定暴击"，无运门槛
        if skill_crit_bonus >= 100:
            # 暗箭必定暴击：阈值降到-5以下，此时恒为True（暴击）
            is_crit = dice >= (95 - skill_crit_bonus)  # dice >= -5 恒为True
            is_fumble = dice == 1 or (dice <= 5 and self.defender.get_stat("运") > 80)
        else:
            is_crit = dice == 100 or (dice >= (95 - skill_crit_bonus) and self.attacker.get_stat("运") > 80)
            is_fumble = dice == 1 or (dice <= 5 and self.defender.get_stat("运") > 80)

        # 胜负判定
        player_won = effective_roll <= win_rate

        # 撤退检查
        fled = False
        if player_action == "撤退" and not player_won:
            flee_chance = 0.35 + action_info.get("win_rate_mod", 0)
            if random.random() < flee_chance:
                fled = True

        self.fled = fled

        # ============ 计算伤亡 ============
        damage_mod = action_info.get("damage_mod", 1.0)
        risk_mod = action_info.get("risk_mod", 1.0)

        atk_troops = self.ctx.get("attacker_troops", 100)
        def_troops = self.ctx.get("defender_troops", 100)

        if fled:
            # 撤退：少量伤亡
            self.attacker_damage = int(atk_troops * 0.1)
            self.defender_damage = int(def_troops * 0.05)
        elif player_won:
            crit_mult = 2.0 if is_crit else 1.0
            # DEBUG
            # print(f"[DEBUG] dice={dice} is_crit={is_crit} crit_mult={crit_mult} skill_damage_mod={skill_damage_mod}")
            self.defender_damage = int(def_troops * (0.20 + random.random() * 0.15) * damage_mod * skill_damage_mod * crit_mult)
            self.attacker_damage = int(atk_troops * (0.05 + random.random() * 0.08) * risk_mod * skill_risk_mod)
        else:
            crit_mult = 2.0 if is_crit else 1.0
            self.attacker_damage = int(atk_troops * (0.20 + random.random() * 0.20) * risk_mod * skill_risk_mod)
            self.defender_damage = int(def_troops * (0.08 + random.random() * 0.10) * damage_mod * skill_damage_mod * crit_mult)

        self.winner = self.attacker if player_won else self.defender
        self.loser = self.defender if player_won else self.attacker

        # ============ 生成叙事 ============
        self._generate_narrative(player_action, action_info, dice, is_crit, is_fumble, player_won, fled)

        return self

    def _get_action_info(self, action):
        if action and action in COMBAT_ACTIONS:
            info = dict(COMBAT_ACTIONS[action])
            # 用计需要检查智谋
            if action == "用计" and self.attacker.get_stat("智") < info.get("requires_intel", 55):
                info["win_rate_mod"] -= 0.15
            return info
        return {"win_rate_mod": 0, "damage_mod": 1.0, "risk_mod": 1.0}

    def _calc_power(self, char, side):
        ctx = self.ctx
        atk_tech = char.get_stat("武")
        atk_intel = char.get_stat("智")

        base = atk_tech * 1.2 + atk_intel * 0.7

        troops_key = f"{side}_troops"
        troops = ctx.get(troops_key, 100)
        troop_factor = min(1.6, 0.4 + troops / 150)

        morale_key = f"{side}_morale"
        morale = ctx.get(morale_key, 100)
        morale_factor = 0.4 + (morale / 100) * 0.6

        terrain = ctx.get("terrain", "平原")
        terrain_map = {
            "平原": 0,
            "山地": 0.1,
            "山林": 0.15 if atk_intel > 60 else -0.05,
            "河流": -0.1,
            "关隘": 0.2,
            "水域": -0.1,
            "荒漠": -0.1,
        }
        terrain_bonus = terrain_map.get(terrain, 0)

        weather = ctx.get("weather", "晴")
        weather_map = {
            "晴": 0,
            "大雨": -0.15,
            "大风": 0.1 if "火攻" in char.skills else -0.1,
            "大雾": -0.15,
            "雪": -0.1,
        }
        weather_bonus = weather_map.get(weather, 0)

        # 伤势惩罚
        if "重伤" in char.effects:
            base *= 0.4
        elif "负伤" in char.effects:
            base *= 0.7

        power = base * troop_factor * morale_factor * (1 + terrain_bonus + weather_bonus)
        return power

    def _generate_narrative(self, action, action_info, dice, is_crit, is_fumble, player_won, fled):
        atk = self.attacker
        def_ = self.defender
        loc = self.ctx.get("location", "旷野")
        terrain = self.ctx.get("terrain", "平原")
        weather = self.ctx.get("weather", "晴")

        # ========== 开场 ==========
        self._narrate_opening(atk, def_, loc, terrain, weather)

        # ========== 动作表态 ==========
        if action and action in COMBAT_ACTIONS:
            desc = action_info.get("description", "")
            self.add_narrative(f"你下令：「{desc}！」")
            if action == "用计" and atk.get_stat("智") >= 55:
                self.add_narrative("你仔细观察敌军阵型，寻找破绽……")
            elif action == "进攻":
                self.add_narrative("全军呐喊，奋勇冲杀！")
            elif action == "坚守":
                self.add_narrative("弓弩手列阵，箭矢上弦，严阵以待。")
            elif action == "撤退":
                self.add_narrative("你传令且战且退，寻找脱身机会……")

        # ========== 关键骰子时刻 ==========
        if is_crit:
            self.add_narrative(f"【天佑！】骰出100！命运站在你这边！")
        elif is_fumble:
            self.add_narrative(f"【大凶！】骰出1！战局急转直下！")

        # ========== 战斗主体叙事 ==========
        if fled:
            self._narrate_flee(atk, def_)
        elif player_won:
            self._narrate_victory(atk, def_, is_crit)
        else:
            self._narrate_defeat(atk, def_, is_fumble)

        # ========== 战果结算 ==========
        self._narrate_result()

    def _narrate_opening(self, atk, def_, loc, terrain, weather):
        """开场叙事"""
        weather_desc = {
            "晴": "艳阳高照，",
            "大雨": "大雨倾盆，",
            "大风": "狂风大作，",
            "大雾": "大雾弥漫，",
            "雪": "大雪纷飞，",
        }.get(weather, "")

        terrain_intro = {
            "平原": f"{weather_desc}两军在{loc}相遇，",
            "山地": f"{weather_desc}两军于{loc}山地相遇，",
            "山林": f"{weather_desc}山林之中，{atk.name}与{def_.name}狭路相逢，",
            "河流": f"{weather_desc}河流两岸，{atk.name}引军渡河，",
            "关隘": f"{weather_desc}{loc}关隘之前，{atk.name}军旗鼓林立，",
            "水域": f"{weather_desc}两军隔江对峙，{atk.name}军战船列阵，",
        }.get(terrain, f"{weather_desc}两军相遇于{loc}，")

        self.add_narrative(terrain_intro + "战鼓擂动，硝烟弥漫。")
        self.add_narrative(f"{atk.name}率部列阵，{def_.name}引军迎战。")

    def _narrate_flee(self, atk, def_):
        """撤退成功叙事"""
        self.add_narrative(f"你率残部且战且退，{def_.name}紧追不舍。")
        self.add_narrative(f"危急时刻，你领数骑绕小路逃脱，{def_.name}追之不及。")
        self.add_narrative("所部散亡大半，但主力得以保全。")

    def _narrate_victory(self, atk, def_, is_crit):
        """胜利叙事"""
        self.add_narrative(f"{atk.name}率军奋勇冲杀，{def_.name}军渐渐不支！")

        if is_crit:
            self.add_narrative(f"你匹马当先，冲入敌阵，{def_.name}措手不及！")
            self.add_narrative(f"一刀挥下，{def_.name}首级滚落马前！")
            self.add_narrative("三军振奋，敌军溃散！")
        else:
            # 根据差额决定叙事风格
            dmg_ratio = self.defender_damage / max(1, self.attacker_damage)
            if dmg_ratio > 3.0:
                self.add_narrative(f"你军攻势如潮，{def_.name}军大败亏输！")
                self.add_narrative(f"战场上尸横遍野，{def_.name}匹马逃窜。")
            elif dmg_ratio > 1.5:
                self.add_narrative(f"{atk.name}亲率精兵冲阵，{def_.name}军阵脚大乱。")
                self.add_narrative(f"鏖战之后，{def_.name}支持不住，引残兵溃逃。")
            else:
                self.add_narrative(f"双方激战良久，{def_.name}军终于力竭退兵。")
                self.add_narrative(f"{atk.name}整军追击，斩杀无数。")

    def _narrate_defeat(self, atk, def_, is_fumble):
        """战败叙事"""
        self.add_narrative(f"{def_.name}军攻势猛烈，{atk.name}军渐渐不支！")

        if is_fumble:
            self.add_narrative("战局突变，{0}陷入重围！".format(atk.name))
            self.add_narrative(f"你身中数创，勉强突围而出，残部四散。")
        else:
            dmg_ratio = self.attacker_damage / max(1, self.defender_damage)
            if dmg_ratio > 3.0:
                self.add_narrative("全军溃败，不可收拾！")
                self.add_narrative(f"{def_.name}率军掩杀，{atk.name}所部折损大半。")
            elif dmg_ratio > 1.5:
                self.add_narrative(f"{def_.name}军势大，你军节节败退。")
                self.add_narrative(f"终因寡不敌众，{atk.name}军被迫撤退。")
            else:
                self.add_narrative("激战之后，{0}军因兵力悬殊而退。".format(atk.name))
                self.add_narrative(f"{atk.name}鸣金收兵，折损部分兵马。")

    def _narrate_result(self):
        """战果结算叙事"""
        atk_troops = self.ctx.get("attacker_troops", 100)
        def_troops = self.ctx.get("defender_troops", 100)

        self.add_narrative(f"\n━━━ 战斗结果 ━━━")
        if self.fled:
            self.add_narrative("结果：撤退成功（损失少量兵力）")
            self.add_narrative(f"我军伤亡：{get_number_desc(self.attacker_damage)}")
            self.add_narrative(f"敌军伤亡：{get_number_desc(self.defender_damage)}")
        elif self.winner == self.attacker:
            self.add_narrative("结果：大胜！")
            self.add_narrative(f"敌军伤亡：{get_number_desc(self.defender_damage)} / 原有{def_troops}")
            self.add_narrative(f"我军伤亡：{get_number_desc(self.attacker_damage)} / 原有{atk_troops}")
        else:
            self.add_narrative("结果：败北")
            self.add_narrative(f"我军伤亡：{get_number_desc(self.attacker_damage)} / 原有{atk_troops}")
            self.add_narrative(f"敌军伤亡：{get_number_desc(self.defender_damage)}")

        self.add_narrative("━" * 20)

    def get_full_narrative(self):
        return "\n".join(self.narrative_log)

    def get_cost(self, action):
        """获取动作消耗"""
        if action in COMBAT_ACTIONS:
            return {
                "morale": COMBAT_ACTIONS[action].get("morale_mod", 0),
                "stamina": COMBAT_ACTIONS[action].get("stamina_mod", 0),
            }
        return {}

    def can_use_action(self, action):
        if action == "用计" and self.attacker.get_stat("智") < 55:
            return False
        return True

    def get_available_actions(self):
        actions = ["进攻", "坚守", "撤退"]
        if self.attacker.get_stat("智") >= 55:
            actions.append("用计")
        return actions


def start_combat(player, enemy, ctx):
    """
    启动一次战斗会话
    ctx: dict — {
        "attacker_troops": int,
        "defender_troops": int,
        "terrain": str,
        "weather": str,
        "location": str,
        "attacker_morale": int,
        "defender_morale": int,
    }
    """
    session = CombatSession(player, enemy, ctx)
    return session


def format_combat_intro(enemy, ctx, usable_skills=None):
    """格式化战斗开始提示"""
    loc = ctx.get("location", "某地")
    terrain = ctx.get("terrain", "平原")
    troops = ctx.get("attacker_troops", 100)

    intel = enemy.get_stat("智")
    actions = [
        f"  1. 进攻 — 全力出击（+12%胜率，消耗体力{COMBAT_ACTIONS['进攻']['stamina_mod']}）",
        f"  2. 坚守 — 以逸待劳（+5%胜率，消耗体力{COMBAT_ACTIONS['坚守']['stamina_mod']}）",
        f"  3. 撤退 — 保存实力（-15%胜率，可逃，消耗体力{COMBAT_ACTIONS['撤退']['stamina_mod']}）",
    ]
    if intel >= 55:
        actions.append(f"  4. 用计 — 施计取胜（+20%胜率，消耗体力{COMBAT_ACTIONS['用计']['stamina_mod']}，需智谋≥55）")

    skill_section = ""
    if usable_skills:
        skill_lines = []
        for sid, sk in usable_skills:
            stat_str = ", ".join(f"{s}{r}" for s, r in (sk.stat_req or {}).items())
            skill_lines.append(f"  [{sid.upper()}] {sk.name} — {sk.desc}")
        if skill_lines:
            skill_section = "\n" + "\n".join(["【主动技能】（可选用字母键使用）"] + skill_lines)

    return f"""
{'━'*30}
⚔️ 遭遇战斗！
{'-'*30}
敌军：{enemy.name}（{enemy.rank}），率军与我相遇于{loc}
地形：{terrain} | 我军兵力：{troops}
{'━'*30}

请选择战术：
{chr(10).join(actions)}{skill_section}
"""