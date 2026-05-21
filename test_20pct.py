#!/usr/bin/env python3
"""快速测试脚本 - 20%遭遇率统计"""
import random, sys, os, json
sys.path.insert(0, '/root/sanguo_roguelike')
import engine
from config import END_YEAR

# 清空转世文件
reinc_file = 'sanguo_roguelike/reincarnation.json'
if os.path.exists(reinc_file):
    os.remove(reinc_file)

reached_220 = 0
died_count = 0

for seed in range(1, 201):
    random.seed(seed)
    e = engine.SanguoEngine(silent=True)
    e.new_game()
    
    lives = 0
    while e.running and lives < 100:
        result = e.tick()
        if result is None:
            months = (e.state.year - 184) * 12 + e.state.month
            if e.state.year >= END_YEAR:
                reached_220 += 1
                break
            else:
                # 死亡 - 直接保存业力
                died_count += 1
                lives += 1
                # 手动保存业力
                karma_data = e._load_reincarnation()
                karma_data["total_deaths"] = karma_data.get("total_deaths", 0) + 1
                player_karma = karma_data.setdefault("karma", {})
                from config import REINCARNATION_CARRY_RATES, REINCARNATION_CAPS
                karma_gain = []
                for stat in ["武", "智", "名", "魅", "运"]:
                    died_value = e.state.player.stats.get(stat, 0)
                    carry = int(died_value * REINCARNATION_CARRY_RATES.get(stat, 0))
                    if carry > 0:
                        cap = REINCARNATION_CAPS.get(stat, 20)
                        before = player_karma.get(stat, 0)
                        player_karma[stat] = min(cap, before + carry)
                        karma_gain.append(f"{stat}+{carry}")
                if karma_gain:
                    e._save_reincarnation(karma_data)
                # 重开
                e.new_game()
            continue
        
        if result.get('combat') and e.pending_combat is not None:
            e.resolve_combat_action('1')
        
        months = (e.state.year - 184) * 12 + e.state.month
        if months > 500:
            reached_220 += 1
            break

rd = {"total_deaths": 0}
if os.path.exists(reinc_file):
    with open(reinc_file) as f:
        rd = json.load(f)

print(f'=== 20%遭遇率（200次模拟）===')
print(f'寿终220年：{reached_220}/200 = {reached_220/2}%')
print(f'总死亡次数：{died_count}')
print(f'转世记录：{rd.get("total_deaths", 0)}')