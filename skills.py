"""
技能树系统基础模块
三国文字Roguelike游戏技能定义数据
"""

class Skill:
    def __init__(self, skill_id, name, desc, skill_type, cost, stat_req=None, rank_req=None, prereq=None):
        self.skill_id = skill_id
        self.name = name
        self.desc = desc
        self.skill_type = skill_type  # "passive" | "active"
        self.cost = cost
        self.stat_req = stat_req       # {"武": 60} 或 None
        self.rank_req = rank_req       # "校尉" 或 None
        self.prereq = prereq           # 前置技能ID 或 None


SKILLS = {
    # === 传承被动技能（无前置）===
    "survival_instinct": Skill(
        skill_id="survival_instinct",
        name="求生本能",
        desc="HP<30时，士气下降减半",
        skill_type="passive",
        cost=3,
    ),
    "last_stand": Skill(
        skill_id="last_stand",
        name="背水一战",
        desc="HP<20时，武力+10",
        skill_type="passive",
        cost=5,
    ),
    "mercenary_spirit": Skill(
        skill_id="mercenary_spirit",
        name="佣兵之道",
        desc="战斗胜利后，金钱+5",
        skill_type="passive",
        cost=4,
    ),
    "info_network": Skill(
        skill_id="info_network",
        name="情报网",
        desc="遭遇NPC时，显示该NPC好感度",
        skill_type="passive",
        cost=6,
    ),
    "iron_stamina": Skill(
        skill_id="iron_stamina",
        name="铁人",
        desc="体力消耗减半",
        skill_type="passive",
        cost=5,
    ),
    "lucky_star": Skill(
        skill_id="lucky_star",
        name="吉星高照",
        desc="暴击率+5%",
        skill_type="passive",
        cost=6,
    ),
    "frugal_traveler": Skill(
        skill_id="frugal_traveler",
        name="节俭旅人",
        desc="移动消耗金钱-3",
        skill_type="passive",
        cost=3,
    ),

    # === 传承主动技能（有前置）===
    "sneak_attack": Skill(
        skill_id="sneak_attack",
        name="暗箭",
        desc="本次进攻必定暴击",
        skill_type="active",
        cost=5,
        stat_req={"武": 60},
    ),
    "feint": Skill(
        skill_id="feint",
        name="佯攻",
        desc="本次进攻-10%胜率，但必定先手",
        skill_type="active",
        cost=4,
        stat_req={"武": 50},
    ),
    "rally_cry": Skill(
        skill_id="rally_cry",
        name="呐喊",
        desc="本次战斗，己方士气+15",
        skill_type="active",
        cost=5,
        stat_req={"魅": 50},
    ),
    "counter_stance": Skill(
        skill_id="counter_stance",
        name="反制",
        desc="本次坚守，承受伤害-30%",
        skill_type="active",
        cost=4,
        stat_req={"智": 55},
    ),
    "decisive_strike": Skill(
        skill_id="decisive_strike",
        name="绝技",
        desc="本次进攻伤害x1.5，暴击率+20%",
        skill_type="active",
        cost=10,
        stat_req={"武": 80},
        prereq="sneak_attack",
    ),
    "formations": Skill(
        skill_id="formations",
        name="布阵",
        desc="战斗中无视地形惩罚",
        skill_type="active",
        cost=8,
        stat_req={"智": 70},
        prereq="counter_stance",
    ),
    "reckless_charge": Skill(
        skill_id="reckless_charge",
        name="破釜沉舟",
        desc="本次进攻伤害x2，但承受伤害x1.5",
        skill_type="active",
        cost=6,
        stat_req={"武": 70},
    ),

    # === NPC赠送技能 ===
    "brotherhood_oath": Skill(
        skill_id="brotherhood_oath",
        name="义结金兰",
        desc="与NPC好感度变化+50%",
        skill_type="passive",
        cost=0,
    ),
    "longzhong_strategy": Skill(
        skill_id="longzhong_strategy",
        name="隆中策",
        desc="智谋+5",
        skill_type="passive",
        cost=0,
    ),
    "wei_strategy": Skill(
        skill_id="wei_strategy",
        name="魏武策略",
        desc="名望+10",
        skill_type="passive",
        cost=0,
    ),
    "dragon_valor": Skill(
        skill_id="dragon_valor",
        name="龙胆",
        desc="HP>50时武力+15",
        skill_type="active",
        cost=0,
    ),
}


def get_skill(skill_id):
    """根据ID获取技能，不存在返回None"""
    return SKILLS.get(skill_id)


def can_learn_skill(skill_id, player):
    """
    检查玩家是否可以学习该技能
    返回 (True/False, 失败原因str或None)

    player 对象预期包含以下属性：
        - learned_skills: 已学会的技能ID列表
        - fragments: 当前拥有碎片数量
        - stats: 属性字典，如 {"武": 70, "智": 60, "魅": 50}
        - rank: 官职字符串
    """
    skill = SKILLS.get(skill_id)
    if skill is None:
        return False, f"技能 {skill_id} 不存在"

    # 检查是否已学会
    if skill_id in (player.active_skills + player.passive_skills or []):
        return False, f"已学会 [{skill.name}]"

    # 检查碎片是否足够（cost=0的NPC赠送技能不消耗碎片）
    if skill.cost > 0 and (player.inheritance_fragments or 0) < skill.cost:
        return False, f"碎片不足：需要 {skill.cost}，当前 {player.inheritance_fragments}"

    # 检查属性要求
    if skill.stat_req:
        player_stats = player.stats or {}
        for stat_name, required_value in skill.stat_req.items():
            if player_stats.get(stat_name, 0) < required_value:
                return False, f"属性不足：{stat_name} 需要 {required_value}，当前 {player_stats.get(stat_name, 0)}"

    # 检查官职要求
    if skill.rank_req and player.rank != skill.rank_req:
        return False, f"官职不足：需要 [{skill.rank_req}]，当前 [{player.rank}]"

    # 检查前置技能
    if skill.prereq:
        if skill.prereq not in (player.active_skills + player.passive_skills or []):
            prereq_skill = SKILLS.get(skill.prereq)
            prereq_name = prereq_skill.name if prereq_skill else skill.prereq
            return False, f"需要先学会 [{prereq_name}]"

    return True, None


def get_available_skills_for_player(player, fragments):
    """
    返回玩家可以购买的技能列表（已解锁的不显示）

    返回格式：[Skill, ...]，仅返回当前满足学习条件且未学会的技能
    """
    available = []
    for skill_id, skill in SKILLS.items():
        # 跳过已学会的
        if skill_id in (player.active_skills + player.passive_skills or []):
            continue

        # 检查碎片是否足够（cost=0视为免费）
        if skill.cost > 0 and fragments < skill.cost:
            continue

        # 检查属性要求
        if skill.stat_req:
            player_stats = player.stats or {}
            if not all(player_stats.get(stat, 0) >= req for stat, req in skill.stat_req.items()):
                continue

        # 检查官职要求
        if skill.rank_req and player.rank != skill.rank_req:
            continue

        # 检查前置技能
        if skill.prereq and skill.prereq not in (player.active_skills + player.passive_skills or []):
            continue

        available.append(skill)

    return available
