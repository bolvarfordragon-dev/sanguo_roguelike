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
INITIAL_FOOD = 30         # 初始粮草
MAX_GOLD = 9999
MAX_FOOD = 999

# ============ 升级经验 ============
RANK_EXP_REQUIRE = {
    "散兵": 0,
    "什长": 30,
    "伍长": 80,
    "队长": 150,
    "曲长": 280,
    "司马": 450,
    "校尉": 700,
    "中郎将": 1000,
    "将军": 1500,
    "诸侯": 99999,  # 终极形态
}
RANK_ORDER = ["散兵", "什长", "伍长", "队长", "曲长", "司马", "校尉", "中郎将", "将军", "诸侯"]

# ============ 事件定义 ============
# 必然事件：(年份, 月份) -> 事件名
# 条件事件：check_conditions(state) -> bool

# ============ 叙事风格 ============
NARRATIVE_TONE = "史书+江湖气"  # 参考《三国演义》章回体 + 《资治通鉴》简洁

# ============ 解锁进度文件 ============
PROGRESSION_FILE = "sanguo_roguelike/progression.json"
SAVE_DIR = "sanguo_roguelike/saves"
UNLOCK_FILE = "sanguo_roguelike/unlocks.json"
HISTORY_FILE = "sanguo_roguelike/history_records.jsonl"