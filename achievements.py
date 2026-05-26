"""
成就系统
定义所有成就及其解锁条件
"""
import os
import json


class Achievement:
    def __init__(self, id, name, desc, icon, karma_reward, condition_fn):
        self.id = id
        self.name = name
        self.desc = desc
        self.icon = icon
        self.karma_reward = karma_reward
        self.condition_fn = condition_fn  # fn(state) -> bool

    def is_unlocked(self, state):
        """检查成就是否满足解锁条件"""
        try:
            return self.condition_fn(state)
        except Exception:
            return False


# ── 条件函数 ──────────────────────────────────────────

def _first_death(state):
    """第一次死亡"""
    return state.run_stats.get("total_deaths", 0) >= 1

def _survive_10_years(state):
    """存活超过10年"""
    elapsed = (state.year - 184) * 12 + state.month
    return elapsed >= 120  # 10 years = 120 months

def _first_sima(state):
    """首次晋升到司马"""
    RANK_ORDER = ["散兵", "什长", "伍长", "队长", "曲长", "司马", "校尉", "中郎将",
                  "牙门将", "偏将军", "裨将军", "镇北将军", "安南将军", "车骑将军", "大将军", "诸侯"]
    return state.run_stats.get("highest_rank_idx", 0) >= RANK_ORDER.index("司马")

def _recruited_non_roamer(state):
    """成功招募任意非游侠NPC"""
    # Check if any non-roamer NPC was recruited
    for flag in state.event_flags:
        if flag.startswith("已招募_") and state.event_flags[flag]:
            npc_name = flag.replace("已招募_", "")
            # Exclude generic NPCs (游侠)
            if npc_name not in ["游侠", "流民", "山贼", "散兵"]:
                return True
    return False

def _taoyuan_oath(state):
    """触发桃园结义事件"""
    return state.event_flags.get("桃园结义", False)

def _battles_over_20(state):
    """一局内战斗超过20次"""
    return state.run_stats.get("battles_this_run", 0) > 20

def _death_20_times(state):
    """累积死亡20次"""
    return state.run_stats.get("total_deaths", 0) >= 20

def _survive_to_220(state):
    """存活到220年"""
    return state.year >= 220 and (getattr(state.player, 'hp', 0) or 0) > 0


# ── 成就列表 ──────────────────────────────────────────

ACHIEVEMENTS = [
    Achievement(
        id="first_death",
        name="初入乱世",
        desc="经历第一次死亡",
        icon="💀",
        karma_reward=1,
        condition_fn=_first_death,
    ),
    Achievement(
        id="survive_10_years",
        name="十年生聚",
        desc="存活超过10年",
        icon="📅",
        karma_reward=2,
        condition_fn=_survive_10_years,
    ),
    Achievement(
        id="first_sima",
        name="武将之才",
        desc="首次晋升到司马",
        icon="⚔️",
        karma_reward=3,
        condition_fn=_first_sima,
    ),
    Achievement(
        id="recruited_hero",
        name="招募名将",
        desc="成功招募任意非游侠NPC",
        icon="👥",
        karma_reward=5,
        condition_fn=_recruited_non_roamer,
    ),
    Achievement(
        id="taoyuan_oath",
        name="桃园之誓",
        desc="触发桃园结义事件",
        icon="🌸",
        karma_reward=5,
        condition_fn=_taoyuan_oath,
    ),
    Achievement(
        id="battles_20",
        name="百战余生",
        desc="一局内战斗超过20次",
        icon="🏅",
        karma_reward=3,
        condition_fn=_battles_over_20,
    ),
    Achievement(
        id="death_20",
        name="乱世轮回者",
        desc="累积死亡20次",
        icon="🔄",
        karma_reward=10,
        condition_fn=_death_20_times,
    ),
    Achievement(
        id="unify_china",
        name="一统天下",
        desc="存活到220年",
        icon="👑",
        karma_reward=20,
        condition_fn=_survive_to_220,
    ),
]


def get_achievement_by_id(aid):
    for a in ACHIEVEMENTS:
        if a.id == aid:
            return a
    return None


# ── 进度文件读写 ──────────────────────────────────────

def load_achievements(filepath):
    """加载已解锁成就列表"""
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return set(json.load(f))
        except Exception:
            pass
    return set()


def save_achievements(filepath, unlocked_ids):
    """保存已解锁成就列表"""
    os.makedirs(os.path.dirname(filepath) if filepath else '.', exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(list(unlocked_ids), f, ensure_ascii=False, indent=2)


# ── 检查并解锁 ───────────────────────────────────────

def check_achievements(state, unlocked_ids):
    """
    检查所有未解锁成就，返回新增解锁的成就列表
    state: GameState 或类似对象
    unlocked_ids: 当前已解锁的成就ID集合（set）
    """
    newly_unlocked = []
    for ach in ACHIEVEMENTS:
        if ach.id in unlocked_ids:
            continue
        if ach.is_unlocked(state):
            newly_unlocked.append(ach)
    return newly_unlocked