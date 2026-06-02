"""
随机事件模块
单挑、舌战、奇遇、凶兆
"""
import random


def trigger_random_events(state):
    """
    在tick()末尾调用，掷骰子触发随机事件
    返回事件描述列表（可能为空）
    """
    results = []

    # 正面随机事件（~25%，提升探索/社交互动收益）
    if random.random() < 0.25:
        event = _roll_positive_event(state)
        if event:
            results.append(event)

    # 负面随机事件（~10%）
    if random.random() < 0.10:
        event = _roll_negative_event(state)
        if event:
            results.append(event)

    return results


def _roll_positive_event(state):
    """掷骰子选择正面事件"""
    p = state.player
    roll = random.randint(1, 100)

    # 根据当前属性和状态决定事件类型
    # 单挑（遇武人，约40%）
    if roll <= 40:
        return _duel_event(state)
    # 舌战（遇文人，约30%）
    elif roll <= 70:
        return _debate_event(state)
    # 奇遇（好事，约30%）
    else:
        return _fortune_event(state)


def _roll_negative_event(state):
    """掷骰子选择负面事件"""
    roll = random.randint(1, 100)
    # 中毒/受伤/遇伏兵
    if roll <= 40:
        return _injury_event(state)
    elif roll <= 70:
        return _poison_event(state)
    else:
        return _ambush_event(state)


# ─────────────────────────────────────────────
# 正面事件
# ─────────────────────────────────────────────

def _duel_event(state):
    """单挑事件 — 遇武将对阵"""
    p = state.player

    # 生成一个虚构对手（根据玩家等级调整）
    duel_tiers = [
        ("无名小卒", 40, 10, 15),
        ("江湖客", 55, 16, 20),
        ("地方豪侠", 70, 24, 25),
        ("名将之姿", 85, 36, 30),
        ("虎将之才", 95, 50, 40),
    ]

    # 根据玩家武力选择对手等级
    wu = p.get_stat("武")
    if wu < 45:
        tier = duel_tiers[0]
    elif wu < 55:
        tier = duel_tiers[1]
    elif wu < 70:
        tier = duel_tiers[2]
    elif wu < 85:
        tier = duel_tiers[3]
    else:
        tier = duel_tiers[4]

    name, required_wu, reward_exp, reward_stat = tier

    # 检查是否符合遭遇条件（需要在野外/移动中）
    location = p.location
    if location in ["颍川", "洛阳", "成都", "建业", "许昌"]:
        # 城内不触发单挑
        return None

    # 对决判定：武力差 + 骰子
    power_diff = wu - required_wu
    win_rate = 0.5 + (power_diff / 100)
    win_rate = max(0.2, min(0.9, win_rate))

    dice = random.randint(1, 100)
    player_wins = (dice / 100) <= win_rate

    if player_wins:
        # 胜利奖励
        p.modify_stat("武", 2)
        p.exp += reward_exp
        p.modify_stat("名", reward_stat // 3)
        return {
            "type": "positive",
            "name": "单挑",
            "desc": (
                f"你于{location}遇见一名自称{name}的剑客。\n"
                f"他傲然拔剑：「久闻足下武艺不俗，可愿与我一战？」\n"
                f"双方交手，数十合后你渐占上风，一击将其制服。\n"
                f"「好！好功夫！」他抱拳而去，佩服不已。\n"
                f"（武力+2，经验+{reward_exp}，名望+{reward_stat//3}）"
            ),
        }
    else:
        # 平局或惜败，也有收获
        p.exp += reward_exp // 2
        p.modify_stat("武", 1)
        return {
            "type": "positive",
            "name": "单挑",
            "desc": (
                f"你于{location}遇见一名{name}，邀你比武。\n"
                f"双方激战百合，难分高下，最终握手言和。\n"
                f"「痛快！来日再战！」\n"
                f"（经验+{reward_exp//2}，武力+1）"
            ),
        }


def _debate_event(state):
    """舌战事件 — 遇谋士论战"""
    p = state.player

    debate_tiers = [
        ("寒门学子", 45, 10, 15),
        ("郡府幕僚", 60, 16, 20),
        ("名士高徒", 75, 24, 25),
        ("当世名儒", 88, 36, 30),
    ]

    zhi = p.get_stat("智")
    if zhi < 45:
        tier = debate_tiers[0]
    elif zhi < 60:
        tier = debate_tiers[1]
    elif zhi < 75:
        tier = debate_tiers[2]
    else:
        tier = debate_tiers[3]

    name, required_zhi, reward_exp, reward_stat = tier

    location = p.location
    if location in ["颍川", "洛阳", "成都", "建业", "许昌"]:
        # 城内不触发舌战（改为在酒馆触发，但酒馆尚未实现，直接排除）
        return None

    # 舌战判定
    power_diff = zhi - required_zhi
    win_rate = 0.5 + (power_diff / 100)
    win_rate = max(0.2, min(0.9, win_rate))

    dice = random.randint(1, 100)
    player_wins = (dice / 100) <= win_rate

    if player_wins:
        p.modify_stat("智", 2)
        p.exp += reward_exp
        p.modify_stat("名", reward_stat // 3)
        return {
            "type": "positive",
            "name": "舌战",
            "desc": (
                f"你于{location}遇一{name}，纵论天下大事。\n"
                f"你引经据典，针砭时弊，对方渐渐词穷。\n"
                f"「佩服！足下见识不凡，他日必成大器。」\n"
                f"（智谋+2，经验+{reward_exp}，名望+{reward_stat//3}）"
            ),
        }
    else:
        p.exp += reward_exp // 2
        p.modify_stat("智", 1)
        return {
            "type": "positive",
            "name": "舌战",
            "desc": (
                f"你于{location}遇一{name}，共论天下大势。\n"
                f"对方见识广博，你一时难以反驳，交谈之下亦有所得。\n"
                f"「愿日后请教。」\n"
                f"（经验+{reward_exp//2}，智谋+1）"
            ),
        }


def _fortune_event(state):
    """奇遇事件 — 随机好事"""
    p = state.player
    location = p.location

    fortunes = [
        {
            "name": "山洞奇遇",
            "desc": (
                f"你于{location}附近山中迷路，误入一隐秘山洞。\n"
                f"洞中竟藏有前朝名将留下的兵法残卷，图文并茂。\n"
                f"你研读数日后，武艺有所精进。\n"
                f"（武力+3，获得经验+{50}）"
            ),
            "stat_gain": {"武": 3},
            "exp_gain": 50,
        },
        {
            "name": "老人授艺",
            "desc": (
                f"你于{location}遇见一白发老人，仙风道骨。\n"
                f"他见你根骨不凡，传授一套内功心法。\n"
                f"「此法可养气凝神，望善加修练。」\n"
                f"（武力+1，智谋+2，获得经验+{35}）"
            ),
            "stat_gain": {"武": 1, "智": 2},
            "exp_gain": 35,
        },
        {
            "name": "古墓秘笈",
            "desc": (
                f"你在{location}郊外发现一座古墓，墓中藏有古籍。\n"
                f"卷中所载皆为兵法要略，你通读之下茅塞顿开。\n"
                f"（智谋+3，获得经验+{55}）"
            ),
            "stat_gain": {"智": 3},
            "exp_gain": 55,
        },
        {
            "name": "老兵赠甲",
            "desc": (
                f"你于{location}遇一退役老兵，他见你气度不凡。\n"
                f"「我观足下乃成大事之人，此甲追随我二十年，今赠予你。」\n"
                f"（名望+5，获得经验+{25}）"
            ),
            "stat_gain": {"名": 5},
            "exp_gain": 25,
        },
        {
            "name": "路遇商队",
            "desc": (
                f"你于{location}遇一富商商队，商队遭劫后货物散落。\n"
                f"商人感激你的帮助，赠你黄金二十两。\n"
                f"（金+20，名望+2）"
            ),
            "stat_gain": {"名": 2},
            "exp_gain": 5,
            "gold_gain": 20,
        },
        {
            "name": "名师指点",
            "desc": (
                f"你在{location}偶遇一位隐世高人，他看出你武艺中的破绽。\n"
                f"「你的招式刚猛，但后劲不足，需以内力辅之。」\n"
                f"他指点一番，你受益匪浅。\n"
                f"（武力+2，智谋+1，获得经验+{40}）"
            ),
            "stat_gain": {"武": 2, "智": 1},
            "exp_gain": 40,
        },
    ]

    fortune = random.choice(fortunes)

    # 应用效果
    for stat, amount in fortune.get("stat_gain", {}).items():
        p.modify_stat(stat, amount)
    if "exp_gain" in fortune:
        p.exp += fortune["exp_gain"]
    if "gold_gain" in fortune:
        p.gold += fortune["gold_gain"]

    fortune["desc"] = fortune["desc"].replace("{location}", location)
    return {"type": "positive", "name": fortune["name"], "desc": fortune["desc"]}


# ─────────────────────────────────────────────
# 负面事件
# ─────────────────────────────────────────────

def _injury_event(state):
    """受伤事件"""
    p = state.player
    if "负伤" in p.effects:
        return None  # 已经负伤了不重复

    location = p.location
    p.take_damage(random.randint(10, 20))
    p.add_effect("负伤")
    p.morale = max(10, p.morale - 5)
    return {
        "type": "negative",
        "name": "负伤",
        "desc": (
            f"你于{location}行走时遭遇不明埋伏，激战后负伤。\n"
            f"伤口血流不止，你需要休养一段时间。\n"
            f"（HP-10~20，获得「负伤」状态）"
        ),
    }


def _poison_event(state):
    """中毒事件"""
    p = state.player
    if "中毒" in p.effects:
        return None

    location = p.location
    p.take_damage(random.randint(5, 15))
    p.add_effect("中毒")
    p.morale = max(10, p.morale - 3)
    return {
        "type": "negative",
        "name": "中毒",
        "desc": (
            f"你于{location}食用了不洁之物，中毒倒地。\n"
            f"幸好路人相救，但余毒仍需数日才能排清。\n"
            f"（HP-5~15，获得「中毒」状态）"
        ),
    }


def _ambush_event(state):
    """遇伏兵事件"""
    p = state.player

    # 逃跑判定
    wu = p.get_stat("武")
    flee_rate = 0.4 + (wu - 50) / 200
    dice = random.randint(1, 100)
    escaped = (dice / 100) <= flee_rate

    if escaped:
        p.morale = max(10, p.morale - 3)
        p.exp += 10  # 紧张逃亡也有经验
        return {
            "type": "negative",
            "name": "伏兵",
            "desc": (
                f"你于{p.location}附近山林中中了伏兵！\n"
                f"幸而你反应敏捷，趁乱逃脱，未受重伤。\n"
                f"（士气-3，经验+10）"
            ),
        }
    else:
        dmg = random.randint(15, 30)
        p.take_damage(dmg)
        p.morale = max(10, p.morale - 8)
        return {
            "type": "negative",
            "name": "伏兵",
            "desc": (
                f"你于{p.location}附近山林中中了伏兵！\n"
                f"敌军四面埋伏，你拼死杀出重围，身上多处负伤。\n"
                f"（HP-{dmg}，士气-8）"
            ),
        }