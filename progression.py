"""
解锁/永久进度系统
"""
import json
import os


class Progression:
    """解锁进度管理"""

    def __init__(self, unlock_file, history_file):
        self.unlock_file = unlock_file
        self.history_file = history_file
        self.unlocks = self._load_unlocks()
        self.history = self._load_history()

    def _load_unlocks(self):
        if os.path.exists(self.unlock_file):
            with open(self.unlock_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return {
            "unlocked_heroes": [],      # 解锁可扮演的武将
            "unlocked_inheritance_skills": [],  # 永久解锁的传承技能
            "unlocked_talents": [],     # 解锁的天赋
            "unlocked_artifacts": [],   # 解锁的图鉴
            "史籍": [],                  # 已解锁的史籍
            "total_deaths": 0,
            "best_run_year": 0,
            "best_run_month": 0,
            "total_kills": 0,
        }

    def _load_history(self):
        """加载历史记录（史书记载片段）"""
        if os.path.exists(self.history_file):
            records = []
            with open(self.history_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        records.append(json.loads(line))
            return records[-100:]  # 只保留最近100条
        return []

    def add_history(self, record):
        """添加一条史书记载"""
        self.history.append(record)
        # 写入文件
        os.makedirs(os.path.dirname(self.history_file), exist_ok=True)
        with open(self.history_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
        # 只保留最近200条
        self.history = self.history[-200:]

    def record_death(self, player, cause, context=None):
        """记录一次死亡"""
        self.unlocks["total_deaths"] += 1

        record = {
            "type": "death_record",
            "year": context.get("year", 184) if context else 184,
            "month": context.get("month", 1) if context else 1,
            "player_name": player.name,
            "player_rank": player.rank,
            "death_cause": cause,
            "exp": player.exp,
            "kills": context.get("kills", 0) if context else 0,
            "location": player.location,
        }

        # 检查是否破了纪录
        elapsed = (context.get("year", 184) - 184) * 12 + context.get("month", 1) if context else 0
        best_elapsed = (self.unlocks.get("best_run_year", 184) - 184) * 12 + self.unlocks.get("best_run_month", 1)
        if elapsed > best_elapsed:
            self.unlocks["best_run_year"] = context.get("year", 184) if context else 184
            self.unlocks["best_run_month"] = context.get("month", 1) if context else 1

        self.add_history(record)
        self._save_unlocks()

        return record

    def unlock_hero(self, hero_name):
        """解锁新武将"""
        if hero_name not in self.unlocks["unlocked_heroes"]:
            self.unlocks["unlocked_heroes"].append(hero_name)
            self._save_unlocks()

    def unlock_skill(self, skill_name):
        """解锁传承技能"""
        if skill_name not in self.unlocks["unlocked_skills"]:
            self.unlocks["unlocked_skills"].append(skill_name)
            self._save_unlocks()

    def unlock_talent(self, talent_name):
        """解锁天赋"""
        if talent_name not in self.unlocks["unlocked_talents"]:
            self.unlocks["unlocked_talents"].append(talent_name)
            self._save_unlocks()

    def unlock_artwork(self, name):
        """解锁图鉴"""
        if name not in self.unlocks["unlocked_artifacts"]:
            self.unlocks["unlocked_artifacts"].append(name)
            self._save_unlocks()

    def unlock_history_book(self, book_name):
        """解锁史籍"""
        if book_name not in self.unlocks["史籍"]:
            self.unlocks["史籍"].append(book_name)
            self._save_unlocks()

    def _save_unlocks(self):
        os.makedirs(os.path.dirname(self.unlock_file), exist_ok=True)
        with open(self.unlock_file, "w", encoding="utf-8") as f:
            json.dump(self.unlocks, f, ensure_ascii=False, indent=2)

    def get_summary(self):
        """获取解锁进度摘要"""
        return {
            "可扮演武将": len(self.unlocks.get("unlocked_heroes", [])),
            "传承技能": len(self.unlocks.get("unlocked_skills", [])),
            "天赋": len(self.unlocks.get("unlocked_talents", [])),
            "图鉴": len(self.unlocks.get("unlocked_artifacts", [])),
            "史籍": len(self.unlocks.get("史籍", [])),
            "死亡次数": self.unlocks.get("total_deaths", 0),
            "最远到达": f"{self.unlocks.get('best_run_year', 184)}年{self.unlocks.get('best_run_month', 1)}月",
        }

    def print_summary(self):
        """打印解锁进度"""
        s = self.get_summary()
        lines = [
            "\n━━━ 解锁进度 ━━━",
            f"  可扮演武将: {s['可扮演武将']}个",
            f"  传承技能: {s['传承技能']}个",
            f"  天赋: {s['天赋']}个",
            f"  图鉴: {s['图鉴']}个",
            f"  史籍: {s['史籍']}部",
            f"  死亡次数: {s['死亡次数']}",
            f"  最远到达: {s['最远到达']}",
            "━━━━━━━━━━━━━━━━\n",
        ]
        return "\n".join(lines)