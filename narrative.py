"""
叙事文字生成模块
"""
import random


def narrate_battle_intro(attacker, defender, context=None):
    """生成战斗开场叙事"""
    templates = [
        "{attacker}引兵至，与{defender}相遇，两阵对圆，兵刃相接。",
        "{defender}引军拦住去路，{attacker}横刀跃马，直取敌将。",
        "{attacker}率部进发，行至{location}，忽见{defender}军旗鼓，列阵以待。",
    ]
    t = random.choice(templates)
    loc = context.get("location", "") if context else ""
    return t.format(
        attacker=attacker,
        defender=defender,
        location=loc
    )


def narrate_combat_round(result, context=None):
    """生成一回合战斗叙事

    result: dict — {
        "outcome": "win"/"lose"/"draw",
        "damage_dealt": int,
        "damage_taken": int,
        "key_moment": str,  # e.g. "critical", "skill_used", "desperate"
        "desc": str,  # 自定义描述
    }
    """
    if result.get("desc"):
        return result["desc"]

    outcome = result.get("outcome", "draw")
    key = result.get("key_moment", "")

    if outcome == "win":
        return _narrate_victory(result, key)
    elif outcome == "lose":
        return _narrate_defeat(result, key)
    else:
        return _narrate_draw(result, key)


def _narrate_victory(result, key_moment):
    damage = result.get("damage_dealt", 0)
    if key_moment == "critical":
        return f"刀光闪过，敌将措手不及，被斩于马下。我军大胜，斩获{get_number_desc(damage)}。"
    elif key_moment == "skill_used" and result.get("skill_name"):
        skill = result["skill_name"]
        return f"施计「{skill}」，敌军大乱，主将落马。大捷。杀敌{get_number_desc(damage)}。"
    elif key_moment == "overwhelming":
        return f"攻势如潮，敌军不能当，大败。斩首{get_number_desc(damage)}，获辎重无数。"
    else:
        return f"激战之后，敌军渐渐不支，溃败而逃。我军斩杀{get_number_desc(damage)}，缴获马匹兵甲。"


def _narrate_defeat(result, key_moment):
    damage = result.get("damage_taken", 0)
    if key_moment == "critical":
        return f"混战之中，敌军一箭射中我军主将，主将落马，军心大乱，溃败。伤亡{get_number_desc(damage)}。"
    elif key_moment == "skill_used" and result.get("skill_name"):
        skill = result["skill_name"]
        return f"敌军「{skill}」大展，我军措手不及，大败而退。折损{get_number_desc(damage)}人。"
    elif key_moment == "desperate":
        return f"力战不支，士卒散亡大半，主将身被数创，勉强脱身。伤亡{get_number_desc(damage)}。"
    else:
        return f"鏖战良久，我军力竭，敌军乘势掩杀，大败而退。损失{get_number_desc(damage)}人。"


def _narrate_draw(result, key_moment):
    d_dealt = result.get("damage_dealt", 0)
    d_taken = result.get("damage_taken", 0)
    return f"双方激战，各有伤亡。敌军退，我军亦折损{d_taken}人，斩敌{d_dealt}人。战成平局。"


def get_number_desc(n):
    """数字转中文描述"""
    if n < 10:
        return f"{n}人"
    elif n < 100:
        return f"数十人" if n < 50 else "近百人"
    elif n < 500:
        return "数百人"
    elif n < 1000:
        return "近千人"
    else:
        return f"{n // 100 * 100}+人"


def narrate_event(title, body, time_str):
    """生成事件叙事"""
    return f"\n{'='*40}\n【{title}】\n{time_str}\n\n{body}\n{'='*40}\n"


def narrate_death_report(player, cause, context=None):
    """生成死亡史书记载"""
    name = player.name
    rank = player.rank
    exp = player.exp

    death_texts = {
        "战死": f"{name}，{rank}，于阵中战死。",
        "重伤": f"{name}，{rank}，身被重创，亡于军中。",
        "被俘": f"{name}，{rank}，兵败被擒，不屈而死。",
        "哗变": f"{name}，{rank}，军士哗变，{name}死于乱军之中。",
        "疾病": f"{name}，{rank}，积劳成疾，卒于军中。",
        "逃亡": f"{name}，{rank}，兵败，匹马逃亡，不知所终。",
    }

    base = death_texts.get(cause, f"{name}，{rank}，亡。")

    extra = []
    if exp > 500:
        extra.append("生前颇有战功")
    if player.get_stat("名") > 60:
        extra.append(f"时名望颇高，人皆惜之")

    result = base
    if extra:
        result += "".join(extra) + "。"
    return result


def format_character_info(player):
    """格式化角色信息"""
    stats = player.stats
    return (
        f"【{player.name}】{player.rank}\n"
        f"  武:{stats.get('武',0):3d} | 智:{stats.get('智',0):3d} | 名:{stats.get('名',0):3d} | 魅:{stats.get('魅',0):3d} | 运:{stats.get('运',0):3d}\n"
        f"  气血:{player.hp:3d}/100 | 士气:{player.morale:3d}/100 | 体力:{player.stamina:3d}/100\n"
        f"  金:{player.gold} | 粮:{player.food} | 经验:{player.exp}\n"
        f"  位置:{player.location}"
    )


def format_event_intro(event_name, time_str):
    """格式化事件标题"""
    return f"\n{'━'*40}\n📜 {event_name}\n{time_str}\n{'━'*40}\n"


def format_choice(options):
    """格式化选项列表"""
    lines = ["\n[请选择]"]
    for i, opt in enumerate(options):
        lines.append(f"  {i+1}. {opt}")
    return "\n".join(lines)