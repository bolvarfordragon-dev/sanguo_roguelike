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
        self.troops = getattr(config, "INITIAL_TROOPS", 40)  # 持久兵力

        # 经验值
        self.exp = 0

        # 技能列表（主动/被动）
        self.active_skills = []   # 战斗中可使用的技能
        self.passive_skills = []  # 永久生效的被动

        # 传承碎片
        self.inheritance_fragments = 0

        # 状态效果（新：dict格式）
        # 格式：{effect_id: {"turns": n, "stacks": n}}
        # turn<0 表示永久/无限
        self.effects = {}

        # NPC好感度（玩家独有）
        self.relations = {}  # {npc_name: value (-100~100)}

        # 装备槽位（最多3件）
        self.equipment = []  # list of equipped item dicts

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

        # 装备加成
        if hasattr(self, 'equipment') and self.equipment:
            eq_bonuses = self.get_equipment_bonuses()
            base += eq_bonuses.get(stat, 0)

        # Buff/Debuff属性修正
        base += self.get_effect_stat_mod(stat)

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
                # 触发升级事件（供 engine 设置 pending_rank_up）
                self._engine_ref._on_rank_up(old_rank, next_rank)
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
        if self.hp <= 30 and not self.has_effect("负伤"):
            self.add_effect("负伤")

    def heal(self, amount):
        self.hp = min(100, self.hp + amount)
        if self.hp > 30 and self.has_effect("负伤"):
            self.remove_effect("负伤")

    def has_effect(self, effect_id):
        """检查是否有某效果"""
        return effect_id in self.effects

    def add_effect(self, effect_id, turns=None, stacks=None):
        """添加状态效果，支持计时/叠加"""
        from effects import get_effect
        eff = get_effect(effect_id)
        if not eff:
            return
        if effect_id not in self.effects:
            duration_type = eff.get("duration_type", "timed")
            if turns is None:
                turns = eff.get("default_duration", 3)
            self.effects[effect_id] = {
                "turns": turns,
                "stacks": stacks if stacks is not None else 1,
                "duration_type": duration_type,
            }
        else:
            # 可叠加效果，增加层数/回合
            if eff.get("duration_type") == "stackable":
                self.effects[effect_id]["stacks"] = self.effects[effect_id].get("stacks", 1) + 1
                self.effects[effect_id]["turns"] = max(self.effects[effect_id]["turns"], turns or 3)

    def remove_effect(self, effect_id):
        if effect_id in self.effects:
            del self.effects[effect_id]

    def tick_effects(self):
        """每月tick时调用，减少持续时间，返回触发的事件描述"""
        from effects import get_effect
        events = []
        expired = []
        for eid, data in list(self.effects.items()):
            eff = get_effect(eid)
            if not eff:
                continue
            dt = data.get("duration_type", "timed")
            if dt == "timed":
                data["turns"] -= 1
                if data["turns"] <= 0:
                    expired.append(eid)
            elif dt == "permanent" or dt == "stackable":
                # stackable自然消退
                if data["turns"] > 0:
                    data["turns"] -= 1
                    if data["turns"] <= 0:
                        expired.append(eid)
            # 中毒: 每回合扣HP
            if eid == "中毒" and eff.get("type") == "debuff":
                dmg = 5 * data.get("stacks", 1)
                self.hp = max(0, self.hp - dmg)
                events.append(f"【中毒】毒素发作，HP-{dmg}")
            # 疗伤: 每回合回HP
            elif eid == "疗伤" and eff.get("type") == "buff":
                heal_amt = 5
                self.heal(heal_amt)  # F2: 用 heal() 而非直接赋值，让 heal() 内置的 HP>30 自动移除「负伤」逻辑生效（对齐 engine.py P-B 注释意图）
                events.append(f"【疗伤】伤势恢复，HP+{heal_amt}")
        for eid in expired:
            eff = get_effect(eid)
            if eff:
                events.append(f"【{eff['name']}】{eff.get('on_remove', '效果结束')}")
            self.remove_effect(eid)
        return events

    def get_effect_stat_mod(self, stat):
        """计算某属性的效果加成总和"""
        from effects import get_effect
        total = 0
        for eid, data in self.effects.items():
            eff = get_effect(eid)
            if not eff or not eff.get("stat_mods"):
                continue
            mod = eff["stat_mods"].get(stat, 0)
            stacks = data.get("stacks", 1)
            duration_type = data.get("duration_type", "")
            if duration_type == "stackable":
                total += mod * stacks
            else:
                total += mod
        return total

    def get_combat_mods(self):
        """获取战斗修正（所有active effects的combat_mods合并）"""
        from effects import get_effect
        result = {}
        for eid, data in self.effects.items():
            eff = get_effect(eid)
            if not eff or not eff.get("combat_mods"):
                continue
            for k, v in eff["combat_mods"].items():
                if k in result:
                    result[k] += v
                else:
                    result[k] = v
        return result

    def modify_relation(self, npc, delta):
        self.relations[npc] = self.relations.get(npc, 0) + delta
        self.relations[npc] = max(-100, min(100, self.relations[npc]))

    def get_relation(self, npc):
        return self.relations.get(npc, 0)

    def add_equipment(self, item):
        """Equip an item. Returns True if equipped, False if slots full."""
        from equipment import EQUIPMENT_SLOTS
        if len(self.equipment) >= EQUIPMENT_SLOTS:
            return False
        self.equipment.append(dict(item))
        return True

    def remove_equipment(self, slot_index):
        """Remove equipment at slot index. Returns the removed item or None."""
        if 0 <= slot_index < len(self.equipment):
            return self.equipment.pop(slot_index)
        return None

    def get_equipment_bonuses(self):
        """Return aggregate stat bonuses from all equipped items."""
        from equipment import apply_equipment_stats
        return apply_equipment_stats(self)


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
            "effects": dict(self.effects),
            "relations": dict(self.relations),
            "gold": self.gold,
            "food": self.food,
            "troops": self.troops,
            "stamina": self.stamina,
            "morale": self.morale,
            "equipment": list(self.equipment),
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
        c.effects = dict(data.get("effects", {}))
        c.relations = dict(data.get("relations", {}))
        c.gold = data.get("gold", config.INITIAL_GOLD)
        c.food = data.get("food", config.INITIAL_FOOD)
        c.troops = data.get("troops", getattr(config, "INITIAL_TROOPS", 40))
        c.stamina = data.get("stamina", config.STAMINA_MAX)
        c.morale = data.get("morale", config.MORALE_MAX)
        c.equipment = list(data.get("equipment", []))
        return c

    def __repr__(self):
        return f"<Character {self.name} [{self.rank}] @ {self.location} 武:{self.stats.get('武',0)} 智:{self.stats.get('智',0)} 名:{self.stats.get('名',0)}>"


class NPC(Character):
    """非玩家角色"""

    def __init__(self, name, preset_stats, rank="", location="", ai_type="normal", npc_type="武将", faction="群雄", bonds=None):
        super().__init__(name=name, is_player=False)
        self.stats = dict(preset_stats)
        self.rank = rank or "未知"
        self.location = location or "未知"
        self.ai_type = ai_type  # normal, aggressive, friendly
        self.npc_type = npc_type  # 文官 / 武将 / 魅力型
        self.faction = faction  # 蜀 / 魏 / 吴 / 群雄 / 民间
        self.bonds = bonds or []  # 羁绊列表

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
            faction=presets.get("faction", "群雄"),
            bonds=presets.get("bonds", []),
        )

    def get_stat(self, stat):
        return self.stats.get(stat, 30)

    def to_dict(self):
        d = super().to_dict()
        d["ai_type"] = self.ai_type
        d["npc_type"] = self.npc_type
        d["faction"] = self.faction
        return d


# ============ NPC预设（历史武将模板）===========
# bonds: 羁绊组队，同组≥2人额外+1%战力（与阵营叠加）
NPC_PRESETS = {
    # ========== 蜀 ==========
    "关羽": {"stats": {"武": 98, "智": 75, "名": 90, "魅": 80, "运": 70}, "rank": "校尉", "location": "涿郡", "type": "武将", "faction": "蜀", "bonds": ["桃园三兄弟", "五虎上将", "襄樊死斗"]},
    "张飞": {"stats": {"武": 95, "智": 35, "名": 60, "魅": 25, "运": 50}, "rank": "伍长", "location": "涿郡", "type": "武将", "faction": "蜀", "bonds": ["桃园三兄弟", "五虎上将"]},
    "赵云": {"stats": {"武": 94, "智": 70, "名": 75, "魅": 65, "运": 85}, "rank": "牙门将", "location": "涿郡", "type": "武将", "faction": "蜀", "bonds": ["五虎上将"]},
    "刘备": {"stats": {"武": 55, "智": 70, "名": 95, "魅": 95, "运": 80}, "rank": "安喜尉", "location": "涿郡", "type": "君主", "faction": "蜀", "bonds": ["桃园三兄弟", "三顾茅庐"]},
    "诸葛亮": {"stats": {"武": 30, "智": 99, "名": 95, "魅": 90, "运": 90}, "rank": "隆中隐士", "location": "南阳", "type": "文官", "faction": "蜀", "bonds": ["诸葛四友", "三顾茅庐"]},
    "黄忠": {"stats": {"武": 91, "智": 50, "名": 60, "魅": 45, "运": 55}, "rank": "校尉", "location": "长沙", "type": "武将", "faction": "蜀", "bonds": ["五虎上将"]},
    "魏延": {"stats": {"武": 87, "智": 55, "名": 45, "魅": 40, "运": 50}, "rank": "牙门将", "location": "长沙", "type": "武将", "faction": "蜀", "bonds": ["反骨天生"]},
    "庞统": {"stats": {"武": 30, "智": 92, "名": 70, "魅": 60, "运": 55}, "rank": "县令", "location": "南阳", "type": "文官", "faction": "蜀", "bonds": ["诸葛四友"]},
    "法正": {"stats": {"武": 40, "智": 83, "名": 55, "魅": 60, "运": 50}, "rank": "军师", "location": "成都", "type": "文官", "faction": "蜀", "bonds": ["蜀中双杰"]},
    "徐庶": {"stats": {"武": 35, "智": 80, "名": 60, "魅": 65, "运": 50}, "rank": "军师", "location": "新野", "type": "文官", "faction": "蜀", "bonds": ["诸葛四友"]},
    "马超": {"stats": {"武": 94, "智": 45, "名": 70, "魅": 50, "运": 60}, "rank": "偏将军", "location": "西凉", "type": "武将", "faction": "蜀", "bonds": ["五虎上将"]},
    # ========== 魏 ==========
    "曹操": {"stats": {"武": 75, "智": 90, "名": 88, "魅": 85, "运": 85}, "rank": "典军校尉", "location": "陈留", "type": "君主", "faction": "魏", "bonds": ["乱世奸雄", "曹氏兄弟"]},
    "司马懿": {"stats": {"武": 45, "智": 95, "名": 80, "魅": 75, "运": 75}, "rank": "主薄", "location": "许昌", "type": "文官", "faction": "魏", "bonds": ["鹰视狼顾"]},
    "张辽": {"stats": {"武": 92, "智": 65, "名": 70, "魅": 55, "运": 65}, "rank": "中郎将", "location": "白马", "type": "武将", "faction": "魏", "bonds": ["五子良将", "威震逍遥津"]},
    "徐晃": {"stats": {"武": 90, "智": 60, "名": 55, "魅": 45, "运": 55}, "rank": "校尉", "location": "白马", "type": "武将", "faction": "魏", "bonds": ["五子良将"]},
    "张郃": {"stats": {"武": 87, "智": 65, "名": 50, "魅": 40, "运": 50}, "rank": "偏将军", "location": "白马", "type": "武将", "faction": "魏", "bonds": ["五子良将", "河北四庭柱"]},
    "荀彧": {"stats": {"武": 30, "智": 92, "名": 78, "魅": 70, "运": 60}, "rank": "尚书", "location": "许昌", "type": "文官", "faction": "魏", "bonds": ["颍川双杰"]},
    "郭嘉": {"stats": {"武": 28, "智": 90, "名": 65, "魅": 60, "运": 70}, "rank": "军师祭酒", "location": "许昌", "type": "文官", "faction": "魏", "bonds": ["颍川双杰"]},
    "贾诩": {"stats": {"武": 35, "智": 88, "名": 50, "魅": 55, "运": 65}, "rank": "太尉", "location": "许昌", "type": "文官", "faction": "魏", "bonds": ["算无遗策"]},
    "庞德": {"stats": {"武": 88, "智": 50, "名": 45, "魅": 40, "运": 45}, "rank": "校尉", "location": "白马", "type": "武将", "faction": "魏", "bonds": ["襄樊死斗"]},
    # ========== 吴 ==========
    "孙坚": {"stats": {"武": 90, "智": 60, "名": 75, "魅": 60, "运": 65}, "rank": "长沙太守", "location": "长沙", "type": "武将", "faction": "吴", "bonds": ["江东三代"]},
    "孙权": {"stats": {"武": 70, "智": 80, "名": 85, "魅": 90, "运": 85}, "rank": "讨逆将军", "location": "吴郡", "type": "君主", "faction": "吴", "bonds": ["江东三代"]},
    "孙策": {"stats": {"武": 93, "智": 65, "名": 80, "魅": 75, "运": 70}, "rank": "校尉", "location": "吴郡", "type": "武将", "faction": "吴", "bonds": ["江东四杰", "江东三代", "孙策知遇"]},
    "周瑜": {"stats": {"武": 60, "智": 95, "名": 85, "魅": 80, "运": 60}, "rank": "建威中郎将", "location": "吴郡", "type": "文官", "faction": "吴", "bonds": ["江东四杰"]},
    "太史慈": {"stats": {"武": 88, "智": 55, "名": 65, "魅": 50, "运": 60}, "rank": "校尉", "location": "东莱", "type": "武将", "faction": "吴", "bonds": ["孙策知遇"]},
    "甘宁": {"stats": {"武": 86, "智": 50, "名": 55, "魅": 45, "运": 55}, "rank": "校尉", "location": "江夏", "type": "武将", "faction": "吴", "bonds": ["锦帆贼"]},
    "鲁肃": {"stats": {"武": 35, "智": 85, "名": 70, "魅": 75, "运": 55}, "rank": "都尉", "location": "吴郡", "type": "文官", "faction": "吴", "bonds": ["江东四杰"]},
    "陆逊": {"stats": {"武": 40, "智": 88, "名": 72, "魅": 70, "运": 65}, "rank": "偏将军", "location": "吴郡", "type": "文官", "faction": "吴", "bonds": ["江东四杰"]},
    # ========== 群雄 ==========
    "吕布": {"stats": {"武": 100, "智": 40, "名": 60, "魅": 45, "运": 40}, "rank": "主薄", "location": "并州", "type": "武将", "faction": "群雄", "bonds": ["义父子弑"]},
    "华雄": {"stats": {"武": 88, "智": 30, "名": 40, "魅": 30, "运": 35}, "rank": "都督", "location": "汜水关", "type": "武将", "faction": "群雄", "bonds": ["汜水虎将"]},
    "高览": {"stats": {"武": 87, "智": 55, "名": 45, "魅": 40, "运": 50}, "rank": "偏将军", "location": "白马", "type": "武将", "faction": "群雄", "bonds": ["河北四庭柱"]},
    "颜良": {"stats": {"武": 90, "智": 35, "名": 45, "魅": 35, "运": 40}, "rank": "上将", "location": "白马", "type": "武将", "faction": "群雄", "bonds": ["河北四庭柱"]},
    "文丑": {"stats": {"武": 89, "智": 35, "名": 42, "魅": 32, "运": 38}, "rank": "上将", "location": "白马", "type": "武将", "faction": "群雄", "bonds": ["河北四庭柱"]},
    "袁绍": {"stats": {"武": 60, "智": 65, "名": 80, "魅": 70, "运": 55}, "rank": "盟主", "location": "邺城", "type": "文官", "faction": "群雄", "bonds": ["河北霸主"]},
    "董卓": {"stats": {"武": 82, "智": 55, "名": 50, "魅": 60, "运": 45}, "rank": "太师", "location": "洛阳", "type": "武将", "faction": "群雄", "bonds": ["董卓之乱"]},
    "陈宫": {"stats": {"武": 40, "智": 82, "名": 55, "魅": 50, "运": 45}, "rank": "别驾", "location": "濮阳", "type": "文官", "faction": "群雄", "bonds": ["谋士无双"]},
    # ========== 新增魏武将 ==========
    "典韦": {"stats": {"武": 95, "智": 40, "名": 65, "魅": 45, "运": 55}, "rank": "校尉", "location": "许昌", "type": "武将", "faction": "魏", "bonds": ["虎痴恶来"]},
    "许褚": {"stats": {"武": 94, "智": 35, "名": 60, "魅": 50, "运": 50}, "rank": "校尉", "location": "许昌", "type": "武将", "faction": "魏", "bonds": ["虎痴恶来"]},
    "夏侯惇": {"stats": {"武": 90, "智": 60, "名": 75, "魅": 70, "运": 65}, "rank": "校尉", "location": "许昌", "type": "武将", "faction": "魏", "bonds": ["夏侯兄弟"]},
    "夏侯渊": {"stats": {"武": 88, "智": 55, "名": 65, "魅": 55, "运": 60}, "rank": "校尉", "location": "白马", "type": "武将", "faction": "魏", "bonds": ["夏侯兄弟"]},
    "曹仁": {"stats": {"武": 86, "智": 65, "名": 70, "魅": 65, "运": 60}, "rank": "校尉", "location": "许昌", "type": "武将", "faction": "魏", "bonds": ["曹氏兄弟"]},
    # ========== 新增群雄/民间 ==========
    "张角": {"stats": {"武": 30, "智": 75, "名": 80, "魅": 90, "运": 85}, "rank": "大贤良师", "location": "邺城", "type": "文官", "faction": "民间", "bonds": ["黄巾起义"]},
    "管亥": {"stats": {"武": 82, "智": 40, "名": 40, "魅": 35, "运": 40}, "rank": "渠帅", "location": "北海", "type": "武将", "faction": "民间", "bonds": ["黄巾起义"]},
    "文聘": {"stats": {"武": 85, "智": 50, "名": 55, "魅": 45, "运": 50}, "rank": "校尉", "location": "江夏", "type": "武将", "faction": "魏", "bonds": ["荆州守将"]},
    # ========== 民间 ==========
    "江湖游侠": {"stats": {"武": 65, "智": 40, "名": 15, "魅": 55, "运": 35}, "rank": "游侠", "location": "颍川", "type": "武将", "faction": "民间", "bonds": ["草莽豪杰"]},
}
