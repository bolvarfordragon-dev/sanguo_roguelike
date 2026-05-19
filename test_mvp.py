#!/usr/bin/env python3
"""Minimal MVP test"""
import sys
import random
sys.path.insert(0, '/root/sanguo_roguelike')

import engine

random.seed(42)
e = engine.SanguoEngine()
e.new_game()

print("=" * 52)
print("⚔️  三国文字Roguelike MVP Test ⚔️")
print("=" * 52)
print(f"\n📅 {e.state.get_time_str()} | 📍 {e.state.player.location}")
e.show_status()

months = 0
max_months = 48
results = []

while e.running and months < max_months:
    result = e.tick()
    months += 1
    
    if result is None:
        print(f"\n💀 游戏结束 (存活 {months} 个月)")
        break

    p = e.state.player
    
    # Combat
    if result.get('combat'):
        enemy = result['combat']['enemy']
        ctx = result['combat']['ctx']
        usable = e.get_active_skills_prompt()
        from combat import format_combat_intro
        print(f"\n⚔️  战斗: {enemy.name} (武力{enemy.get_stat('武')}, {enemy.troops}兵)")
        if usable:
            print(f"  可用技能: {', '.join(s for s,_ in usable)}")
        print(f"  选择: 进攻")
        res = e.resolve_combat_action('1')
        print("  结果:", [l for l in res.split('\n') if l.strip()][-1])

    # NPC encounter
    if result.get('npc_encounter'):
        npc = result['npc_encounter']['npc']
        print(f"\n🎭 NPC遭遇: {npc.name} ({npc.rank}) - {npc.faction}")
        print(engine.format_npc_encounter_options(npc).strip())
        # Try recruit with option 1
        print("  选择: 诚心相邀 (选项1)")
        res = e.try_recruit_npc(npc, '1')
        if res:
            print(f"  结果: {res[:100]}")

    # Mandatory events
    if result.get('mandatory'):
        ev = result['mandatory']
        print(f"\n⚔️ 【必然事件】{ev['name']}")

    # Monthly summary every 6 months
    if months % 6 == 0:
        print(f"\n--- {months}个月小结 ---")
        print(f"  📍 {p.location} | 💰{p.gold}金 | 🍚{p.food}粮 | ⚡{p.stamina}体力 | 💨{p.morale}士气")
        print(f"  📊 武力{p.get_stat('武')} 智谋{p.get_stat('智')} 名声{p.get_stat('名')} 魅力{p.get_stat('魅')} 运气{p.get_stat('运')}")
        print(f"  🎒 技能: 主动{len(p.active_skills)} 被动{len(p.passive_skills)} 碎片{p.inheritance_fragments}")
        if p.rank != '散兵':
            print(f"  🏅 等级: {p.rank}")

print(f"\n{'='*52}")
print("✅ MVP测试完成")
stats = e.progression.print_summary()
print(stats)