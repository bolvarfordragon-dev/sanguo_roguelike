"""
必然事件模块
按年份月份触发，记录重大历史事件
"""
from narrative import format_event_intro


# ============ 必然事件定义 ============
# 格式：(year, month): {
#     "name": str,
#     "desc": str,
#     "effect": callable(state),
#     "choices": list[dict] or None,
# }

def get_mandatory_events():
    """返回所有必然事件列表（按时间排序）"""
    return sorted(MANDATORY_EVENTS.keys(), key=lambda x: (x[0], x[1]))


MANDATORY_EVENTS = {
    # ============ 184年 黄巾之乱 ============
    (184, 1): {
        "name": "黄巾起义",
        "desc": (
            "中平元年春，钜鹿张角借宗教布道，信徒遍及八州。\n"
            "三月，张角自称天公将军，举旗反汉，天下大乱。\n"
            "州郡失守，朝野震动。汉廷急令各地募兵镇压。\n\n"
            "你身在颍川，正是黄巾之乱的核心区域之一。"
        ),
        "effect": lambda state: _effect_yellow_turbans(state),
        "player_can_act": True,
    },

    # ============ 189年 董卓进京 ============
    (189, 12): {
        "name": "董卓进京",
        "desc": (
            "初平元年十二月，董卓率凉州铁骑入京。\n"
            "废少帝而立献帝，血洗朝野，权倾天下。\n"
            "袁绍、曹操等群雄各怀心思，天下动荡。\n\n"
            "董卓军威势滔天，京城一片混乱。"
        ),
        "effect": lambda state: _effect_dong_zhuo_enters(state),
        "player_can_act": False,
    },

    # ============ 190年 群雄讨董 ============
    (190, 1): {
        "name": "群雄讨董",
        "desc": (
            "袁绍自称盟主，传檄天下，诸侯并起响应。\n"
            "十八路诸侯会盟，联军号称百万，浩浩荡荡。\n"
            "董卓挟天子以令诸侯，迁都长安，焚烧洛阳。\n\n"
            "天下大乱，正是英雄崛起之时。"
        ),
        "effect": lambda state: _effect_coalition_against_dong(state),
        "player_can_act": True,
        "choices": [
            {"id": "join_alliance", "label": "加入讨董联军", "effect": lambda s: _join_alliance(s)},
            {"id": "join_dong", "label": "投靠董卓", "effect": lambda s: _join_dong(s)},
            {"id": "stay_independent", "label": "观望待机", "effect": lambda s: _stay_independent(s)},
        ],
    },

    # ============ 190年 虎牢关之战 ============
    (190, 3): {
        "name": "虎牢关之战",
        "desc": (
            "联军进兵至虎牢关，董卓部下华雄把守关隘。\n"
            "华雄骁勇，连斩联军数将，诸侯皆不敢出战。\n"
            "关羽请战，温酒之间，斩华雄于马下。\n\n"
            "（历史事件触发关羽斩华雄）"
        ),
        "effect": lambda state: _effect_hulao_battle(state),
        "player_can_act": True,
        "condition": lambda state: state.event_flags.get("讨董联军", False) or state.global_flags.get("in_coalition", False),
    },

    # ============ 200年 官渡之战 ============
    (200, 10): {
        "name": "官渡之战",
        "desc": (
            "袁绍与曹操对峙于官渡。\n"
            "绍军七十万，曹操军不足三万，形势悬殊。\n"
            "曹操夜袭乌巢，烧毁袁绍粮草，绍军大溃。\n"
            "此战奠定曹操北方霸主地位。\n\n"
            "天下格局即将大变。"
        ),
        "effect": lambda state: _effect_guandu(state),
        "player_can_act": True,
    },

    # ============ 208年 赤壁之战 ============
    (208, 11): {
        "name": "赤壁之战",
        "desc": (
            "曹操统一北方后，率军八十三万南下荆州。\n"
            "刘备与孙权联盟，周瑜黄盖施火攻之计。\n"
            "东南风起，火船冲入曹军船阵，烈焰冲天。\n"
            "曹军大败，曹操北返，孙刘势力大涨。\n\n"
            "三国鼎立的雏形由此奠定。"
        ),
        "effect": lambda state: _effect_chibi(state),
        "player_can_act": True,
    },

    # ============ 220年 三国鼎立（结局） ============
    (220, 1): {
        "name": "曹丕篡汉 / 三国鼎立",
        "desc": (
            "曹操薨，其子曹丕继位魏王。\n"
            "逼汉献帝禅位，魏朝建立，汉朝灭亡。\n"
            "刘备随即在蜀地称帝，建立蜀汉。\n"
            "孙权在江东称帝，建立东吴。\n\n"
            "三国鼎立，天下正式分裂。"
        ),
        "effect": lambda state: _effect_three_kingdoms(state),
        "player_can_act": False,
        "is_ending": True,
        "ending_type": "three_kingdoms",
    },

    # ============ 222年 三国正式鼎立（隐藏结局前置） ============
    (222, 1): {
        "name": "夷陵之战",
        "desc": (
            "刘备为报关羽之仇，率蜀汉精锐伐吴。\n"
            "陆逊火烧连营，刘备大败，退守白帝城。\n"
            "蜀汉精锐损失殆尽，刘备病逝于白帝城。\n"
            "吴蜀联盟破裂，三国格局彻底稳定。\n\n"
            "（可选：若玩家统一天下则触发隐藏结局）"
        ),
        "effect": lambda state: _effect_yiling(state),
        "player_can_act": False,
    },
}


# ============ 事件效果函数 ============

def _effect_yellow_turbans(state):
    """黄巾起义效果"""
    state.global_flags["黄巾之乱"] = True
    state.event_flags["黄巾起义触发"] = True
    if state.player:
        state.player.exp += 20
        state.player.modify_stat("名", 5)
        state.player.inheritance_fragments += 2
        print("（获得传承碎片 +2）")


def _effect_dong_zhuo_enters(state):
    """董卓进京效果"""
    state.global_flags["董卓进京"] = True
    state.event_flags["董卓已进京"] = True
    # 京城附近NPC位置更新
    if "曹操" in state.npcs:
        state.npcs["曹操"].location = "陈留"
    if "董卓" in state.npcs:
        state.npcs["董卓"].location = "洛阳"


def _effect_coalition_against_dong(state):
    """讨董联军效果"""
    state.global_flags["讨董联军"] = True
    state.event_flags["讨董联军触发"] = True
    # 玩家可选择加入联军


def _effect_hulao_battle(state):
    """虎牢关之战效果"""
    state.global_flags["虎牢关之战"] = True
    state.event_flags["虎牢关之战触发"] = True
    # 华雄死亡
    if "华雄" in state.npcs:
        state.npcs["华雄"].hp = 0


def _effect_guandu(state):
    """官渡之战效果"""
    state.global_flags["官渡之战"] = True
    state.event_flags["官渡之战触发"] = True
    if "袁绍" in state.npcs:
        state.npcs["袁绍"].hp = 0
    if state.player:
        state.player.inheritance_fragments += 5
        print("（获得传承碎片 +5）")


def _effect_chibi(state):
    """赤壁之战效果"""
    state.global_flags["赤壁之战"] = True
    state.event_flags["赤壁之战触发"] = True
    if state.player:
        state.player.inheritance_fragments += 8
        print("（获得传承碎片 +8）")


def _effect_three_kingdoms(state):
    """三国鼎立效果（结局）"""
    state.global_flags["三国鼎立"] = True
    state.event_flags["三国鼎立触发"] = True


def _effect_yiling(state):
    """夷陵之战效果"""
    state.global_flags["夷陵之战"] = True
    if state.player:
        state.player.inheritance_fragments += 5
        print("（获得传承碎片 +5）")
    state.global_flags["夷陵之战"] = True


# ============ 辅助函数 ============

def _join_alliance(state):
    """玩家加入讨董联军"""
    state.global_flags["in_coalition"] = True
    state.player.location = "酸枣"
    state.event_flags["讨董联军"] = True


def _join_dong(state):
    """玩家投靠董卓"""
    state.global_flags["joined_dongzhou"] = True
    state.player.location = "洛阳"
    state.event_flags["投靠董卓"] = True


def _stay_independent(state):
    """玩家观望待机"""
    state.global_flags["independent"] = True


def trigger_mandatory_event(state, year, month):
    """触发指定时间的必然事件"""
    key = (year, month)
    if key not in MANDATORY_EVENTS:
        return None

    evt = MANDATORY_EVENTS[key]
    # 检查条件
    if "condition" in evt and not evt["condition"](state):
        return None

    # 执行效果
    evt["effect"](state)

    return {
        "name": evt["name"],
        "desc": evt["desc"],
        "player_can_act": evt.get("player_can_act", False),
        "choices": evt.get("choices", None),
        "is_ending": evt.get("is_ending", False),
        "ending_type": evt.get("ending_type", None),
    }


def list_mandatory_events():
    """列出所有必然事件"""
    return [(k, v["name"]) for k, v in MANDATORY_EVENTS.items()]