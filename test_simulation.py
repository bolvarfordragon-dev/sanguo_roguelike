#!/usr/bin/env python3
"""测试脚本 - 200次模拟统计（修复版）"""
import random, sys, json, os

sys.path.insert(0, '/root/sanguo_roguelike')
import engine
from config import START_YEAR, END_YEAR

reached_220 = 0
died_early = 0

for seed in range(1, 201):
    random.seed(seed)
    e = engine.SanguoEngine(silent=True)
    e.new_game()
    
    while e.running:
        result = e.tick()
        if result is None:
            # 游戏结束
            if e.state.year >= END_YEAR:
                reached_220 += 1
            else:
                died_early += 1
                # 调用死亡界面以保存转世数据
                months = (e.state.year - START_YEAR) * 12 + e.state.month
                fragments = 5 + ((months + 5) // 6)
                e.show_death_screen(fragments, months)
            break
        
        if result.get('combat') and e.pending_combat is not None:
            e.resolve_combat_action('1')
        
        # 安全检查：最多跑36年
        months = (e.state.year - START_YEAR) * 12 + e.state.month
        if months > 450:  # 37.5年
            reached_220 += 1
            break

reinc_file = 'sanguo_roguelike/reincarnation.json'
total_deaths = 0
if os.path.exists(reinc_file):
    with open(reinc_file) as f:
        rd = json.load(f)
    total_deaths = rd.get('total_deaths', 0)

print(f'=== 200次模拟统计 ===')
print(f'跑完36年到220年（寿终）：{reached_220}/200 = {reached_220/2}%')
print(f'中途死亡：{died_early}/200 = {died_early/2}%')
print(f'转世记录的总死亡次数：{total_deaths}')