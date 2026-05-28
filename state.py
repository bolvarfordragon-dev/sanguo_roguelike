"""
游戏状态管理
"""
import json
import os
from datetime import datetime
import config


class GameState:
    """全局游戏状态"""

    def __init__(self):
        self.year = config.START_YEAR
        self.month = config.START_MONTH
        self.player = None
        self.npcs = {}         # {npc_name: NPC}
        self.active_events = []  # 当前正在触发的事件栈
        self.event_flags = {}    # 事件标记（如"讨董已触发"）
        self.global_flags = {}   # 全局状态标记
        self.turn_count = 0
        # 本局统计（每局重置）
        self.run_stats = {
            "battles_this_run": 0,
            "wins": 0,
            "losses": 0,
            "win_streak": 0,
            "lose_streak": 0,
            "npcs_recruited_this_run": [],
            "events_triggered_this_run": 0,
            "highest_rank": "散兵",
            "total_exp_earned": 0,
            # 行为业力追踪（用于转世加成）
            "karma_wins": 0,        # 战斗胜利场数
            "karma_npc_recruited": 0,  # 本局招募NPC数
            "karma_history_events": 0,  # 本局触发历史事件数
            "karma_speech_wins": 0,     # 本局舌战胜数
            "karma_rare_encounters": 0, # 本局稀有奇遇数
        }
        # 城市好感度 {city_name: 0-100, neutral=50}
        self.city_favorability = {}

    def _reset_runtime_state(self):
        """Reset per-run data structures called by new_game()"""
        self.battle_history = []
        self.history_log = []

    def tick(self):
        """推进一个月"""
        self.month += 1
        if self.month > 12:
            self.month = 1
            self.year += 1
        self.turn_count += 1

    def get_time_str(self):
        """返回当前时间字符串"""
        return f"{self.year}年{self.month}月"

    def advance_time(self, months=1):
        """前进指定月数"""
        for _ in range(months):
            self.tick()

    def set_player(self, player):
        self.player = player

    def get_player(self):
        return self.player

    def is_game_over(self):
        """检查游戏是否结束"""
        # 玩家死亡
        if self.player and self.player.hp <= 0:
            return True
        # 到达结局年
        if self.year >= config.END_YEAR:
            return True
        return False

    def get_elapsed_months(self):
        """从游戏开始经过的月数"""
        return (self.year - config.START_YEAR) * 12 + (self.month - config.START_MONTH)

    def save(self, path):
        """保存存档"""
        os.makedirs(os.path.dirname(path), exist_ok=True)
        data = {
            "year": self.year,
            "month": self.month,
            "turn_count": self.turn_count,
            "player": self.player.to_dict() if self.player else None,
            "event_flags": self.event_flags,
            "global_flags": self.global_flags,
            "npcs": {name: npc.to_dict() for name, npc in self.npcs.items()},
            "city_favorability": self.city_favorability,
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    @classmethod
    def load(cls, path):
        """加载存档"""
        from character import Character, NPC
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        state = cls()
        state.year = data["year"]
        state.month = data["month"]
        state.turn_count = data.get("turn_count", 0)
        state.event_flags = data.get("event_flags", {})
        state.global_flags = data.get("global_flags", {})
        state.city_favorability = data.get("city_favorability", {})
        if data.get("player"):
            state.player = Character.from_dict(data["player"])
        state.npcs = {}
        for name, npc_data in data.get("npcs", {}).items():
            npc = NPC(name=npc_data["name"], preset_stats=npc_data["stats"])
            npc.rank = npc_data.get("rank", "武将")
            npc.location = npc_data.get("location", "未知")
            npc.hp = npc_data.get("hp", 100)
            npc.morale = npc_data.get("morale", 100)
            state.npcs[name] = npc
        return state

    def to_dict(self):
        return {
            "year": self.year,
            "month": self.month,
            "turn_count": self.turn_count,
            "player_rank": self.player.rank if self.player else None,
            "player_location": self.player.location if self.player else None,
            "event_flags": list(self.event_flags.keys()),
            "city_favorability": self.city_favorability,
        }