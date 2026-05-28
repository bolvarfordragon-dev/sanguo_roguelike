import sys, os, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from engine import SanguoEngine

results = []
for seed in range(1, 101):
    e = SanguoEngine(silent=True)
    e.new_game()
    months, battles = 0, 0
    while not e.state.is_game_over() and months < 2400:
        # Advance one month
        res = e.tick()
        months += 1
        if res and res.get("combat"):
            battles += 1
        # Auto-resolve combat if pending (use tactic 1 = normal attack)
        if e.pending_combat:
            # Pick best tactic: find tactic with highest win_rate_mod
            from combat import COMBAT_ACTIONS
            best = max(COMBAT_ACTIONS.items(), key=lambda x: x[1]["win_rate_mod"])
            e.resolve_combat_action(best[0])
            e.pending_combat = None
    results.append((months, e.state.player.rank, battles, e.state.player.hp <= 0))
    print(f"{seed}: {months}月 {e.state.player.rank} battles={battles} death={'HP' if e.state.player.hp<=0 else 'time'}")

total = len(results)
hp_deaths = sum(1 for r in results if r[3])
from collections import Counter
rank_ct = Counter(r[1] for r in results)
print(f"\n存活率: {total-hp_deaths}/{total} ({(total-hp_deaths)/total*100:.1f}%)")
print(f"平均月数: {sum(r[0] for r in results)/total:.1f}")
print(f"平均战斗: {sum(r[2] for r in results)/total:.1f}")
print(f"官职分布: {dict(sorted(rank_ct.items()))}")
print(f"HP死亡: {hp_deaths} 时间到: {total-hp_deaths}")