"""
三国文字Roguelike - 配置文件
"""

# ============ 游戏时间 ============
START_YEAR = 184
START_MONTH = 1
END_YEAR = 220  # 三国鼎立，本篇结局

# ============ 角色初始属性 ============
INITIAL_STATS = {
    "武": 40,      # 武力，影响战斗
    "智": 30,      # 智谋，影响计策
    "名": 10,      # 名望，影响招募和NPC态度
    "魅": 20,      # 魅力，影响舌战说服
    "运": 30,      # 气运，影响暴击和稀有事件
}
INITIAL_RANK = "散兵"
INITIAL_LOCATION = "颍川"  # 黄巾之乱的发源地之一

# ============ 战斗参数 ============
BASE_WIN_RATE = 0.5       # 基础胜率（属性相同时）
STAT_WEIGHT_BATTLE = 2    # 属性差值对胜率的权重
STAMINA_MAX = 100         # 最大体力
MORALE_MAX = 100          # 最大士气
MORALE_THRESHOLD = 30     # 士气低于此值可能溃逃

# ============ 资源参数 ============
INITIAL_GOLD = 50         # 初始金钱
INITIAL_FOOD = 50         # 初始粮草
INITIAL_TROOPS = 40       # 初始兵力（持久）
MIN_TROOPS = 5            # 兵力下限（贴身亲兵，不会归零）
MAX_GOLD = 9999
MAX_FOOD = 999

# ============ 征兵系统 ============
# 每级官职的兵力上限（征兵不能超过）
RANK_TROOP_CAP = {
    "散兵": 60, "什长": 90, "伍长": 120, "队长": 160,
    "曲长": 200, "司马": 260, "校尉": 340, "中郎将": 440,
    "牙门将": 560, "偏将军": 700, "禅将军": 860,
    "镇北将军": 1040, "车骑将军": 1240, "大将军": 1500, "诸侯": 2000,
}
# 征兵价格：每招 10 兵消耗
TROOP_RECRUIT_BATCH = 10   # 每次征兵人数
TROOP_RECRUIT_GOLD = 10    # 每批花费金
TROOP_RECRUIT_FOOD = 8     # 每批花费粮
# 兵粮消耗：每月每 20 兵额外消耗 1 粮
TROOP_FOOD_PER = 20

# ============ 升级经验 ============
RANK_EXP_REQUIRE = {
    "散兵": 0,
    "什长": 30,
    "伍长": 80,
    "队长": 150,
    "曲长": 280,
    "司马": 400,
    "校尉": 500,
    "中郎将": 650,
    "牙门将": 1300,
    "偏将军": 1650,
    "禅将军": 2050,
    "镇北将军": 2500,
    "车骑将军": 3000,
    "大将军": 3600,
    "诸侯": 99999,
}
RANK_ORDER = ["散兵", "什长", "伍长", "队长", "曲长", "司马", "校尉", "中郎将", "牙门将", "偏将军", "禅将军", "镇北将军", "车骑将军", "大将军", "诸侯"]

# 官职月俸（gold per month）
RANK_SALARY = {
    "散兵": 5,
    "什长": 7,
    "伍长": 9,
    "队长": 12,
    "曲长": 14,
    "司马": 16,
    "校尉": 18,
    "中郎将": 20,
    "牙门将": 22,
    "偏将军": 24,
    "禅将军": 26,
    "镇北将军": 28,
    "车骑将军": 30,
    "大将军": 30,
    "诸侯": 30,
}

# ============ 事件定义 ============
# 必然事件：(年份, 月份) -> 事件名
# 条件事件：check_conditions(state) -> bool

# ============ 叙事风格 ============
NARRATIVE_TONE = "史书+江湖气"  # 参考《三国演义》章回体 + 《资治通鉴》简洁

# ============ 解锁进度文件 ============
PROGRESSION_FILE = "sanguo_roguelike/progression.json"
REINCARNATION_FILE = "sanguo_roguelike/reincarnation.json"

# ============ 城市好感度配置 ============
CITY_FAVORABILITY = {
    "neutral": 50,
    "friendly_threshold": 70,
    "allied_threshold": 90,
    "hostile_threshold": 30,
    "monthly_gain": 1,
    "battle_win_gain": 3,
    "recruit_gain": 5,
    "battle_loss_penalty": 5,
}

# ============ 转世加成（死后继承）===========
# 死亡时，各属性按此比例转化为业力（永久累积）
REINCARNATION_CARRY_RATES = {
    "武": 0.12,   # 武力转世率 12%（配合压缩后的cap）
    "智": 0.10,   # 智谋转世率 10%
    "名": 0.10,   # 名望转世率 10%
    "魅": 0.12,   # 魅力转世率 12%
    "运": 0.08,   # 运气转世率 8%
}
# 各属性业力累加上限（基础上限，装备/道具可额外+20）
REINCARNATION_CAPS = {
    "武": 600,   # 基础上限600，装备加成后最高720
    "智": 480,   # 基础上限480，装备加成后最高560
    "名": 400,   # 基础上限400，装备加成后最高480
    "魅": 400,   # 基础上限400，装备加成后最高480
    "运": 320,   # 基础上限320，装备加成后最高400
}  # 总上限 2200


SAVE_DIR = "sanguo_roguelike/saves"
UNLOCK_FILE = "sanguo_roguelike/unlocks.json"
HISTORY_FILE = "sanguo_roguelike/history_records.jsonl"
ACHIEVEMENTS_FILE = "sanguo_roguelike/achievements.json"

# ============ 阵容系统 ============
TEAM_CAPACITY = 4  # 初始阵容容量（上限4人，超出需替换板凳）