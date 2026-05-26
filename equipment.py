"""
Equipment System - 装备掉落与装备定义
"""
import random


# ── Equipment Definitions ──────────────────────────────────────────────────────
# tier: 普通(common) / 精良(fine) / 史诗(epic) / 传奇(legendary)

EQUIPMENT_POOL = [
    # ═══════════════ 普通 (Common) ═══════════════
    {
        "id": "duangong",
        "name": "短弓",
        "type": "weapon",
        "tier": "普通",
        "stats": {"武": 3},
        "bonuses": {},
        "desc": "武力+3",
    },
    {
        "id": "buyi",
        "name": "布衣",
        "type": "armor",
        "tier": "普通",
        "stats": {"防": 2},
        "bonuses": {},
        "desc": "防御+2",
    },
    {
        "id": "caoxie",
        "name": "草鞋",
        "type": "accessory",
        "tier": "普通",
        "stats": {"体力": 3},
        "bonuses": {},
        "desc": "体力+3",
    },
    {
        "id": "tongjian",
        "name": "铜剑",
        "type": "weapon",
        "tier": "普通",
        "stats": {"武": 5},
        "bonuses": {},
        "desc": "武力+5",
    },
    {
        "id": "pijia",
        "name": "皮甲",
        "type": "armor",
        "tier": "普通",
        "stats": {"防": 3},
        "bonuses": {},
        "desc": "防御+3",
    },
    {
        "id": "ganliangdai",
        "name": "干粮袋",
        "type": "accessory",
        "tier": "普通",
        "stats": {"粮": 10},
        "bonuses": {},
        "desc": "粮+10",
    },
    {
        "id": "ditucanpian",
        "name": "地图残片",
        "type": "book",
        "tier": "普通",
        "stats": {"智": 3},
        "bonuses": {"intel_cost_reduction": 5},
        "desc": "智谋+3，用计费用-5金",
    },
    {
        "id": "pinganfu",
        "name": "平安符",
        "type": "accessory",
        "tier": "普通",
        "stats": {"HP": 10},
        "bonuses": {},
        "desc": "HP上限+10",
    },
    {
        "id": "junqi",
        "name": "军旗",
        "type": "banner",
        "tier": "普通",
        "stats": {"名": 3},
        "bonuses": {},
        "desc": "名望+3",
    },
    {
        "id": "zhuzhang",
        "name": "竹杖",
        "type": "accessory",
        "tier": "普通",
        "stats": {"体力": 2},
        "bonuses": {"stamina_regen": 1},
        "desc": "体力+2，体力恢复+1/回合",
    },

    # ═══════════════ 精良 (Fine) ═══════════════
    {
        "id": "jingtiejian",
        "name": "精铁剑",
        "type": "weapon",
        "tier": "精良",
        "stats": {"武": 10},
        "bonuses": {"crit_rate": 0.03},
        "desc": "武力+10，暴击率+3%",
    },
    {
        "id": "jingjipijia",
        "name": "精制皮甲",
        "type": "armor",
        "tier": "精良",
        "stats": {"防": 5},
        "bonuses": {},
        "desc": "防御+5",
    },
    {
        "id": "kuaima",
        "name": "快马",
        "type": "mount",
        "tier": "精良",
        "stats": {},
        "bonuses": {"move_cost_reduction": 2},
        "desc": "移动金消耗-2",
    },
    {
        "id": "yishu",
        "name": "医书",
        "type": "book",
        "tier": "精良",
        "stats": {"HP": 25},
        "bonuses": {},
        "desc": "HP上限+25",
    },
    {
        "id": "bingfarumen",
        "name": "兵法入门",
        "type": "book",
        "tier": "精良",
        "stats": {"智": 8},
        "bonuses": {},
        "desc": "智谋+8",
    },
    {
        "id": "meijiu",
        "name": "美酒",
        "type": "accessory",
        "tier": "精良",
        "stats": {"魅": 8},
        "bonuses": {},
        "desc": "魅力+8",
    },
    {
        "id": "yinliang",
        "name": "银两",
        "type": "accessory",
        "tier": "精良",
        "stats": {"金": 30},
        "bonuses": {},
        "desc": "金币+30",
    },
    {
        "id": "jianrenhuanwan",
        "name": "坚韧护腕",
        "type": "accessory",
        "tier": "精良",
        "stats": {"防": 2},
        "bonuses": {"hp_low_defense": 5},
        "desc": "防御+2，HP≤5时防御+5",
    },

    # ═══════════════ 史诗 (Epic) ═══════════════
    {
        "id": "wuliling",
        "name": "武力令",
        "type": "weapon",
        "tier": "史诗",
        "stats": {"武": 15},
        "bonuses": {"crit_rate": 0.05},
        "desc": "武力+15，暴击率+5%",
    },
    {
        "id": "zhimoufu",
        "name": "智谋符",
        "type": "accessory",
        "tier": "史诗",
        "stats": {"智": 15},
        "bonuses": {"strategy_rate": 0.10},
        "desc": "智谋+15，计策成功率+10%",
    },
    {
        "id": "mingwangqi",
        "name": "名望旗",
        "type": "banner",
        "tier": "史诗",
        "stats": {"名": 15},
        "bonuses": {"npc_recruit_rate": 0.15},
        "desc": "名望+15，NPC招募率+15%",
    },
    {
        "id": "chituma",
        "name": "赤兔马",
        "type": "mount",
        "tier": "史诗",
        "stats": {},
        "bonuses": {"move_cost_reduction": 1, "stamina_regen": 8},
        "desc": "移动消耗-1金，体力+8/回合",
    },
    {
        "id": "sunzibingfa",
        "name": "孙子兵法",
        "type": "book",
        "tier": "史诗",
        "stats": {"智": 18, "名": 12},
        "bonuses": {},
        "desc": "智谋+18，名望+12",
    },

    # ═══════════════ 传奇 (Legendary) ═══════════════
    {
        "id": "qinglongyanyue",
        "name": "青龙偃月刀",
        "type": "weapon",
        "tier": "传奇",
        "stats": {"武": 25},
        "bonuses": {"battle_damage": 0.20},
        "desc": "武力+25，战斗伤害+20%",
    },
    {
        "id": "fangtianhuaji",
        "name": "方天画戟",
        "type": "weapon",
        "tier": "传奇",
        "stats": {"武": 28},
        "bonuses": {"crit_rate": 0.10},
        "desc": "武力+28，暴击率+10%",
    },
    {
        "id": "qixingdeng",
        "name": "七星灯",
        "type": "accessory",
        "tier": "传奇",
        "stats": {"HP": 50},
        "bonuses": {"death_immunity": True},
        "desc": "HP上限+50，死亡时HP=1并免疫一次",
    },
]

EQUIPMENT_BY_ID = {e["id"]: e for e in EQUIPMENT_POOL}
EQUIPMENT_SLOTS = 3
DROP_CHANCE = 0.20

# Tier order for display
TIER_ORDER = ["普通", "精良", "史诗", "传奇"]
# Tier color map (class names for CSS)
TIER_CLASS = {
    "普通": "equip-common",
    "精良": "equip-fine",
    "史诗": "equip-epic",
    "传奇": "equip-legendary",
}
TIER_ICON = {
    "普通": "⚪",
    "精良": "🔵",
    "史诗": "🟣",
    "传奇": "🟠",
}


def get_random_equipment(force_tier=None):
    """Return a random equipment dict, respecting tier-weighted probabilities.

    Probability table (1-100 roll):
      <=2  → 传奇 (2%)
      <=10 → 史诗 (8%)
      <=30 → 精良 (20%)
      else → 普通 (70%)
    """
    if force_tier:
        candidates = [e for e in EQUIPMENT_POOL if e["tier"] == force_tier]
        if not candidates:
            candidates = EQUIPMENT_POOL
    else:
        roll = random.randint(1, 100)
        if roll <= 2:
            tier = "传奇"
        elif roll <= 10:
            tier = "史诗"
        elif roll <= 30:
            tier = "精良"
        else:
            tier = "普通"
        candidates = [e for e in EQUIPMENT_POOL if e["tier"] == tier]

    chosen = random.choice(candidates)
    return dict(chosen)


def get_equipment_by_id(eq_id):
    return EQUIPMENT_BY_ID.get(eq_id)


def apply_equipment_stats(player):
    """
    Add equipment stat bonuses to player stats for display/combat purposes.
    Returns a dict of total stat bonuses.
    """
    bonuses = {"武": 0, "智": 0, "名": 0, "魅": 0, "运": 0,
               "防": 0, "HP": 0, "粮": 0, "金": 0,
               "crit_rate": 0.0, "strategy_rate": 0.0,
               "npc_recruit_rate": 0.0, "move_cost_reduction": 0,
               "stamina_regen": 0, "battle_damage": 0.0,
               "intel_cost_reduction": 0,
               "hp_low_defense": 0,
               "death_immunity": False}

    if not hasattr(player, 'equipment'):
        return bonuses

    for item in player.equipment:
        if not item:
            continue
        for stat, val in item.get("stats", {}).items():
            bonuses[stat] = bonuses.get(stat, 0) + val
        b = item.get("bonuses", {})
        for k, v in b.items():
            if k in bonuses and isinstance(v, float):
                bonuses[k] = bonuses.get(k, 0.0) + v
            elif k in bonuses:
                bonuses[k] = v  # boolean flags

    return bonuses


def get_equipment_display():
    """Return a formatted list of all equipment definitions grouped by tier."""
    lines = ["【装备图鉴】"]
    for tier in TIER_ORDER:
        items = [e for e in EQUIPMENT_POOL if e["tier"] == tier]
        if items:
            icon = TIER_ICON.get(tier, "⚪")
            lines.append(f"\n── {icon} {tier} ──")
            for eq in items:
                lines.append(f"  「{eq['name']}」- {eq['desc']}")
    return "\n".join(lines)