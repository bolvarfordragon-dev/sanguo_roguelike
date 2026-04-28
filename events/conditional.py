"""
条件事件模块
满足特定条件时触发的事件（命运/随机遭遇）
"""
import random


class ConditionalEvent:
    """条件事件"""
    def __init__(self, name, condition_fn, trigger_fn, desc, rarity="normal"):
        self.name = name
        self.condition_fn = condition_fn  # callable(state) -> bool
        self.trigger_fn = trigger_fn       # callable(state) -> result dict
        self.desc = desc
        self.rarity = rarity  # "common", "normal", "rare", "legendary"

    def check_and_trigger(self, state):
        if self.condition_fn(state):
            return self.trigger_fn(state)
        return None


# ============ 条件事件工厂 ============

def meet_npc_event(npc_name, location=None):
    """生成一个遭遇NPC的条件事件"""
    def condition(state):
        npc = state.npcs.get(npc_name)
        if not npc or npc.hp <= 0:
            return False
        if location and state.player.location != location:
            return False
        # 检查是否已经遭遇过
        flag = f"遭遇_{npc_name}"
        if state.event_flags.get(flag):
            return False
        return True

    def trigger(state):
        state.event_flags[f"遭遇_{npc_name}"] = True
        npc = state.npcs[npc_name]
        # 根据好感度决定关系
        rel = state.player.get_relation(npc_name)
        if rel >= 50:
            result_text = f"你与{npc_name}再度相逢，{npc_name}对你颇为友善。"
        elif rel <= -50:
            result_text = f"{npc_name}见你，面色不善，拔剑相向。"
        else:
            result_text = f"你与{npc_name}相遇，{npc_name}打量着你，不知是敌是友。"
        return {
            "name": f"遭遇{npc_name}",
            "desc": result_text,
            "npc": npc_name,
            "type": "encounter",
        }

    return ConditionalEvent(
        name=f"遭遇{npc_name}",
        condition_fn=condition,
        trigger_fn=trigger,
        desc=f"在{location or '某地'}遇到{npc_name}",
        rarity="normal"
    )


def random_encounter_event(encounter_type, min_year=184, max_year=220):
    """随机遭遇事件"""
    def condition(state):
        if state.year < min_year or state.year > max_year:
            return False
        # 随机概率（每月5%概率）
        return random.random() < 0.05

    def trigger(state):
        loc = state.player.location
        results = {
            "流民": f"你路过{loc}，见一群流民扶老携幼，狼狈而行。",
            "山贼": f"{loc}附近山林中，一伙山贼突然杀出，拦路抢劫！",
            "散兵": f"你遇见一队散兵，盔甲破败，不知属于何方。",
            "商队": f"{loc}道上，一支商队正缓缓行来，商人谨慎地打量着你。",
            "游侠": f"你见一道人打扮的游侠，腰悬宝剑，独行于道。",
            "行脚僧": f"{loc}城外，一个行脚僧正在化缘，见你过来，口中念经。",
        }
        text = results.get(encounter_type, f"你在{loc}遭遇了不明人物。")
        return {
            "name": f"随机遭遇：{encounter_type}",
            "desc": text,
            "type": "random_encounter",
            "encounter_type": encounter_type,
            "location": loc,
        }

    return ConditionalEvent(
        name=f"随机遭遇：{encounter_type}",
        condition_fn=condition,
        trigger_fn=trigger,
        desc=f"在旅途中随机遭遇",
        rarity="common"
    )


def rank_up_event():
    """升级事件（当经验足够时）"""
    def condition(state):
        if not state.player:
            return False
        rank = state.player.rank
        idx_map = {
            "散兵": 0, "什长": 1, "伍长": 2, "队长": 3,
            "曲长": 4, "司马": 5, "校尉": 6, "中郎将": 7, "将军": 8
        }
        if rank not in idx_map:
            return False
        # 经验足够时触发（简化判断）
        exp = state.player.exp
        threshold = [0, 30, 80, 150, 280, 450, 700, 1000, 1500]
        idx = idx_map[rank]
        return exp >= threshold[idx + 1] if idx + 1 < len(threshold) else False

    def trigger(state):
        old_rank = state.player.rank
        leveled = state.player.check_level_up()
        new_rank = state.player.rank
        if leveled:
            return {
                "name": "职务升迁",
                "desc": f"你因战功卓著，职务由{old_rank}升为{new_rank}。\n全属性小幅提升。",
                "type": "rank_up",
                "old_rank": old_rank,
                "new_rank": new_rank,
            }
        return None

    return ConditionalEvent(
        name="职务升迁",
        condition_fn=condition,
        trigger_fn=trigger,
        desc="经验达到要求，职务提升",
        rarity="normal"
    )


# ============ 预设条件事件列表 ============

def get_default_conditional_events():
    """获取默认的条件事件列表"""
    events = []

    # 固定NPC遭遇事件
    for npc_name in ["关羽", "张飞", "刘备", "曹操", "孙坚", "赵云", "诸葛亮", "吕布"]:
        if npc_name in ["关羽", "张飞", "刘备"]:
            loc = "涿郡"
        elif npc_name == "曹操":
            loc = "陈留"
        elif npc_name == "孙坚":
            loc = "长沙"
        elif npc_name == "孙策":
            loc = "吴郡"
        elif npc_name == "周瑜":
            loc = "吴郡"
        elif npc_name == "赵云":
            loc = "邺城"
        elif npc_name == "诸葛亮":
            loc = "南阳"
        elif npc_name == "吕布":
            loc = "并州"
        else:
            loc = None

        events.append(meet_npc_event(npc_name, loc))

    # 随机遭遇
    for enc_type in ["流民", "山贼", "散兵", "商队", "游侠"]:
        events.append(random_encounter_event(enc_type, min_year=184, max_year=220))

    # 升级检测
    events.append(rank_up_event())

    return events


# ============ 桃园结义（特殊条件事件） ============

def taoyuan_oath_event():
    """桃园结义条件事件 — 需要刘备、关羽、张飞同时在场"""
    def condition(state):
        # 需要在涿郡 + 刘备关羽张飞都存在且存活
        if state.player.location != "涿郡":
            return False
        required = ["刘备", "关羽", "张飞"]
        for npc in required:
            if npc not in state.npcs or state.npcs[npc].hp <= 0:
                return False
        # 检查是否已经触发过
        if state.event_flags.get("桃园结义", False):
            return False
        # 检查玩家与刘备的关系
        if state.player.get_relation("刘备") < 0:
            return False
        return True

    def trigger(state):
        state.event_flags["桃园结义"] = True
        return {
            "name": "桃园结义",
            "desc": (
                "刘备、关羽、张飞相遇于涿郡。\n"
                "三人志同道合，欲共举大事。\n"
                "刘备见你亦在附近，邀你一同加入。\n\n"
                "你愿意与刘关张结为异姓兄弟吗？"
            ),
            "type": "special",
            "choices": [
                {
                    "id": "accept_oath",
                    "label": "加入桃园结义",
                    "effect": lambda s: _accept_taoyuan(s),
                },
                {
                    "id": "decline_oath",
                    "label": "婉言谢绝",
                    "effect": lambda s: _decline_taoyuan(s),
                },
            ],
        }

    return ConditionalEvent(
        name="桃园结义",
        condition_fn=condition,
        trigger_fn=trigger,
        desc="在涿郡遇刘备、关羽、张飞，有机会结为兄弟",
        rarity="legendary"
    )


def _accept_taoyuan(state):
    state.event_flags["桃园结义_已加入"] = True
    state.player.modify_relation("刘备", 50)
    state.player.modify_relation("关羽", 50)
    state.player.modify_relation("张飞", 50)
    state.player.modify_stat("名", 20)
    return {
        "result": "success",
        "text": "你与刘备、关羽、张飞于桃园中结为异姓兄弟。\n不求同年同月同日生，但愿同年同月同日死。\n你的名望大幅提升。",
    }


def _decline_taoyuan(state):
    state.event_flags["桃园结义_已拒绝"] = True
    return {
        "result": "declined",
        "text": "你婉言谢绝了刘备的邀请。\n天下英雄何其多，各有志向，不必强求。",
    }


# ============ 华容道（条件事件） ============

def huarong_road_event():
    """华容道 — 赤壁战后曹操败走"""
    def condition(state):
        if not state.event_flags.get("赤壁之战触发", False):
            return False
        if state.year != 209:
            return False
        if state.player.location not in ["江陵", "荆州", "华容道"]:
            return False
        if state.event_flags.get("华容道触发", False):
            return False
        return True

    def trigger(state):
        state.event_flags["华容道触发"] = True
        return {
            "name": "华容道",
            "desc": (
                "赤壁战后，曹操败走华容道。\n"
                "关羽率兵截击，曹操困于山谷之中。\n"
                "你恰好在附近，闻讯赶来……\n\n"
                "关羽曾受你恩惠，此刻正在犹豫。"
            ),
            "type": "special",
            "choices": [
                {
                    "id": "let曹操escape",
                    "label": "暗示关羽放行",
                    "effect": lambda s: _let_cao_escape(s),
                    "requires_relations": {"关羽": 50},
                },
                {
                    "id": "att曹操",
                    "label": "趁机截击曹操",
                    "effect": lambda s: _attack_cao(s),
                },
                {
                    "id": "watch",
                    "label": "袖手旁观",
                    "effect": lambda s: _watch_event(s),
                },
            ],
        }

    return ConditionalEvent(
        name="华容道",
        condition_fn=condition,
        trigger_fn=trigger,
        desc="赤壁战后曹操败走华容道",
        rarity="legendary"
    )


def _let_cao_escape(state):
    state.event_flags["华容道_放曹"] = True
    state.player.modify_relation("关羽", 30)
    state.player.modify_stat("名", 10)
    return {
        "result": "success",
        "text": "你向关羽使了一个眼色，关羽会意，佯装不胜，放曹操残部逃走。\n此事传开，世人皆称你义薄云天。"
    }


def _attack_cao(state):
    state.event_flags["华容道_截曹"] = True
    return {
        "result": "success",
        "text": "你率部截击曹操，曹操军疲惫不堪，无力再战。\n然而曹操终究在亲卫护送下逃脱。\n你斩获颇丰，但关羽对此颇为不满。"
    }


def _watch_event(state):
    state.event_flags["华容道_旁观"] = True
    return {
        "result": "neutral",
        "text": "你按兵不动，静观其变。\n关羽最终放走了曹操，你在一旁目睹了这一切。"
    }


# ============ 三顾茅庐（条件事件） ============

def three_visits_to_zhuge_event():
    """三顾茅庐 — 需要名望足够高才能触发"""
    def condition(state):
        if state.event_flags.get("三顾茅庐_完成", False):
            return False
        if state.event_flags.get("三顾茅庐_尝试", False) and state.event_flags.get("三顾茅庐_次数", 0) >= 3:
            return False
        if state.player.get_stat("名") < 50:
            return False
        if state.player.location not in ["南阳", "襄阳", "荆州"]:
            return False
        if "诸葛亮" not in state.npcs or state.npcs["诸葛亮"].hp <= 0:
            return False
        return True

    def trigger(state):
        visits = state.event_flags.get("三顾茅庐_次数", 0)
        visits += 1
        state.event_flags["三顾茅庐_次数"] = visits

        desc_templates = {
            1: "你来到南阳隆中，只见草堂紧闭，诸葛亮似不在家。你留下名帖，怅然而归。",
            2: "二顾茅庐，时值大雪，诸葛亮闭门不见。你在门外等候多时，只得再次离去。",
            3: "三顾茅庐，诸葛亮终于在家。他与你纵论天下大事，指出三分天下之策。\n你心悦诚服，请诸葛亮出山相助。",
        }

        if visits >= 3:
            state.event_flags["三顾茅庐_完成"] = True
            state.event_flags["诸葛亮_已加入"] = True
            state.player.modify_stat("名", 30)
            state.player.modify_relation("诸葛亮", 80)

        return {
            "name": f"三顾茅庐（第{visits}次）",
            "desc": desc_templates.get(visits, f"第{visits}次前往隆中拜访诸葛亮。"),
            "type": "special",
            "choices": None if visits >= 3 else [],
        }

    return ConditionalEvent(
        name="三顾茅庐",
        condition_fn=condition,
        trigger_fn=trigger,
        desc="名望足够时前往荆州拜访诸葛亮",
        rarity="rare"
    )