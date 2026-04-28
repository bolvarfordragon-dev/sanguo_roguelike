"""
地图系统 - 十三州地理 + 移动
"""

# ============ 地图结构 ============
# 十三州 + 京兆（司隶）

REGIONS = {
    "司隶": {
        "name": "司隶",
        "cities": ["洛阳", "长安", "许昌", "陈留", "酸枣"],
        "description": "天下之中，汉室京畿",
        "adjacent": ["豫州", " "],  # 地理简化
    },
    "豫州": {
        "name": "豫州",
        "cities": ["颍川", "南阳", "汝南", "谯郡", "陈国"],
        "description": "中原腹地，黄巾渊薮",
        "adjacent": ["司隶", "兖州", "扬州", "荆州"],
    },
    "兖州": {
        "name": "兖州",
        "cities": ["濮阳", "东郡", "山阳", "济北", "泰山"],
        "description": "黄河之畔，战略要地",
        "adjacent": ["豫州", "徐州", "冀州", "青州"],
    },
    "徐州": {
        "name": "徐州",
        "cities": ["下邳", "琅琊", "东海", "广陵", "彭城"],
        "description": "江淮门户，工商繁荣",
        "adjacent": ["兖州", "扬州", "豫州"],
    },
    "扬州": {
        "name": "扬州",
        "cities": ["建业", "吴郡", "会稽", "庐江", "丹阳"],
        "description": "江东锦绣，鱼米之乡",
        "adjacent": ["徐州", "豫州", "荆州"],
    },
    "荆州": {
        "name": "荆州",
        "cities": ["襄阳", "江陵", "长沙", "零陵", "桂阳"],
        "description": "南北枢纽，用武之地",
        "adjacent": ["豫州", "扬州", "交州", "益州", "关中"],
    },
    "冀州": {
        "name": "冀州",
        "cities": ["邺城", "中山", "河间", "清河", "安平"],
        "description": "河北重镇，袁绍根基",
        "adjacent": ["兖州", "青州", "幽州", "并州"],
    },
    "幽州": {
        "name": "幽州",
        "cities": ["蓟县", "辽东", "右北平", "涿郡"],
        "description": "边塞苦寒，胡汉杂居",
        "adjacent": ["冀州", "并州"],
    },
    "并州": {
        "name": "并州",
        "cities": ["晋阳", "上党", "雁门", "太原"],
        "description": "山河表里，匈奴故地",
        "adjacent": ["冀州", "幽州", "司隶", "凉州"],
    },
    "青州": {
        "name": "青州",
        "cities": ["临菑", "济南", "东莱", "北海", "平原"],
        "description": "山东半岛，海岱之区",
        "adjacent": ["兖州", "冀州", "徐州"],
    },
    "益州": {
        "name": "益州",
        "cities": ["成都", "绵竹", "巴郡", "汉中", "梓潼"],
        "description": "天府之国，易守难攻",
        "adjacent": ["荆州", "凉州", "交州"],
    },
    "凉州": {
        "name": "凉州",
        "cities": ["姑臧", "安定", "北地", "天水", "武威"],
        "description": "河西走廊，羌戎之地",
        "adjacent": ["并州", "益州", "司隶"],
    },
    "雍州": {
        "name": "雍州",
        "cities": ["长安", "汜水关", "虎牢关", "武关"],
        "description": "关中四塞，秦汉故都",
        "adjacent": ["司隶", "凉州", "益州"],
    },
    "交州": {
        "name": "交州",
        "cities": ["番禺", "交趾", "苍梧", "郁林"],
        "description": "岭南边陲，瘴疠之地",
        "adjacent": ["荆州", "益州"],
    },
}

# 初始玩家位置
INITIAL_CITY = "颍川"
INITIAL_REGION = "豫州"

# 移动消耗
MOVE_COST_GOLD = 10    # 移动基本消耗
MOVE_COST_TIME = 1     # 移动消耗月数

# 城市之间的路径（简化）
CITY_CONNECTIONS = {
    "颍川": ["洛阳", "南阳", "汝南"],
    "洛阳": ["颍川", "长安", "陈留", "汜水关"],
    "陈留": ["洛阳", "濮阳", "酸枣"],
    "酸枣": ["陈留", "汜水关"],
    "汜水关": ["酸枣", "洛阳", "虎牢关"],
    "虎牢关": ["汜水关", "洛阳"],
    "南阳": ["颍川", "襄阳", "汝南"],
    "汝南": ["颍川", "南阳", "寿春"],
    "襄阳": ["南阳", "江陵", "长沙"],
    "江陵": ["襄阳", "长沙", "益州"],
    "长沙": ["江陵", "苍梧", "桂阳"],
    "涿郡": ["蓟县", "邺城"],
    "邺城": ["涿郡", "濮阳", "中山"],
    "濮阳": ["邺城", "陈留", "临菑"],
    "临菑": ["濮阳", "东莱", "平原"],
    "建业": ["吴郡", "会稽", "丹阳"],
    "吴郡": ["建业", "会稽"],
    "成都": ["绵竹", "巴郡", "汉中"],
}


def get_current_region(city):
    """根据城市反推所属州"""
    for region, data in REGIONS.items():
        if city in data["cities"]:
            return region
    return None


def get_adjacent_cities(city):
    """获取相邻城市列表"""
    return CITY_CONNECTIONS.get(city, [])


def get_region_cities(region):
    """获取某州所有城市"""
    return REGIONS.get(region, {}).get("cities", [])


def can_move_to(city):
    """检查是否可移动到某城市"""
    return city in CITY_CONNECTIONS


def get_move_info(from_city, to_city):
    """
    获取移动信息（消耗、可行性）
    返回: dict — {"can": bool, "cost": int, "time": int, "narrative": str}
    """
    if from_city == to_city:
        return {"can": False, "cost": 0, "time": 0, "narrative": "已在城中"}

    if to_city not in CITY_CONNECTIONS.get(from_city, []):
        return {"can": False, "cost": 0, "time": 0, "narrative": f"从{from_city}无法直达{to_city}"}

    return {
        "can": True,
        "cost": MOVE_COST_GOLD,
        "time": MOVE_COST_TIME,
        "narrative": f"从{from_city}前往{to_city}，需{MOVE_COST_TIME}月，耗金{MOVE_COST_GOLD}。"
    }


def format_map():
    """打印地图概览"""
    lines = ["\n【十三州地图】", "=" * 40]
    for region, data in REGIONS.items():
        cities_str = "、".join(data["cities"][:3])
        if len(data["cities"]) > 3:
            cities_str += "..."
        lines.append(f"{region}：{cities_str}")
        lines.append(f"  └ {data['description']}")
    lines.append("=" * 40)
    return "\n".join(lines)


def format_location_info(city, region=None):
    """格式化当前位置信息"""
    if region is None:
        region = get_current_region(city)
    region_data = REGIONS.get(region, {})
    desc = region_data.get("description", "")
    adj_cities = get_adjacent_cities(city)

    lines = [
        f"\n📍 {city}（{region}）",
        f"   {desc}",
        f"   相邻城市: {', '.join(adj_cities) if adj_cities else '无'}",
    ]
    return "\n".join(lines)


def travel_narrative(from_city, to_city):
    """生成旅途叙事"""
    narratives = [
        f"你收拾行装，从{from_city}出发，一路向东，{to_city}渐近。",
        f"离开{from_city}，踏上前往{to_city}的道路。沿途风景变换，偶见流民。",
        f"你骑马上路，经{from_city}向东而行，数日后{to_city}已在眼前。",
        f"自{from_city}启程，沿官道南下，{to_city}在望。",
    ]
    import random
    return random.choice(narratives)