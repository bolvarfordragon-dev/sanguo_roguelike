"""
NPC 时空调量数据
历史准确的 NPC 遭遇系统数据源
"""

# NPC_SCHEDULE 格式：
# {
#     "NPC名": {
#         "active_years": [出生年, 死亡年],
#         "home_base": "常驻据点",
#         "timeline": [
#             {
#                 "years": [start_year, end_year],
#                 "location": "城市名",
#                 "event": "事件描述（可选）"
#             }
#         ],
#         "is_faction_leader": bool,
#     }
# }

NPC_SCHEDULE = {

    # ========== 蜀汉 ==========

    "关羽": {
        "active_years": [160, 220],
        "home_base": "涿郡",
        "timeline": [
            {"years": [160, 184], "location": "涿郡", "event": "早年生平，杀人亡命"},
            {"years": [184, 189], "location": "涿郡", "event": "黄巾之乱，从军镇压"},
            {"years": [189, 200], "location": "许昌", "event": "依附曹操，被封为汉寿亭侯"},
            {"years": [200, 201], "location": "汝南", "event": "千里走单骑，过五关斩六将"},
            {"years": [201, 207], "location": "荆州", "event": "依附刘备，驻守新野"},
            {"years": [208, 211], "location": "江陵", "event": "赤壁之战，镇守江陵"},
            {"years": [211, 219], "location": "江陵", "event": "镇守荆州，水淹七军"},
            {"years": [219, 220], "location": "麦城", "event": "败走麦城，被擒身亡"},
        ],
        "is_faction_leader": False,
    },

    "张飞": {
        "active_years": [165, 221],
        "home_base": "涿郡",
        "timeline": [
            {"years": [165, 184], "location": "涿郡", "event": "早年生平"},
            {"years": [184, 191], "location": "涿郡", "event": "黄巾之乱，随刘备征战"},
            {"years": [191, 201], "location": "荆州", "event": "依附刘表，驻守新野"},
            {"years": [201, 211], "location": "江陵", "event": "赤壁后随刘备入蜀"},
            {"years": [211, 214], "location": "成都", "event": "协助刘备平定益州"},
            {"years": [214, 221], "location": "江陵", "event": "镇守荆州后被部下所杀"},
        ],
        "is_faction_leader": False,
    },

    "刘备": {
        "active_years": [161, 223],
        "home_base": "涿郡",
        "timeline": [
            {"years": [161, 183], "location": "涿郡", "event": "早年生平，织席贩履"},
            {"years": [184, 186], "location": "涿郡", "event": "黄巾之乱后四处征战"},
            {"years": [186, 189], "location": "涿郡", "event": "因功封安喜尉"},
            {"years": [189, 193], "location": "洛阳", "event": "讨伐董卓，参与酸枣会盟"},
            {"years": [193, 199], "location": "北海", "event": "依附公孙瓒，驻守平原"},
            {"years": [199, 201], "location": "汝南", "event": "依附袁绍，官渡前夕"},
            {"years": [201, 207], "location": "荆州", "event": "依附刘表，三顾茅庐"},
            {"years": [208, 210], "location": "江陵", "event": "赤壁之战，借南郡"},
            {"years": [211, 214], "location": "成都", "event": "入蜀，接管益州"},
            {"years": [214, 219], "location": "成都", "event": "汉中之战，自立汉中王"},
            {"years": [219, 221], "location": "成都", "event": "称帝，建立蜀汉"},
            {"years": [221, 222], "location": "江陵", "event": "夷陵之战，败退永安"},
            {"years": [222, 223], "location": "永安", "event": "病逝于永安"},
        ],
        "is_faction_leader": True,
    },

    "赵云": {
        "active_years": [162, 229],
        "home_base": "涿郡",
        "timeline": [
            {"years": [162, 191], "location": "涿郡", "event": "早年生平"},
            {"years": [191, 201], "location": "邺城", "event": "依附袁绍，后离去"},
            {"years": [201, 207], "location": "荆州", "event": "依附刘备"},
            {"years": [208, 211], "location": "江陵", "event": "赤壁之战，长坂坡护主"},
            {"years": [211, 214], "location": "成都", "event": "随刘备入蜀"},
            {"years": [214, 229], "location": "江陵", "event": "镇守荆州，随诸葛亮北伐，病逝"},
        ],
        "is_faction_leader": False,
    },

    "诸葛亮": {
        "active_years": [181, 234],
        "home_base": "南阳",
        "timeline": [
            {"years": [181, 207], "location": "南阳", "event": "躬耕陇亩，博览群书"},
            {"years": [208, 211], "location": "江陵", "event": "赤壁之战，联吴抗曹"},
            {"years": [211, 214], "location": "成都", "event": "随刘备入蜀"},
            {"years": [214, 221], "location": "江陵", "event": "镇守荆州，处理内政"},
            {"years": [221, 223], "location": "成都", "event": "刘备托孤，辅佐刘禅"},
            {"years": [223, 227], "location": "成都", "event": "休养生息，整顿内政"},
            {"years": [228, 229], "location": "汉中", "event": "第一次北伐"},
            {"years": [229, 230], "location": "汉中", "event": "第二、三次北伐"},
            {"years": [230, 231], "location": "汉中", "event": "第四次北伐"},
            {"years": [231, 234], "location": "汉中", "event": "第五次北伐，病逝五丈原"},
        ],
        "is_faction_leader": False,
    },

    # ========== 曹魏 ==========

    "曹操": {
        "active_years": [155, 220],
        "home_base": "陈留",
        "timeline": [
            {"years": [155, 174], "location": "陈留", "event": "早年生平"},
            {"years": [174, 184], "location": "洛阳", "event": "任洛阳北部尉，济南相"},
            {"years": [184, 189], "location": "陈留", "event": "黄巾之乱，佐骑都尉"},
            {"years": [189, 192], "location": "陈留", "event": "讨董卓，参与酸枣会盟"},
            {"years": [192, 196], "location": "濮阳", "event": "收编黄巾，兖州牧"},
            {"years": [196, 200], "location": "许昌", "event": "迎献帝，挟天子以令诸侯"},
            {"years": [200, 207], "location": "许昌", "event": "官渡之战，大破袁绍"},
            {"years": [208, 210], "location": "江陵", "event": "赤壁之战，大败于周瑜"},
            {"years": [210, 215], "location": "许昌", "event": "平定马超，统一北方"},
            {"years": [215, 219], "location": "许昌", "event": "汉中之战，进爵魏王"},
            {"years": [219, 220], "location": "许昌", "event": "进封魏王，病逝"},
        ],
        "is_faction_leader": True,
    },

    "吕布": {
        "active_years": [161, 198],
        "home_base": "涿郡",
        "timeline": [
            {"years": [161, 189], "location": "涿郡", "event": "早年生平，拜丁原为义父"},
            {"years": [189, 192], "location": "洛阳", "event": "杀丁原，依附董卓"},
            {"years": [192, 196], "location": "长安", "event": "与王允合谋杀董卓，后出奔"},
            {"years": [196, 198], "location": "下邳", "event": "占据徐州，被曹操围困"},
            {"years": [198, 198], "location": "下邳", "event": "兵败被擒，被杀"},
        ],
        "is_faction_leader": False,
    },

    "华雄": {
        "active_years": [156, 191],
        "home_base": "酸枣",
        "timeline": [
            {"years": [156, 189], "location": "酸枣", "event": "早年生平"},
            {"years": [189, 191], "location": "酸枣", "event": "董卓部下，校尉"},
            {"years": [191, 191], "location": "汜水关", "event": "汜水关被孙坚斩杀"},
        ],
        "is_faction_leader": False,
    },

    "颜良": {
        "active_years": [158, 200],
        "home_base": "邺城",
        "timeline": [
            {"years": [158, 190], "location": "邺城", "event": "早年生平"},
            {"years": [190, 200], "location": "邺城", "event": "袁绍部下名将"},
            {"years": [200, 200], "location": "白马", "event": "官渡之战，被关羽斩杀"},
        ],
        "is_faction_leader": False,
    },

    "文丑": {
        "active_years": [157, 200],
        "home_base": "邺城",
        "timeline": [
            {"years": [157, 190], "location": "邺城", "event": "早年生平"},
            {"years": [190, 200], "location": "邺城", "event": "袁绍部下名将"},
            {"years": [200, 200], "location": "白马", "event": "官渡之战，遭曹军击败身亡"},
        ],
        "is_faction_leader": False,
    },

    "袁绍": {
        "active_years": [131, 202],
        "home_base": "邺城",
        "timeline": [
            {"years": [131, 180], "location": "邺城", "event": "早年生平，累世公卿"},
            {"years": [180, 190], "location": "邺城", "event": "司隶校尉，参与党锢之祸"},
            {"years": [190, 200], "location": "邺城", "event": "讨董卓，十八路诸侯盟主"},
            {"years": [200, 202], "location": "黎阳", "event": "官渡大败，忧愤而亡"},
        ],
        "is_faction_leader": False,
    },

    "董卓": {
        "active_years": [138, 192],
        "home_base": "洛阳",
        "timeline": [
            {"years": [138, 184], "location": "洛阳", "event": "早年生平，任凉州刺使"},
            {"years": [184, 189], "location": "长安", "event": "平定凉州羌乱"},
            {"years": [189, 192], "location": "洛阳", "event": "擅权废立，迁都长安"},
            {"years": [192, 192], "location": "长安", "event": "被王允设计诛杀"},
        ],
        "is_faction_leader": False,
    },

    # ========== 江东 ==========

    "孙坚": {
        "active_years": [155, 191],
        "home_base": "长沙",
        "timeline": [
            {"years": [155, 184], "location": "长沙", "event": "早年生平，长沙太守"},
            {"years": [184, 189], "location": "长沙", "event": "黄巾之乱，镇压区星"},
            {"years": [189, 190], "location": "洛阳", "event": "讨董卓，率先攻入洛阳"},
            {"years": [191, 191], "location": "汝南", "event": "与刘表交战，战死"},
        ],
        "is_faction_leader": False,
    },

    "孙策": {
        "active_years": [175, 200],
        "home_base": "吴郡",
        "timeline": [
            {"years": [175, 191], "location": "长沙", "event": "早年生平，随父征战"},
            {"years": [191, 194], "location": "扬州", "event": "寓居江淮，投奔袁术"},
            {"years": [194, 200], "location": "吴郡", "event": "平定江东，奠定基业"},
            {"years": [200, 200], "location": "吴郡", "event": "遭刺杀重伤而亡"},
        ],
        "is_faction_leader": False,
    },

    "周瑜": {
        "active_years": [175, 210],
        "home_base": "吴郡",
        "timeline": [
            {"years": [175, 190], "location": "吴郡", "event": "早年生平，与孙策结交"},
            {"years": [190, 200], "location": "吴郡", "event": "辅佐孙策，平定江东"},
            {"years": [200, 207], "location": "吴郡", "event": "孙策死后，辅佐孙权"},
            {"years": [208, 209], "location": "江陵", "event": "赤壁之战，火烧曹军"},
            {"years": [209, 210], "location": "江陵", "event": "取南郡，病逝"},
        ],
        "is_faction_leader": False,
    },
    "江湖游侠": {
        "active_years": [175, 195],
        "home_base": "颍川",
        "timeline": [
            {"years": [175, 184], "location": "颍川", "event": "游侠江湖"},
            {"years": [184, 190], "location": "颍川", "event": "与刘备结交"},
            {"years": [190, 195], "location": "洛阳", "event": "讨董战场"},
        ],
        "is_faction_leader": False,
    },
        "太史慈": {
        "active_years": [195, 206],
        "home_base": "东莱",
        "timeline": [
            {"years": [195, 200], "location": "扬州", "event": "追随刘繇"},
            {"years": [200, 208], "location": "江夏", "event": "孙策部下"},
            {"years": [208, 215], "location": "吴郡", "event": "孙权部下"},
            {"years": [215, 206], "location": "南郡", "event": "征战荆州"},
        ],
        "is_faction_leader": False,
    },
    "甘宁": {
        "active_years": [195, 222],
        "home_base": "江夏",
        "timeline": [
            {"years": [195, 208], "location": "江夏", "event": "依附刘表"},
            {"years": [208, 215], "location": "江夏", "event": "归孙权"},
            {"years": [215, 222], "location": "江陵", "event": "征战荆益"},
        ],
        "is_faction_leader": False,
    },
    "魏延": {
        "active_years": [208, 234],
        "home_base": "义阳",
        "timeline": [
            {"years": [208, 211], "location": "荆州", "event": "入蜀"},
            {"years": [211, 219], "location": "成都", "event": "刘备部下"},
            {"years": [219, 234], "location": "汉中", "event": "诸葛亮北伐"},
        ],
        "is_faction_leader": False,
    },
    "张辽": {
        "active_years": [189, 222],
        "home_base": "雁门",
        "timeline": [
            {"years": [189, 198], "location": "洛阳", "event": "丁原/董卓/吕布部下"},
            {"years": [198, 207], "location": "徐州", "event": "吕布部下"},
            {"years": [207, 222], "location": "许昌", "event": "曹操部下"},
        ],
        "is_faction_leader": False,
    },
    "徐晃": {
        "active_years": [197, 227],
        "home_base": "杨县",
        "timeline": [
            {"years": [197, 204], "location": "洛阳", "event": "杨奉部下"},
            {"years": [204, 227], "location": "许昌", "event": "曹操部下"},
        ],
        "is_faction_leader": False,
    },
    "张郃": {
        "active_years": [200, 231],
        "home_base": "河间",
        "timeline": [
            {"years": [200, 207], "location": "邺城", "event": "袁绍部下"},
            {"years": [207, 231], "location": "许昌", "event": "曹操下部"},
        ],
        "is_faction_leader": False,
    },
    "黄忠": {
        "active_years": [208, 220],
        "home_base": "南阳",
        "timeline": [
            {"years": [208, 211], "location": "长沙", "event": "刘表下部"},
            {"years": [211, 214], "location": "成都", "event": "入蜀"},
            {"years": [214, 220], "location": "成都", "event": "刘备下部"},
        ],
        "is_faction_leader": False,
    },
    "马超": {
        "active_years": [196, 222],
        "home_base": "扶风",
        "timeline": [
            {"years": [196, 211], "location": "西凉", "event": "马腾下部"},
            {"years": [211, 214], "location": "汉中", "event": "张鲁下部"},
            {"years": [214, 222], "location": "成都", "event": "刘备下部"},
        ],
        "is_faction_leader": False,
    },
    "庞德": {
        "active_years": [195, 219],
        "home_base": "南安",
        "timeline": [
            {"years": [195, 209], "location": "长安", "event": "马腾下部"},
            {"years": [209, 219], "location": "樊城", "event": "曹操下部"},
        ],
        "is_faction_leader": False,
    },
    "鲁肃": {
        "active_years": [200, 217],
        "home_base": "临淮",
        "timeline": [
            {"years": [200, 208], "location": "吴郡", "event": "周瑜友人"},
            {"years": [208, 217], "location": "吴郡", "event": "孙权谋士"},
        ],
        "is_faction_leader": False,
    },
    "陆逊": {
        "active_years": [204, 245],
        "home_base": "吴郡",
        "timeline": [
            {"years": [204, 219], "location": "吴郡", "event": "孙权下部"},
            {"years": [219, 222], "location": "江陵", "event": "荆州太守"},
            {"years": [222, 245], "location": "吴郡", "event": "丞粵"},
        ],
        "is_faction_leader": False,
    },
    "司马懿": {
        "active_years": [208, 251],
        "home_base": "河内",
        "timeline": [
            {"years": [208, 220], "location": "许昌", "event": "曹操司空府"},
            {"years": [220, 239], "location": "洛阳", "event": "曹丕/曹叡信任"},
            {"years": [239, 251], "location": "洛阳", "event": "权倾朝野"},
        ],
        "is_faction_leader": False,
    },
    "荀彧": {
        "active_years": [189, 212],
        "home_base": "颍川",
        "timeline": [
            {"years": [189, 196], "location": "兖州", "event": "曹操典农校尉"},
            {"years": [196, 212], "location": "许昌", "event": "曹操谋士"},
        ],
        "is_faction_leader": False,
    },
    "郭嘉": {
        "active_years": [196, 207],
        "home_base": "颍川",
        "timeline": [
            {"years": [196, 207], "location": "许昌", "event": "曹操军师祭酒"},
        ],
        "is_faction_leader": False,
    },
    "贾诩": {
        "active_years": [192, 220],
        "home_base": "武威",
        "timeline": [
            {"years": [192, 197], "location": "长安", "event": "李傕下部"},
            {"years": [197, 208], "location": "荆州", "event": "刘表客卿"},
            {"years": [208, 220], "location": "许昌", "event": "曹操下部"},
        ],
        "is_faction_leader": False,
    },
    "陈宫": {
        "active_years": [189, 199],
        "home_base": "东武",
        "timeline": [
            {"years": [189, 192], "location": "兖州", "event": "曹操下部"},
            {"years": [192, 198], "location": "濮阳", "event": "吕布下部"},
            {"years": [198, 199], "location": "下邳", "event": "吕布谋士"},
        ],
        "is_faction_leader": False,
    },
    "徐庶": {
        "active_years": [200, 230],
        "home_base": "颍川",
        "timeline": [
            {"years": [200, 208], "location": "新野", "event": "刘备下部"},
            {"years": [208, 230], "location": "许昌", "event": "曹操下部"},
        ],
        "is_faction_leader": False,
    },
    "庞统": {
        "active_years": [209, 214],
        "home_base": "襄阳",
        "timeline": [
            {"years": [209, 211], "location": "南郡", "event": "周瑜下部"},
            {"years": [211, 214], "location": "雒县", "event": "刘备下部，阵亡"},
        ],
        "is_faction_leader": False,
    },
    "法正": {
        "active_years": [207, 220],
        "home_base": "扶风",
        "timeline": [
            {"years": [207, 211], "location": "成都", "event": "刘璋下部"},
            {"years": [211, 214], "location": "成都", "event": "归刘备"},
            {"years": [214, 220], "location": "成都", "event": "刘备谋主"},
        ],
        "is_faction_leader": False,
    },

    }


def get_npc_location(npc_name, year):
    """根据年份返回NPC所在城市，不在活跃期返回None"""
    if npc_name not in NPC_SCHEDULE:
        return None
    npc = NPC_SCHEDULE[npc_name]
    if year < npc["active_years"][0] or year > npc["active_years"][1]:
        return None
    for entry in npc.get("timeline", []):
        if entry["years"][0] <= year <= entry["years"][1]:
            return entry["location"]
    return npc["home_base"]


def is_npc_active(npc_name, year):
    """判断NPC在某年是否活跃（活着）"""
    if npc_name not in NPC_SCHEDULE:
        return False
    start, end = NPC_SCHEDULE[npc_name]["active_years"]
    return start <= year <= end


def is_faction_leader(npc_name):
    """判断是否为势力领袖"""
    return NPC_SCHEDULE.get(npc_name, {}).get("is_faction_leader", False)


def is_major_hero(npc_name):
    """判断是否为历史名将（招募难度额外加成）"""
    major_heroes = {"刘备", "关羽", "张飞", "赵云", "诸葛亮", "曹操", "吕布", "孙权", "周瑜", "司马懿"}
    return npc_name in major_heroes


def get_npcs_in_city(city, year):
    """返回某年某城市的NPC列表"""
    npcs = []
    for npc_name in NPC_SCHEDULE:
        loc = get_npc_location(npc_name, year)
        if loc == city:
            npcs.append(npc_name)
    return npcs


def get_all_active_npcs(year):
    """返回某年所有活跃的NPC"""
    npcs = []
    for npc_name in NPC_SCHEDULE:
        if is_npc_active(npc_name, year):
            npcs.append(npc_name)
    return npcs


if __name__ == "__main__":
    # 简单测试
    print(f"关羽在184年位于: {get_npc_location('关羽', 184)}")
    print(f"曹操在208年位于: {get_npc_location('曹操', 208)}")
    print(f"周瑜在209年位于: {get_npc_location('周瑜', 209)}")
    print(f"刘备在223年是否活跃: {is_npc_active('刘备', 223)}")
    print(f"司马师在184年是否活跃: {is_npc_active('司马师', 184)}")
    print(f"刘备是否为领袖: {is_faction_leader('刘备')}")
    print(f"曹操是否为领袖: {is_faction_leader('曹操')}")
