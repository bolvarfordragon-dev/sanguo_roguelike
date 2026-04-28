#!/usr/bin/env python3
"""三国Roguelike - 快速体验脚本"""
import sys
sys.path.insert(0, '/root/sanguo_roguelike')

from engine import SanguoEngine
from narrative import format_event_intro

def run():
    e = SanguoEngine()
    e.new_game()

    print("\n🎮 测试模式：自动运行3个月")
    print("=" * 40)

    for i in range(3):
        print(f"\n>>> 推进时间...")
        result = e.tick()

        time_str = e.state.get_time_str()
        print(f"\n📅 {time_str}")
        print(f"   位置: {e.state.player.location} | 职务: {e.state.player.rank}")
        print(f"   气血: {e.state.player.hp} | 士气: {e.state.player.morale} | 体力: {e.state.player.stamina}")
        print(f"   金: {e.state.player.gold} | 粮: {e.state.player.food} | 经验: {e.state.player.exp}")
        print(f"   武: {e.state.player.get_stat('武')} | 智: {e.state.player.get_stat('智')} | 名: {e.state.player.get_stat('名')} | 魅: {e.state.player.get_stat('魅')} | 运: {e.state.player.get_stat('运')}")

        # 检查事件
        if result:
            if result.get("mandatory"):
                evt = result["mandatory"]
                print(f"\n⚔️ 【必然事件】{evt['name']}")
                print(evt['desc'][:100] + "...")
            if result.get("conditionals"):
                for c in result["conditionals"]:
                    print(f"\n✨ 【条件事件】{c.get('name', '未知')}")

    print("\n" + "=" * 40)
    print("✅ 自动测试完成")

    # 测试战斗
    print("\n⚔️ 测试战斗系统...")
    from combat import simulate_combat
    from character import NPC

    enemy = NPC.from_preset("华雄")
    ctx = {
        "attacker_troops": 200,
        "defender_troops": 300,
        "terrain": "汜水关",
        "weather": "晴",
        "attacker_morale": 80,
        "defender_morale": 75,
    }
    result = simulate_combat(e.state.player, enemy, ctx)
    print(f"\n战斗结果: {'我方胜利' if result.winner == e.state.player else '我方失败'}")
    print(f"回合数: {result.rounds}")
    print(f"我军伤亡: {result.damages['winner_damage']} | 敌军伤亡: {result.damages['loser_damage']}")
    print("\n战斗叙事:")
    for part in result.narrative_parts:
        print(f"  {part}")

    print("\n" + "=" * 40)
    print("🎮 游戏测试完毕！")
    print(f"\n📊 当前进度: {e.progression.print_summary()}")

if __name__ == "__main__":
    run()