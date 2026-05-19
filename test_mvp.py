#!/usr/bin/env python3
"""
MVP 测试脚本（非交互版）- 模拟一局完整游戏的前2年
"""
import sys
import random
sys.path.insert(0, '/root/sanguo_roguelike')

import engine

def run_mvp():
    random.seed(12345)
    e = engine.SanguoEngine()
    e.new_game()

    print("=" * 50)
    print("⚔️  三国文字Roguelike MVP 自动测试")
    print("=" * 50)

    p = e.state.player
    print(f"\n📅 {e.state.get_time_str()} | 📍 {p.location}")
    print(f"身份：{p.rank} | {p.name}")
    print(f"属性：武{p.get_stat('武')} 智{p.get_stat('智')} 名{p.get_stat('名')} 魅{p.get_stat('魅')} 运{p.get_stat('运')}")
    print(f"资源：体力{p.stamina} 士气{p.morale} 金{p.gold} 粮{p.food}")

    months = 0
    combats = 0; wins = 0; npc_meets = 0; fragments = 0

    # 模拟24个月
    for i in range(24):
        result = e.tick()
        months += 1
        if result is None:
            print(f"\n💀 游戏结束")
            break

        p = e.state.player

        # 战斗
        if result.get('combat'):
            combats += 1
            enemy = result['combat']['enemy']
            # 自动选进攻
            res = e.resolve_combat_action('1')
            if '大胜' in res or '胜利' in res: wins += 1
            if '碎片' in res: fragments += 1
            print(f"{result['time']} ⚔️ {enemy.name} → {'胜' if wins else '负'} | "
                  f"体力{p.stamina} 金{p.gold} 粮{p.food} 碎片{p.inheritance_fragments}")
            continue

        # NPC
        if result.get('npc_encounter'):
            npc_meets += 1
            enc = result['npc_encounter']
            e.handle_npc_encounter('7')  # 离开
            print(f"{result['time']} 🎭 {enc['npc_name']} → 离开")
            continue

        # 事件
        ev_parts = []
        if result.get('mandatory'):
            ev_parts.append(f"📜{result['mandatory']['name']}")
        for c in result.get('conditionals', []):
            ev_parts.append(f"✨{c.get('name','')[:12]}")
        ev_str = ' '.join(ev_parts)
        print(f"{result['time']} | {p.location[:4]} | 体力{p.stamina} 士气{p.morale} 金{p.gold} 粮{p.food} | {ev_str}")

    # 结局
    print(f"\n{'='*50}")
    print(f"📊 MVP 测试结果（{months}个月）")
    print(f"  ⚔️ 战斗: {combats}场 (胜{wins}负{combats-wins})")
    print(f"  🎭 NPC相遇: {npc_meets}次")
    print(f"  🔮 碎片: {p.inheritance_fragments}枚")
    print(f"  💰 金: {p.gold} | 🍚 粮: {p.food}")
    print(f"  📈 经验: {p.exp} | 官职: {p.rank}")
    print(f"  🎒 主动技能: {p.active_skills}")
    print(f"  🛡️ 被动技能: {p.passive_skills}")
    print(f"{'='*50}")

if __name__ == "__main__":
    run_mvp()