"""
Historical Choice Events - 历史事件分支
These pause the game and ask the player to choose between two options.
"""
from config import RANK_ORDER


class ChoiceEvent:
    """A branching historical event requiring a player decision."""
    def __init__(self, id, name, year, month, description,
                 options, condition_fn=None,
                 effect_fn=None):
        self.id = id
        self.name = name
        self.year = year
        self.month = month
        self.description = description
        # options: list of {"id": str, "label": str, "desc": str, "effect": fn(state)}
        self.options = options
        self.condition_fn = condition_fn or (lambda state: True)
        self.effect_fn = effect_fn  # optional extra effect

    def check_and_trigger(self, state):
        """Returns True if this event should trigger."""
        if state.year != self.year or state.month != self.month:
            return False
        if not self.condition_fn(state):
            return False
        flag = f"choice_{self.id}_resolved"
        if state.event_flags.get(flag):
            return False
        return True


def chibi_choice_condition(state):
    """赤壁选择：208年，玩家已归附吴或楚阵营，且尚未做出选择"""
    faction_npcs = ["刘备", "孙权", "吴", "楚"]
    for name in faction_npcs:
        if state.player.get_relation(name) > 0:
            return True
    return False


def guandu_choice_condition(state):
    """官渡抉择：200年，玩家名望>=80"""
    return (state.year == 200 and state.player.get_stat("名") >= 80
            and not state.event_flags.get("choice_guandu_resolved"))


def hanzhong_king_condition(state):
    """汉中王：219年，玩家官职>=偏将军"""
    try:
        rank_idx = RANK_ORDER.index(state.player.rank)
        return rank_idx >= RANK_ORDER.index("偏将军")
    except ValueError:
        return False


def apply_chibi_side(state, side):
    """Apply effect of choosing a side in 赤壁."""
    state.event_flags["chibi_side"] = side
    if side == "wu":
        state.player.modify_relation("孙权", 30)
        state.player.modify_relation("周瑜", 20)
        state.event_flags["chibi_ally"] = "wu"
    else:  # wei
        state.player.modify_relation("曹操", 30)
        state.player.modify_relation("曹仁", 20)
        state.event_flags["chibi_ally"] = "wei"


def apply_guandu_choice(state, side):
    """Apply effect of 官渡抉择."""
    state.event_flags["guandu_side"] = side
    if side == "cao":
        state.player.modify_relation("曹操", 30)
        state.event_flags["guandu_joined"] = "cao"
    else:  # yuan
        state.player.modify_relation("袁绍", 30)
        state.event_flags["guandu_joined"] = "yuan"


def apply_hanzhong_choice(state, choice):
    """Apply effect of 汉中王 choice."""
    state.event_flags["hanzhong_choice"] = choice
    if choice == "accept":
        state.player.modify_stat("名", 15)
        state.event_flags["hanzhong_king"] = True
    else:  # "rebel"
        state.player.modify_stat("名", -10)
        state.event_flags["hanzhong_king"] = False


CHOICE_EVENTS = [
    ChoiceEvent(
        id="chibi_side",
        name="赤壁抉择",
        year=208,
        month=1,
        description="赤壁之战迫在眉睫。曹操率八十万大军南下，孙权固守江东。你已归附其中一阵营，必须做出抉择：",
        options=[
            {
                "id": "wu",
                "label": "联吴抗曹",
                "desc": "与孙权、周瑜共拒曹操，合纵抗强",
                "effect": lambda s: apply_chibi_side(s, "wu"),
            },
            {
                "id": "wei",
                "label": "联曹灭吴",
                "desc": "从曹操破孙权，一统江东",
                "effect": lambda s: apply_chibi_side(s, "wei"),
            },
        ],
        condition_fn=chibi_choice_condition,
    ),
    ChoiceEvent(
        id="guandu",
        name="官渡抉择",
        year=200,
        month=1,
        description="官渡之战前夕，袁绍与曹操对峙。你已积累不小名望，两方都在拉拢你。你必须做出选择：",
        options=[
            {
                "id": "cao",
                "label": "加入曹操",
                "desc": "曹操雄才大略，值得追随",
                "effect": lambda s: apply_guandu_choice(s, "cao"),
            },
            {
                "id": "yuan",
                "label": "加入袁绍",
                "desc": "袁绍兵多将广，地广人多",
                "effect": lambda s: apply_guandu_choice(s, "yuan"),
            },
        ],
        condition_fn=guandu_choice_condition,
    ),
    ChoiceEvent(
        id="hanzhong",
        name="汉中王",
        year=219,
        month=1,
        description="刘备进位汉中王，封你为偏将军。然而，你也可自立为王，逐鹿天下。此乃关键抉择：",
        options=[
            {
                "id": "accept",
                "label": "接受汉中王封号",
                "desc": "受封为王，为刘备麾下效力",
                "effect": lambda s: apply_hanzhong_choice(s, "accept"),
            },
            {
                "id": "rebel",
                "label": "自立为王",
                "desc": "独立一方，争夺天下霸权",
                "effect": lambda s: apply_hanzhong_choice(s, "rebel"),
            },
        ],
        condition_fn=hanzhong_king_condition,
    ),
]


def get_choice_events():
    return CHOICE_EVENTS


def check_choice_events(state):
    """Check and return any triggered choice events this tick."""
    for evt in CHOICE_EVENTS:
        if evt.check_and_trigger(state):
            return evt
    return None