#!/usr/bin/env python3
"""快速测试"""
import sys
sys.path.insert(0, '/root/sanguo_roguelike')

import engine

e = engine.SanguoEngine()
e.new_game()

print("\n=== 测试 tick ===")
result = e.tick()
print("tick result:", result)

print("\n=== 测试第二次 tick ===")
result = e.tick()
print("tick result:", result)

print("\n=== 测试解锁系统 ===")
print(e.progression.print_summary())

print("\n✅ 核心模块测试通过")