#!/usr/bin/env python3
"""Test 100 runs to collect statistics."""
import sys
import os
import random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine import SanguoEngine

def run_one(seed=None):
    if seed is not None:
        random.seed(seed)
    e = SanguoEngine(silent=True)
    e.new_game()
    months = 0
    battles = 0
    npc_recruited = 0
    highest_rank = e.state.player.rank
    death_by_hp = False
    while not e.state.is_game_over():
        result = e.tick()
        months += 1
        if result and result.get("combat"):
            battles += 1
        if e.state.player.rank != highest_rank:
            highest_rank = e.state.player.rank
        if months > 2400:
            break
    death_by_hp = e.state.player.hp <= 0
    return {
        "survived": months,
        "battles": battles,
        "death_by_hp": death_by_hp,
        "highest_rank": highest_rank,
        "npc_recruited": sum(1 for k in e.state.event_flags if k.startswith("已招募_")),
    }

def main():
    seeds = list(range(1, 101))
    results = []
    for i, seed in enumerate(seeds):
        r = run_one(seed)
        results.append(r)
        print(f"[{i+1}/100] seed={seed}: {r['survived']}月 rank={r['highest_rank']} battles={r['battles']} hp_death={r['death_by_hp']}")

    total = len(results)
    deaths = sum(1 for r in results if r['death_by_hp'])
    survived = total - deaths
    avg_months = sum(r['survived'] for r in results) / total
    avg_battles = sum(r['battles'] for r in results) / total
    avg_npc = sum(r['npc_recruited'] for r in results) / total
    max_months = max(r['survived'] for r in results)
    min_months = min(r['survived'] for r in results)

    print("\n" + "="*50)
    print("100次模拟统计")
    print("="*50)
    print(f"存活率: {survived}/{total} ({survived/total*100:.1f}%)")
    print(f"平均存活月数: {avg_months:.1f} (min={min_months}, max={max_months})")
    print(f"平均战斗次数: {avg_battles:.1f}")
    print(f"平均招募NPC: {avg_npc:.1f}")

    # Rank distribution
    from collections import Counter
    rank_counts = Counter(r['highest_rank'] for r in results)
    print("\n最高官职分布:")
    for rank, count in sorted(rank_counts.items()):
        print(f"  {rank}: {count}次")

    # HP death vs year limit death
    hp_deaths = sum(1 for r in results if r['death_by_hp'])
    year_deaths = sum(1 for r in results if not r['death_by_hp'])
    print(f"\n死因: HP死亡={hp_deaths} 时间到={year_deaths}")

if __name__ == "__main__":
    main()