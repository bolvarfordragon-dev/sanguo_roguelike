#!/usr/bin/env python3
"""
完整游戏流程模拟 - 模拟玩家做出选择，记录关键画面
"""
import sys
import random
sys.path.insert(0, '/root/sanguo_roguelike')

import engine

def simulate():
    random.seed(42)
    e = engine.SanguoEngine()
    e.new_game()

    print("\n" + "="*52)
    print("⚔️  三国文字Roguelike ⚔️")
    print("="*52)
    print(f"\n📅 {e.state.get_time_str()} | 📍 {e.state.player.location}")
    print(f"身份：{e.state.player.rank} | {e.state.player.name}")
    e.show_status()

    months = 0
    max_months = 60

    while e.running and months < max_months:
        result = e.tick()
        months += 1
        if result is None:
            print("\n💀 游戏结束")
            break

        p = e.state.player

        # === 战斗 ===
        if result.get('combat'):
            enemy = result['combat']['enemy']
            ctx = result['combat']['ctx']
            usable = e.get_active_skills_prompt()
            from combat import format_combat_intro

            print(f"\n{'='*52}")
            print(f"⚔️  战斗触发！")
            print(format_combat_intro(enemy, ctx, usable))

            # 自动选择：进攻
            res = e.resolve_combat_action('1')
            lines = res.split('\n')
            # 打印关键行
            for line in lines[-10:]:
                print(line)
            print(f"体力{p.stamina} 士气{p.morale} 金{p.gold} 粮{p.food}")
            continue

        # === NPC遭遇 ===
        if result.get('npc_encounter'):
            enc = result['npc_encounter']
            npc = enc['npc']
            from narrative import narrate_npc_encounter

            print(f"\n{'='*52}")
            print(f"🎭 NPC遭遇：{npc.name}")
            print(narrate_npc_encounter(npc))
            print(e.format_npc_encounter_options(npc))

            # 自动选择策略：非领袖尝试诚心招募，领袖用利诱
            from npc_schedule import is_faction_leader
            if is_faction_leader(npc.name):
                if p.gold >= 30:
                    success, msg = e._try_recruit_npc(npc, 'bribe')
                else:
                    success, msg = e._try_recruit_npc(npc, 'sincere')
            else:
                success, msg = e._try_recruit_npc(npc, 'sincere')
            print(msg)

            # 清理pending
            if e.pending_npc_encounter:
                e.pending_npc_encounter = None
            print(f"体力{p.stamina} 士气{p.morale} 金{p.gold} 粮{p.food}")
            continue

        # === 每月结果 ===
        parts = []
        if result.get('mandatory'):
            parts.append(f"📜 {result['mandatory']['name']}")
        for c in result.get('conditionals', []):
            parts.append(f"✨ {c.get('name','')[:20]}")

        ev_str = ' '.join(parts) if parts else '平静的一个月'
        print(f"\n{result['time']} | {ev_str}")
        print(f"体力{p.stamina} 士气{p.morale} 金{p.gold} 粮{p.food} | 碎片{p.inheritance_fragments}枚")

    # === 结局 ===
    print(f"\n{'='*52}")
    print(f"📊 游戏结束 — {e.state.get_time_str()}，存活{months}个月")
    p = e.state.player
    print(f"最终：体力{p.stamina} 士气{p.morale} 金{p.gold} 粮{p.food}")
    print(f"经验：{p.exp} | 官职：{p.rank}")
    print(f"主动技能：{[s for s in p.active_skills]}")
    print(f"被动技能：{[s for s in p.passive_skills]}")
    print(f"招募NPC：{[k[3:] for k in e.state.event_flags if k.startswith('已招募_')]}")
    print(f"碎片：{p.inheritance_fragments}枚")
    print(f"{'='*52}")

if __name__ == "__main__":
    simulate()