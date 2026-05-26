"""
角色数据模型
"""
import random
import config


class Character:
    def __init__(self, name=None, is_player=True, preset=None):
        self.name = name or self._random_name()
        self.is_player = is_player

        if preset:
            self.stats = dict(preset["stats"])
            self.rank = preset["rank"]
            self.location = preset["location"]
            self.skills = list(preset.get("skills", []))
        else:
            self.stats = dict(config.INITIAL_STATS)
            # 加一点随机波动
            for k in self.stats:
                self.stats[k] += random.randint(-5, 5)
            self.rank = config.INITIAL_RANK
            self.location = config.INITIAL_LOCATION
            self.skills = []

        self.hp = 100
        self.stamina = config.STAMINA_MAX
        self.morale = config.MORALE_MAX
        self.gold = config.INITIAL_GOLD
        self.food = config.INITIAL_FOOD

        # 经验值
        self.exp = 0

        # 技能列表（主动/被动）
        self.active_skills = []   # 战斗中可使用的技能
        self.passive_skills = []  # 永久生效的被动

        # 传承碎片
        self.inheritance_fragments = 0

        # 状态效果
        self.effects = []  # e.g. ["中毒", "重伤"]

        # NPC好感度（玩家独有）
        self.relations = {}  # {npc_name: value (-100~100)}

    def _random_name(self):
        surnames = ["张", "王", "刘", "陈", "赵", "孙", "周", "吴", "郑", "李"]
        given = ["羽", "飞", "超", "义", "勇", "忠", "德", "仁", "威", "杰"]
        return random.choice(surnames) + random.choice(given)

    def add_skill(self, skill_id):
        """添加技能到对应列表（被动或主动）"""
        from skills import get_skill
        skill = get_skill(skill_id)
        if not skill:
            return
        if skill.skill_type == "active":
            if skill_id not in self.active_skills:
                self.active_skills.append(skill_id)
        elif skill.skill_type == "passive":
            if skill_id not in self.passive_skills:
                self.passive_skills.append(skill_id)

    def has_skill(self, skill_id):
        """检查是否拥有某技能"""
        return skill_id in self.active_skills or skill_id in self.passive_skills

    def get_effective_stat(self, stat):
        """获取属性（含被动技能加成）"""
        base = self.stats.get(stat, 0)

        # last_stand: HP<20时，武力+10
        if "last_stand" in self.passive_skills and stat == "武" and self.hp < 20:
            base += 10

        # longzhong_strategy: 智谋+5
        if "longzhong_strategy" in self.passive_skills and stat == "智":
            base += 5

        # wei_strategy: 名望+10
        if "wei_strategy" in self.passive_skills and stat == "名":
            base += 10

        # dragon_valor: HP>50时武力+15
        if "dragon_valor" in self.active_skills and stat == "武" and self.hp > 50:
            base += 15

        # brotherhood_oath: 好感度变化+50%（通过modify_relation处理，不在这里）

        return base

    def get_stat(self, stat):
        return self.get_effective_stat(stat)

    def modify_stat(self, stat, delta):
        self.stats[stat] = max(1, min(100, self.stats.get(stat, 0) + delta))

    def add_exp(self, amount):
        self.exp += amount
        # 检查升级
        return self.check_level_up()

    def check_level_up(self):
        """检查是否可以升级，返回是否升级成功"""
        next_rank = self._get_next_rank()
        if next_rank and self.exp >= config.RANK_EXP_REQUIRE.get(next_rank, 99999):
            old_rank = self.rank
            self.rank = next_rank
            # 升级时全属性小幅提升
            for k in self.stats:
                self.stats[k] = min(100, self.stats[k] + random.randint(1, 3))
            # 更新本局最高官职（成就系统用）
            if hasattr(self, '_engine_ref') and self._engine_ref.state:
                rs = self._engine_ref.state.run_stats
                new_idx = config.RANK_ORDER.index(next_rank)
                old_idx = rs.get("highest_rank_idx", 0)
                if new_idx > old_idx:
                    rs["highest_rank_idx"] = new_idx
                    rs["highest_rank"] = next_rank
            return True
        return False

    def _get_next_rank(self):
        idx = config.RANK_ORDER.index(self.rank)
        if idx + 1 < len(config.RANK_ORDER):
            return config.RANK_ORDER[idx + 1]
        return None

    def is_alive(self):
        return self.hp > 0

    def take_damage(self, amount):
        self.hp = max(0, self.hp - amount)
        if self.hp <= 30:
            self.add_effect("负伤")

    def heal(self, amount):
        self.hp = min(100, self.hp + amount)
        if self.hp > 30 and "负伤" in self.effects:
            self.effects.remove("负伤")

    def add_effect(self, effect):
        if effect not in self.effects:
            self.effects.append(effect)

    def remove_effect(self, effect):
        if effect in self.effects:
            self.effects.remove(effect)

    def modify_relation(self, npc, delta):
        self.relations[npc] = self.relations.get(npc, 0) + delta
        self.relations[npc] = max(-100, min(100, self.relations[npc]))

    def get_relation(self, npc):
        return self.relations.get(npc, 0)

    def to_dict(self):
        return {
            "name": self.name,
            "stats": dict(self.stats),
            "rank": self.rank,
            "location": self.location,
            "hp": self.hp,
            "exp": self.exp,
            "skills": list(self.skills),
            "active_skills": list(self.active_skills),
            "passive_skills": list(self.passive_skills),
            "inheritance_fragments": self.inheritance_fragments,
            "effects": list(self.effects),
            "relations": dict(self.relations),
            "gold": self.gold,
            "food": self.food,
            "stamina": self.stamina,
            "morale": self.morale,
        }

    @classmethod
    def from_dict(cls, data):
        c = cls(name=data["name"], is_player=True)
        c.stats = dict(data["stats"])
        c.rank = data["rank"]
        c.location = data.get("location", "颍川")
        c.hp = data.get("hp", 100)
        c.exp = data.get("exp", 0)
        c.skills = list(data.get("skills", []))
        c.active_skills = list(data.get("active_skills", []))
        c.passive_skills = list(data.get("passive_skills", []))
        c.inheritance_fragments = data.get("inheritance_fragments", 0)
        c.effects = list(data.get("effects", []))
        c.relations = dict(data.get("relations", {}))
        c.gold = data.get("gold", config.INITIAL_GOLD)
        c.food = data.get("food", config.INITIAL_FOOD)
        c.stamina = data.get("stamina", config.STAMINA_MAX)
        c.morale = data.get("morale", config.MORALE_MAX)
        return c

    def __repr__(self):
        return f"<Character {self.name} [{self.rank}] @ {self.location} 武:{self.stats.get('武',0)} 智:{self.stats.get('智',0)} 名:{self.stats.get('名',0)}>"


class NPC(Character):
    """非玩家角色"""

    def __init__(self, name, preset_stats, rank="", location="", ai_type="normal", npc_type="武将"):
        super().__init__(name=name, is_player=False)
        self.stats = dict(preset_stats)
        self.rank = rank or "未知"
        self.location = location or "未知"
        self.ai_type = ai_type  # normal, aggressive, friendly
        self.npc_type = npc_type  # 文官 / 武将 / 魅力型

    @classmethod
    def from_preset(cls, preset_name):
        """从预设创建NPC（如关羽、张飞等）"""
        presets = NPC_PRESETS.get(preset_name, {})
        return cls(
            name=preset_name,
            preset_stats=presets.get("stats", {"武": 50, "智": 30, "名": 20, "魅": 30, "运": 30}),
            rank=presets.get("rank", "武将"),
            location=presets.get("location", "未知"),
            npc_type=presets.get("type", "武将"),
        )

    def get_stat(self, stat):
        return self.stats.get(stat, 30)

    def to_dict(self):
        d = super().to_dict()
        d["ai_type"] = self.ai_type
        d["npc_type"] = self.npc_type
        return d


# ============ NPC预设（历史武将模板）===========
NPC_PRESETS = {
    # ========== 武将 ==========
    "关羽": {"stats": {"武": 98, "智": 75, "名": 90, "魅": 80, "运": 70}, "rank": "校尉", "location": "涿郡", "type": "武将"},
    "张飞": {"stats": {"武": 95, "智": 35, "名": 60, "魅": 25, "运": 50}, "rank": "伍长", "location": "涿郡", "type": "武将"},
    "赵云": {"stats": {"武": 94, "智": 70, "名": 75, "魅": 65, "运": 85}, "rank": "牙门将", "location": "邺城", "type": "武将"},
    "吕布": {"stats": {"武": 100, "智": 40, "名": 60, "魅": 45, "运": 40}, "rank": "主薄", "location": "并州", "type": "武将"},
    "华雄": {"stats": {"武": 88, "智": 30, "名": 40, "魅": 30, "运": 35}, "rank": "都督", "location": "汜水关", "type": "武将"},
    "颜良": {"stats": {"武": 90, "智": 35, "名": 45, "魅": 35, "运": 40}, "rank": "上将", "location": "白马", "type": "武将"},
    "文丑": {"stats": {"武": 89, "智": 35, "名": 42, "魅": 32, "运": 38}, "rank": "上将", "location": "白马", "type": "武将"},
    "孙坚": {"stats": {"武": 90, "智": 60, "名": 75, "魅": 60, "运": 65}, "rank": "长沙太守", "location": "长沙", "type": "武将"},
    "孙策": {"stats": {"武": 93, "智": 65, "名": 80, "魅": 75, "运": 70}, "rank": "校尉", "location": "吴郡", "type": "武将"},
    "董卓": {"stats": {"武": 82, "智": 55, "名": 50, "魅": 60, "运": 45}, "rank": "太师", "location": "洛阳", "type": "武将"},
    # ========== 文官 ==========
    "周瑜": {"stats": {"武": 60, "智": 95, "名": 85, "魅": 80, "运": 60}, "rank": "建威中郎将", "location": "吴郡", "type": "文官"},
    "诸葛亮": {"stats": {"武": 30, "智": 99, "名": 95, "魅": 90, "运": 90}, "rank": "隆中隐士", "location": "南阳", "type": "文官"},
    "袁绍": {"stats": {"武": 60, "智": 65, "名": 80, "魅": 70, "运": 55}, "rank": "盟主", "location": "邺城", "type": "文官"},
    "刘备": {"stats": {"武": 55, "智": 70, "名": 95, "魅": 95, "运": 80}, "rank": "安喜尉", "location": "涿郡", "type": "文官"},
    "曹操": {"stats": {"武": 75, "智": 90, "名": 88, "魅": 85, "运": 85}, "rank": "典军校尉", "location": "陈留", "type": "文官"},
    # ========== 虚构NPC（用于开局引导）==========
    "江湖游侠": {"stats": {"武": 65, "智": 40, "名": 15, "魅": 55, "运": 35}, "rank": "游侠", "location": "颍川", "type": "武将"},
}
