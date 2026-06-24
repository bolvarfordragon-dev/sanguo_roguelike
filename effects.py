"""
Buff/Debuff 效果系统
定义所有状态效果及其行为
"""

# 效果定义
# id: 效果唯一ID
# name: 显示名称
# type: "buff" | "debuff"
# duration_type: "permanent" | "timed" | "combat" | "stackable"
# duration: int - 持续月数（timed类型）
# stat_mods: dict - 属性加成/减免 {"武": -5, "防": -3} 等
# combat_mods: dict - 战斗修正 {"crit_rate": +10, "win_rate": -0.1} 等
# on_apply: str - 施加时额外动作描述
# on_remove: str - 移除时描述
# desc: str - 显示描述（{turns}会被替换为剩余月数）

EFFECT_DEFINITIONS = {
    # ═══════════════ BUFFS（正面效果） ═══════════════
    "高昂": {
        "name": "高昂",
        "type": "buff",
        "duration_type": "timed",
        "default_duration": 3,
        "stat_mods": {"武": 5, "运": 3},
        "combat_mods": {"crit_rate": 5},
        "on_apply": "你士气大振，战意高昂！",
        "on_remove": "高昂的情绪渐渐平复。",
        "desc": "武力+5，气运+3，暴击率+5%（剩余{turns}月）",
    },
    "疗伤": {
        "name": "疗伤",
        "type": "buff",
        "duration_type": "timed",
        "default_duration": 4,
        "stat_mods": {},
        "combat_mods": {},
        "on_apply": "你得到妥善医治，伤势正在恢复。",
        "on_remove": "伤口已大致痊愈。",
        "desc": "每回合回复HP+5（剩余{turns}月）",
    },
    "激励": {
        "name": "激励",
        "type": "buff",
        "duration_type": "timed",
        "default_duration": 2,
        "stat_mods": {"名": 3},
        "combat_mods": {"win_rate": 0.08},
        "on_apply": "身边将士齐声高呼，为你助威！",
        "on_remove": "激励之情渐渐消散。",
        "desc": "名望+3，战斗胜率+8%（剩余{turns}月）",
    },
    "连胜": {
        "name": "连胜",
        "type": "buff",
        "duration_type": "stackable",
        "default_duration": 3,
        "stat_mods": {"武": 2, "名": 2},
        "combat_mods": {"crit_rate": 3},
        "on_apply": "连战连捷，威名远扬！",
        "on_remove": "连胜的气势不再。",
        "desc": "武力+2，名望+2，暴击率+3%（可叠加）",
    },
    "备战": {
        "name": "备战",
        "type": "buff",
        "duration_type": "timed",
        "default_duration": 2,
        "stat_mods": {},
        "combat_mods": {"first_strike": True},
        "on_apply": "你占据了有利地形，以逸待劳。",
        "on_remove": "地形优势已不再。",
        "desc": "战斗必定先手（剩余{turns}月）",
    },

    # ═══════════════ DEBUFFS（负面效果） ═══════════════
    "负伤": {
        "name": "负伤",
        "type": "debuff",
        "duration_type": "timed",
        "default_duration": 4,
        "stat_mods": {"武": -5},
        "combat_mods": {"crit_rate": -5, "win_rate": -0.05},
        "on_apply": "伤口隐隐作痛，影响发挥。",
        "on_remove": "伤势痊愈，完全恢复状态。",
        "desc": "武力-5，暴击率-5%（剩余{turns}月）",
    },
    "中毒": {
        "name": "中毒",
        "type": "debuff",
        "duration_type": "timed",
        "default_duration": 3,
        "stat_mods": {},
        "combat_mods": {},
        "on_apply": "体内毒素发作，头晕目眩。",
        "on_remove": "毒素渐渐排除，身体轻松许多。",
        "desc": "每回合HP-5（剩余{turns}月）",
    },
    "士气低落": {
        "name": "士气低落",
        "type": "debuff",
        "duration_type": "timed",
        "default_duration": 3,
        "stat_mods": {},
        "combat_mods": {"win_rate": -0.10, "morale_loss_extra": 5},
        "on_apply": "连番挫折，士气受挫。",
        "on_remove": "士气渐渐恢复。",
        "desc": "战斗胜率-10%，失败时额外-5士气（剩余{turns}月）",
    },
    # === F1.5: 战役奖励技能效果（火攻之计 / 苦肉计）===
    "火攻": {
        "name": "火攻",
        "type": "debuff",
        "duration_type": "timed",
        "default_duration": 3,
        "stat_mods": {"武": -3},
        "combat_mods": {"win_rate": -0.05, "risk": 0.5},
        "on_apply": "敌军陷入火海！",
        "on_remove": "大火渐渐熄灭。",
        "desc": "武力-3，战斗胜率-5%，承受伤害+50%（剩余{turns}月）",
    },
    "大混乱": {
        "name": "大混乱",
        "type": "debuff",
        "duration_type": "timed",
        "default_duration": 2,
        "stat_mods": {"武": -5, "智": -5},
        "combat_mods": {"win_rate": -0.20, "crit_rate": -10},
        "on_apply": "敌军阵脚大乱！",
        "on_remove": "敌军渐渐稳住阵脚。",
        "desc": "武力-5，智谋-5，战斗胜率-20%，暴击率-10%（剩余{turns}月）",
    },
    "疲惫": {
        "name": "疲惫",
        "type": "debuff",
        "duration_type": "timed",
        "default_duration": 2,
        "stat_mods": {"运": -5},
        "combat_mods": {"crit_rate": -5},
        "on_apply": "连日奔波，身心俱疲。",
        "on_remove": "经过休整，精力有所恢复。",
        "desc": "气运-5，暴击率-5%（剩余{turns}月）",
    },
    "惊惧": {
        "name": "惊惧",
        "type": "debuff",
        "duration_type": "timed",
        "default_duration": 2,
        "stat_mods": {"武": -3, "魅": -3},
        "combat_mods": {"flee_fail_chance": 0.20},
        "on_apply": "遭遇惊变，心有余悸。",
        "on_remove": "渐渐平复了恐惧之心。",
        "desc": "武力-3，魅力-3，撤退失败率+20%（剩余{turns}月）",
    },
}


def get_effect(id):
    return EFFECT_DEFINITIONS.get(id)


def format_effect_desc(effect_id, turns=None):
    """格式化效果描述"""
    eff = get_effect(effect_id)
    if not eff:
        return ""
    desc = eff.get("desc", "")
    if turns is not None and "{turns}" in desc:
        desc = desc.replace("{turns}", str(turns))
    return desc


def is_buff(effect_id):
    eff = get_effect(effect_id)
    return eff.get("type") == "buff" if eff else False


def is_debuff(effect_id):
    eff = get_effect(effect_id)
    return eff.get("type") == "debuff" if eff else False