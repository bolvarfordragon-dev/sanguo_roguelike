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
MAX_GOLD = 9999
MAX_FOOD = 999

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
# 特殊：武可通过装备达到120，智/名/魅/运可达100
REINCARNATION_CAPS = {
    "武": 150,   # 基础上限150，装备加成后最高180
    "智": 120,   # 基础上限120，装备加成后最高140
    "名": 100,   # 基础上限100，装备加成后最高120
    "魅": 100,   # 基础上限100，装备加成后最高120
    "运": 80,    # 基础上限80，装备加成后最高100
}


SAVE_DIR = "sanguo_roguelike/saves"
UNLOCK_FILE = "sanguo_roguelike/unlocks.json"
HISTORY_FILE = "sanguo_roguelike/history_records.jsonl"
ACHIEVEMENTS_FILE = "sanguo_roguelike/achievements.json"