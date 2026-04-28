"""NPC 相遇系统整合测试"""
import sys
sys.path.insert(0, '/root/sanguo_roguelike')

from npc_schedule import get_npc_location, is_npc_active, is_faction_leader
from engine import SanguoEngine


def test_关羽时空():
    assert is_npc_active("关羽", 159) == False  # 出生前
    assert is_npc_active("关羽", 160) == True   # 出生年
    assert is_npc_active("关羽", 184) == True
    assert is_npc_active("关羽", 220) == True   # 死亡年
    assert is_npc_active("关羽", 221) == False  # 死后
    assert get_npc_location("关羽", 184) == "涿郡"
    assert get_npc_location("关羽", 208) == "江陵"
    assert get_npc_location("关羽", 219) == "江陵"
    assert get_npc_location("关羽", 220) == "麦城"
    assert get_npc_location("关羽", 221) is None
    print("✅ 关羽时空测试通过")


def test_曹操时空():
    assert is_npc_active("曹操", 184) == True
    assert is_npc_active("曹操", 220) == True
    assert is_npc_active("曹操", 221) == False
    assert get_npc_location("曹操", 184) == "洛阳"
    assert get_npc_location("曹操", 208) == "江陵"
    assert get_npc_location("曹操", 200) == "许昌"
    print("✅ 曹操时空测试通过")


def test_诸葛亮时空():
    assert is_npc_active("诸葛亮", 180) == False
    assert is_npc_active("诸葛亮", 181) == True
    assert is_npc_active("诸葛亮", 234) == True
    assert is_npc_active("诸葛亮", 235) == False
    assert get_npc_location("诸葛亮", 180) is None
    assert get_npc_location("诸葛亮", 181) == "南阳"
    assert get_npc_location("诸葛亮", 209) == "江陵"
    print("✅ 诸葛亮时空测试通过")


def test_司马师不出现():
    assert is_npc_active("司马师", 184) == False
    assert get_npc_location("司马师", 184) is None
    print("✅ 司马师时空测试通过（184年不存在）")


def test_阵营领袖():
    assert is_faction_leader("刘备") == True
    assert is_faction_leader("曹操") == True
    assert is_faction_leader("关羽") == False
    assert is_faction_leader("周瑜") == False
    print("✅ 阵营领袖测试通过")


def test_周瑜赤壁位置():
    assert get_npc_location("周瑜", 208) == "江陵"
    assert get_npc_location("周瑜", 209) == "江陵"
    assert is_npc_active("周瑜", 210) == True
    assert is_npc_active("周瑜", 211) == False
    print("✅ 周瑜时空测试通过")


def test_刘备赤壁():
    assert get_npc_location("刘备", 208) == "荆州"
    assert get_npc_location("刘备", 209) == "江陵"
    print("✅ 刘备赤壁位置测试通过")


def test_engine_encounter_trigger():
    engine = SanguoEngine()
    engine.new_game()
    engine.state.player.location = "涿郡"
    engine.state.year = 184

    candidates = []
    for npc_name, npc in engine.state.npcs.items():
        if npc.hp <= 0:
            continue
        if not is_npc_active(npc_name, 184):
            continue
        if engine.state.event_flags.get(f"已招募_{npc_name}", False):
            continue
        npc_loc = get_npc_location(npc_name, 184)
        if npc_loc == "涿郡":
            candidates.append(npc_name)

    assert "刘备" in candidates, f"刘备应该在涿郡@184，实际候选: {candidates}"
    assert "关羽" in candidates
    assert "张飞" in candidates
    print(f"✅ 引擎遭遇触发测试通过（184年涿郡候选: {candidates}）")


def test_no_anachronisms():
    for name in ["刘备", "关羽", "张飞", "曹操", "孙坚", "董卓"]:
        assert is_npc_active(name, 184), f"{name} 应该在184年活跃"
    for name in ["司马师", "司马昭", "邓艾", "钟会", "姜维"]:
        active = is_npc_active(name, 184)
        assert not active, f"{name} 184年不应该存在，但is_active={active}"
    print("✅ 无时代错误测试通过")


if __name__ == "__main__":
    test_关羽时空()
    test_曹操时空()
    test_诸葛亮时空()
    test_司马师不出现()
    test_阵营领袖()
    test_周瑜赤壁位置()
    test_刘备赤壁()
    test_engine_encounter_trigger()
    test_no_anachronisms()
    print("\n🎉 所有测试通过！NPC相遇系统就绪。")
