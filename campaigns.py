"""
Campaign System - 战役系统
Three major historical campaigns that span multiple months.
"""
from config import RANK_ORDER


class Campaign:
    """Defines a historical campaign."""
    def __init__(self, id, name, year, month, duration,
                 description, rewards, condition_fn=None,
                 combat_intro=None, side_choice=False,
                 reward_type="equipment"):
        self.id = id
        self.name = name           # e.g. "讨董战役"
        self.year = year           # Trigger year
        self.month = month         # Trigger month
        self.duration = duration   # months (ticks)
        self.description = description
        self.rewards = rewards     # list of reward dicts
        self.condition_fn = condition_fn  # fn(engine.state) -> bool
        self.combat_intro = combat_intro or f"战役紧迫，敌军来犯！"
        self.side_choice = side_choice  # whether player must pick a side
        self.reward_type = reward_type  # "equipment" or "skill"


# ── Reward definitions ──────────────────────────────────────────────────────────

REWARD_SHANGJIANG_SWORD = {
    "type": "equipment",
    "id": "shangjiang_sword",
    "name": "上将之剑",
    "stats": {"武": 15},
    "desc": "上将之剑，武力+15",
}
REWARD_BINGFA_TAOLUE = {
    "type": "skill",
    "id": "bingfa_taolue",
    "name": "兵法韬略",
    "skill_id": "bingfa_taolue",
    "desc": "被动技能，战斗经验获取+20%",
}
REWARD_FIRE_STRATEGY = {
    "type": "skill",
    "id": "huogong zhiji",
    "name": "火攻之计",
    "skill_id": "fire_strategy",
    "desc": "主动技能，对敌军施加「火攻」状态",
}
REWARD_KUROUJI = {
    "type": "skill",
    "id": "kurouji",
    "name": "苦肉计",
    "skill_id": "kurou_ji",
    "desc": "主动技能，牺牲自身HP换取敌军大混乱",
}


# ── Condition helpers ──────────────────────────────────────────────────────────

def has_rank_曲长_or_above(state):
    rank_idx = RANK_ORDER.index(state.player.rank)
    return rank_idx >= RANK_ORDER.index("曲长")

def has_joined_faction(state):
    """Player has any relation with Liu Bei, Cao Cao, or Sun Quan."""
    faction_npcs = ["刘备", "曹操", "孙权"]
    for name in faction_npcs:
        if state.player.get_relation(name) > 0:
            return True
    return False

def reached_year_220(state):
    return state.year >= 220


# ── Campaign definitions ───────────────────────────────────────────────────────

CAMPAIGNS = [
    Campaign(
        id="taodong",
        name="讨董战役",
        year=189,
        month=1,
        duration=3,
        description=(
            "董卓乱政，天下诸侯共讨之！你已身为曲长或以上军官，"
            "被编入讨董联军。战役期间所有战斗获取2倍经验，但粮草消耗翻倍。"
            "坚持三个月可获特殊奖励。"
        ),
        rewards=[REWARD_SHANGJIANG_SWORD, REWARD_BINGFA_TAOLUE],
        condition_fn=has_rank_曲长_or_above,
        combat_intro="董卓军铁骑逼近，诸侯联军严阵以待！",
        side_choice=False,
        reward_type="equipment",
    ),
    Campaign(
        id="chibi",
        name="赤壁战役",
        year=208,
        month=1,
        duration=4,
        description=(
            "曹操率八十万大军南下，江东危急！你已归附某一阵营，"
            "赤壁之战迫在眉睫。你必须选择：联吴抗曹，还是联曹灭吴？"
            "选择将决定你在此战中的命运，以及谁能成为你的盟友。"
        ),
        rewards=[REWARD_FIRE_STRATEGY, REWARD_KUROUJI],
        condition_fn=has_joined_faction,
        combat_intro="曹军战舰连绵，烟火蔽江！",
        side_choice=True,
        reward_type="skill",
    ),
    Campaign(
        id="sanguo",
        name="三国鼎立",
        year=220,
        month=1,
        duration=2,
        description=(
            "天下三分，尘埃落定。你的实力与阵营将决定最终的结局："
            "一统天下、归隐山林，还是身死乱军？"
            "最终之战，胜者为王。"
        ),
        rewards=[],
        condition_fn=reached_year_220,
        combat_intro="乱军之中，生死一战！",
        side_choice=False,
        reward_type="equipment",
    ),
]


def get_campaign_by_id(campaign_id):
    for c in CAMPAIGNS:
        if c.id == campaign_id:
            return c
    return None


def check_campaign_trigger(state):
    """Check if any campaign should trigger this tick. Returns Campaign or None."""
    for c in CAMPAIGNS:
        if c.year == state.year and c.month == state.month:
            if c.condition_fn and not c.condition_fn(state):
                continue
            # Check not already completed/skiped
            flag = f"campaign_{c.id}_resolved"
            if state.event_flags.get(flag):
                continue
            return c
    return None