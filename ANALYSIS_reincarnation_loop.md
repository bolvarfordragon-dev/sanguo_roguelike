# 三国文字 Roguelike — 转世循环机制分析报告

> 范围：只读源码，不修改代码。  
> 项目根：`/root/sanguo_roguelike/`  
> 总规模：约 8,394 行 Python（核心 ~7,500 行）

---

## 1. 源码结构图

```
/root/sanguo_roguelike/
├── config.py          120  全局常量：年表/属性/官职/业力上限/转世率
├── state.py           136  GameState：年/月/事件标志/本局统计/run_stats
├── character.py       424  Character + NPC + 41 个 NPC 预设（含武/智/魅/运/运）
├── combat.py          463  CombatSession：掷骰子战斗 + 4 战术 + 7 主动技能
├── engine.py         2444  SanguoEngine：new_game / tick / 转世 / NPC / 商店
├── skills.py          243  Skill + 18 个技能（7 被动/7 主动/4 NPC 赠）
├── effects.py         156  buff/debuff 定义（含「疗伤」但永远不发放）
├── world.py           333  13 州地图 + 完整连通图 + BFS 寻路
├── npc_schedule.py    620  武将历史时空表（184-220）+ is_active 判定
├── events/
│   ├── mandatory.py   261  必然事件（讨董/官渡/赤壁/三顾茅庐…）
│   ├── conditional.py 377  条件事件（桃园/华容/三顾…）
│   └── choices.py     172  分支选择事件
├── random_events.py   367  城外随机：单挑/舌战/奇遇 vs 负伤/中毒/伏兵
├── campaigns.py       151  3 大战役（讨董/赤壁/三国鼎立）
├── equipment.py       349  装备掉落（20% 概率，传奇上限+20 业力 cap）
├── achievements.py    181  8 个成就 + 解锁判定
├── progression.py     143  史籍/解锁/历史记录（仅记录，不影响游戏）
├── narrative.py       182  叙事字符串
├── api.py             888  WSGI 入口（供 Railway 部署）
├── playthrough.py     106  完整流程模拟器
├── test_100.py         75  100 次原始「啥都不做」跑分
├── test_20pct.py        68  200 次「只做战斗策略1」跑分
├── skills/skills/game-playtest-loop/  自动化试玩 skill
│   └── scripts/playtest.py             当前主用脚本
```

### 1.1 模块依赖关系

```
                    config.py
                       │
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
    state.py     character.py     world.py
        │              │              │
        └──────┬───────┘              │
               ▼                      │
         combat.py  ◀── random_events.py
               │                      │
               └────────┬─────────────┘
                        ▼
                    engine.py ◀── effects.py
                        │  ◀── skills.py
                        │  ◀── npc_schedule.py
                        │  ◀── events/*.py
                        │  ◀── campaigns.py
                        │  ◀── equipment.py
                        │  ◀── achievements.py
                        ▼
                      api.py
```

`engine.SanguoEngine` 是唯一状态机驱动者：所有 tick、战斗结算、转世都从这里走。

---

## 2. 核心机制摘要

### 2.1 单局循环（出生→死亡→转世）

```
new_game()                                   engine.py:318
  ├─ 创建 Character（武40/智30/名10/魅20/运30 ± 随机±5）
  ├─ 加载 karma = _load_reincarnation()     engine.py:299
  ├─ 把每个 karma 项加到对应属性上           engine.py:328-336
  ├─ 初始化 NPC（41 个历史武将）              engine.py:368
  └─ running=True

tick()                                       engine.py:918
  ├─ state.tick() — 月+1
  ├─ 检查战役 / 选择事件 / 必然事件 / 条件事件
  ├─ _natural_recovery() — 体力+25 / 士气微调 / 粮-3 / 金-1+月俸
  ├─ _tick_favorability_monthly()
  ├─ _sync_npc_locations() — NPC 按时间表换城
  ├─ trigger_random_events() — 单挑/舌战/奇遇 vs 负伤/中毒/伏兵
  ├─ player.tick_effects() — 状态衰减
  ├─ _check_combat_encounter() — 32% 概率遇敌
  ├─ _check_npc_encounter() — 25% 概率遇同 NPC
  └─ is_game_over() — hp≤0 或 year≥220

  ↳ 战斗：resolve_combat_action(choice)      engine.py:420
  ↳ NPC：handle_npc_encounter(choice)        engine.py:1564
  ↳ 移动：move_to(city)                      engine.py:772
  ↳ 市集：handle_market_input(cmd)            engine.py:645

is_game_over() 返回 True 时                  state.py:117
  ├─ 死亡（HP≤0）→ show_death_screen()      engine.py:1918
  └─ 到 220 年 → resolve_ending()             engine.py:2147

show_death_screen()                         engine.py:1918
  ├─ 计算 fragments = 5 + months/6
  ├─ 展示传承商店（按 can_learn_skill 过滤）
  ├─ 玩家选技能（输入数字 / 0 直接开始）
  ├─ 累计 karma：
  │   ├─ behavior_karma（行为业力，主要来源）
  │   │   ├─ 武 = round(karma_wins × 0.3, 1) + upset_bonus
  │   │   ├─ 魅 = karma_npc_recruited + karma_conversation × 0.2
  │   │   ├─ 名 = int(karma_history_events × 0.5)
  │   │   ├─ 智 = int(karma_speech_wins × 0.5 + karma_intel × 0.3)
  │   │   └─ 运 = int(karma_rare_encounters × 0.5)
  │   └─ death_karma（死亡时属性 × 1% 的补充）  ← 几乎为 0
  ├─ 写 reincarnation.json（karma 持久化）
  └─ new_game() — 立即转世
```

### 2.2 转世机制：业力 / 碎片 / 商店

**业力（Karma）** — 跨局永久累积的属性加成：

| 来源 | 文件:行 | 公式 |
|---|---|---|
| 战斗胜利 | engine.py:2014 | `武 += wins × 0.3`（取整 + 差值 upset bonus） |
| 招募 NPC | engine.py:2015 | `魅 += npc_count + conversation × 0.2` |
| 触发历史事件 | engine.py:2016 | `名 += history_events × 0.5` |
| 舌战胜 | engine.py:2017 | `智 += speech_wins × 0.5 + intel × 0.3` |
| 稀有奇遇 | engine.py:2018 | `运 += rare_encounters × 0.5` |
| 死亡属性 1% | engine.py:2022 | `int(stats[stat] × 0.01)` — 几乎为 0 |
| 成就 | engine.py:1095 | 任意 stat +1 |

业力通过 `new_game()` 在新角色上加到 `stats` 字典（engine.py:328-336）。  
**业力上限**：基础 cap = 600/480/400/400/320（武/智/名/魅/运），传奇装备可 +20/属性。

**碎片（Fragments）** — 死亡后买技能用：
- 死亡时奖励：`5 + (months + 5) // 6`（engine.py:2410）
- 战斗胜利奖励：15% 概率掉 1 枚（engine.py:485）
- 仅在**死亡界面**可用，**会跨局保留**（`inheritance_fragments` 在 character 持久化）
- 技能价格：3-10 枚（skills.py）

**死亡结算**（engine.py:1918）：
```
本局总结 → 商店列表 → 玩家购买 → 写 karma 文件 → 立刻 new_game()
```
注意：死亡后**没有「重新出生选项」**，直接进入下一局。

**传承商店**（engine.py:1957）：
- 7 个传承被动（3-6 枚）：求生本能/背水一战/佣兵之道/情报网/铁人/吉星高照/节俭旅人
- 7 个传承主动（4-10 枚）：暗箭/佯攻/呐喊/反制/绝技/布阵/破釜沉舟
- 4 个 NPC 赠技能（0 枚）：义结金兰/龙胆/隆中策/魏武策略
- 筛选：`can_learn_skill(sid, p)`（skills.py:167）— 检查碎片、属性、官职、前置

### 2.3 单局循环关键参数

| 参数 | 值 | 来源 |
|---|---|---|
| 时间窗口 | 184-220 年（36 年 = 432 月） | config.START_YEAR/END_YEAR |
| 初始属性 | 武40/智30/名10/魅20/运30 ± 5 | config.INITIAL_STATS |
| 初始资源 | 粮50/金50/HP100/体100/士气100 | config |
| 战斗遭遇率 | 32% 名望修正 | engine.py:1175 |
| NPC 遭遇率 | 25%（仅同城） | engine.py:1157 |
| 正面随机事件率 | 25% | random_events.py:18 |
| 负面随机事件率 | 10% | random_events.py:23 |
| 月消耗 | 粮-3 / 金-1+月俸 | engine.py:1297 |
| 移动成本 | 10 金/1 月 | world.py |
| 移动遭遇（travel） | 30% 概率 | （playtest 里） |

### 2.4 战斗系统（掷骰子版）

`CombatSession.simulate()`（combat.py:67）：
```
power = (武 × 1.2 + 智 × 0.7) × 兵因子 × 士气因子 × (1+地形+天气)
基础胜率 = 0.5 + (attacker_power - defender_power) / 200
行动修正 = base + tactic_mod + skill_mod        # 进攻+12% / 坚守+5% / 撤退-15% / 用计+20%
胜率 = clamp(0.05, 0.95)
掷骰 = random(1, 100)
effective_roll = dice/100 + (运-50)/200
胜负 = effective_roll ≤ 胜率
暴击 = (dice==100) 或 (dice≥95-bonus 且 运>80)
大凶 = dice==1 或 (dice≤5 且 敌方运>80)
```
战损 = `兵力 × 系数 × damage_mod × crit_mult`，仅战败且大损时玩家 HP -10\~30。

---

## 3. 为什么 playtest 100% 死亡？

### 3.1 实证数据

跑了 50 次 playtest（playtest.py 智能策略）：

| 指标 | 数值 |
|---|---|
| 总跑数 | 50 |
| 到达 220 年 | **0 / 50 = 0%** |
| 平均存活 | 76.6 月（≈ 6.4 年） |
| 平均最高官职 | 校尉 |
| NPC 招募率 | 71.8% |
| 平均业力/局 | +14.6 |

### 3.2 根本原因（按结构性从强到弱）

#### 原因 A — **结构性 Bug：游戏没有任何 HP 恢复机制** 🚨

源码检索结论：
- `take_damage()` 在 5 个地方被调用：战斗战败、负伤、中毒、伏兵、饥饿。
- `heal()` 方法定义了 1 个（character.py:155），但**整个项目 0 次调用**。
- 「疗伤」buff 在 effects.py:31 定义了 +5HP/turn，character.py:216 实现逻辑，**但全代码 0 次 add_effect("疗伤")**。

也就是说，**HP 是单调下降的**，初始 100 HP，配合：
- 32% 战斗遭遇率（~30 场/局）
- 战败概率 ~30%（其中 ~30% 触发 HP 损伤 10-30）
- 5-8 次负伤/中毒/伏兵（每次 -5\~30 HP）
- 饥饿时 -5 HP/月

数学上无法撑到 220 年（432 月）。**这是设计上的硬伤，不是 playtest 策略差**。

#### 原因 B — playtest 策略过于激进

playtest.py 的自动决策：

```python
# 1. 战斗：永远选 1（进攻）
if e.pending_combat is not None:
    e.resolve_combat_action("1")
```
「进攻」是 4 个战术中**风险最高**的：risk_mod=1.2，体力消耗-12，承担伤害 +20%。

```python
# 2. NPC：永远选 1（诚心相邀）
e.handle_npc_encounter("1")
```
- 诚心策略 +10% 招募率，但刘备/曹操不可招募
- 从不选择「以利诱之」（需要 30 金，但能招到顶级 NPC）
- 从不选择「晓以大义」（需要名望≥50）
- 从不主动触发刘/曹的羁绊赠送技能

```python
# 3. 移动：30% 概率随机探索
if random.random() < 0.30 and p.gold >= 10 and p.stamina >= 15:
```
- 平均每月消耗 3 金，36 年 432 月消耗 ~1300 金（远超初始 50）
- 但实际上没有足够金币支撑 → 后续被迫依赖俸禄（散兵 5 金）
- 从不主动去 NPC 所在城市（缺乏目标导航）

```python
# 4. 市集：粮<20 自动买
if p.food < 20 and p.gold >= 10:
    e.state.player.gold -= 10
    e.state.player.food = min(100, e.state.player.food + 15)
```
- 10 金 15 粮，**但每月消耗粮 3 + 战役 3** = 6
- 只买不卖，金币被持续抽干
- **没有"卖粮换金"的反循环**

**playtest 缺的关键决策**：
1. ❌ 不使用主动技能（暗箭/反制/破釜沉舟）
2. ❌ 不切换战术（用计 +20% 胜率，坚守 -40% 承担伤害）
3. ❌ 不在战败时撤退
4. ❌ 不购买「情报」做 NPC 寻路
5. ❌ 不参与战役（campaign 跳过 → 错过关键奖励）
6. ❌ 不使用装备栏管理

#### 原因 C — 战斗频率与经济双重压力

| 月份 | 资源状况（典型） |
|---|---|
| 0 | 粮 50 / 金 50 / HP 100 |
| 12 | 粮 30 / 金 ~150 / HP 60-80 |
| 24 | 粮 30 / 金 ~250 / HP 30-50 |
| 36 | 粮 0 / 金 ~350 / HP 0-20 |
| 48 | **HP=0 死亡** |

实际跑 seed=42 4 年（48 月）死亡：HP=0, 粮 20, 金 584, rank 队长, 战斗 13（6W/7L）。

---

## 4. 推荐 Evolution Reward 公式

### 4.1 当前评估指标的不足

| 指标 | 问题 |
|---|---|
| `survived = months` | 不能反映游戏深度（如 6 月与 60 月 reward 线性） |
| `survival_rate = reached_220/total` | 0% 是全结构性问题，gradient 信号为零 |
| `avg_karma_growth` | 反映「业力引擎」健康度，但业力增长是单调的 |
| `recruit_rate` | 反映 NPC 系统，但不区分顶级/普通 NPC |

### 4.2 推荐 Reward 公式（多目标加权）

```python
def evolution_reward(run_result: dict, run_stats: dict) -> float:
    """
    Evolution-friendly reward for genetic/RL strategy search.
    目标：和人类玩家目标一致（活下来 + 变强 + 收集 + 体验内容）
    """
    # ── 1. 生存（鼓励活到 220 年）────────────────
    months = run_result['months']                     # 0..432
    months_reward = months / 4.32                     # 归一到 0..100
    
    # 终局 bonus（强引导）
    end_bonus = 0
    if run_result['status'] == 'reached_220':
        end_bonus += 100                              # 通关 +100
    elif run_result['final_hp'] > 0 and months > 240:
        end_bonus += 30                               # 活过半程 +30
    elif run_result['final_hp'] > 0 and months > 120:
        end_bonus += 10                               # 活过 10 年 +10
    
    # ── 2. 成长（鼓励晋升 + 累积属性）────────────
    rank_idx = RANK_ORDER.index(run_result['max_rank_achieved'])
    rank_reward = rank_idx * 4                        # 0..60 (15 级)
    
    exp_reward = min(run_result['max_exp_achieved'] / 50, 20)
                                                    # 0..20
    total_stats = sum(run_result['final_stats'].values())
    stat_reward = total_stats / 4                      # 初始 130 → 满 200 → 50
                                                    # 0..50
    
    # ── 3. 收集（鼓励招募顶级 NPC + 触发事件）─────
    npc_count = run_result.get('npc_recruited', 0)
    npc_score = 0
    for n in run_result.get('npc_list', []):
        if n in TOP_TIER:        npc_score += 15     # 刘/曹/诸葛/赵/关/张/周/司马
        elif n in MID_TIER:      npc_score += 8
        else:                    npc_score += 3
    npc_reward = min(npc_score, 40)                   # 0..40
    
    event_count = run_result.get('events_triggered', 0)
    event_reward = min(event_count * 4, 20)           # 桃园/三顾/华容等
    
    # ── 4. 战斗表现（鼓励有效战斗 + 越级挑战）─────
    wins = run_result.get('wins', 0)
    losses = run_result.get('losses', 0)
    total_battles = max(wins + losses, 1)
    win_rate = wins / total_battles
    combat_score = wins * 1.5 + (wins - losses) * 2   # 鼓励净胜
    
    # ── 5. 经济（鼓励稳定资源流）─────────────────
    final_gold = run_result.get('final_gold', 0)
    final_food = run_result.get('final_food', 0)
    econ_reward = 0
    if final_gold > 50:   econ_reward += 2
    if final_food > 30:   econ_reward += 2
    if final_gold > 200:  econ_reward += 3
    if final_food > 60:   econ_reward += 3
    
    # ── 6. 转世/业力（鼓励长程 meta-progress）─────
    karma_gain = run_result.get('karma_after', 0) - run_result.get('karma_before', 0)
    karma_reward = min(karma_gain / 5, 30)            # 0..30
    
    # ── 总分 ─────────────────────────────────────
    total = (
        months_reward + end_bonus +                   # 生存（最大 200）
        rank_reward + exp_reward + stat_reward +     # 成长（最大 130）
        npc_reward + event_reward +                   # 收集（最大 60）
        combat_score +                                # 战斗（无上限）
        econ_reward +                                 # 经济（最大 10）
        karma_reward                                  # 转世（最大 30）
    )
    return total
```

### 4.3 推荐评估指标

**1. 阶段指标（短期信号）**
- 12/24/36 月生存率（曲线指标）
- 曲长→司马晋升率（中期卡点诊断）
- 司马→校尉晋升率（后期卡点诊断）

**2. 内容覆盖指标**
- 战役触发率（讨董/赤壁/三国鼎立）
- 历史事件触发率（桃园/三顾/华容）
- 顶级 NPC 招募率（刘/曹/诸葛/周/赵）

**3. 战斗质量指标**
- 越级战斗率（打赢比自己强的敌人）
- 撤退成功率（避免无谓战损）
- 主动技能使用率（策略深度）

**4. 经济健康指标**
- 末期金/粮 > 0 比例
- 月平均收支平衡率
- 战役期间资源消耗管理

**5. 转世深度指标**
- 跨 N 局累计 karma 增长曲线
- 关键属性业力（武/名/魅）的「饱和速率」
- 传承技能购买的多样性

### 4.4 评分权重建议（针对 Genetic Strategy Search）

```python
# 进化算法用的 fitness = 上面公式的输出
# 关键变化点：
# 1) survival rate 不能直接当 reward（gradient=0）
# 2) 需要 sub-goal bonus 引导策略发现
# 3) 必须奖励「避免战斗」「主动技能使用」等隐性行为
WEIGHTS = {
    'survival_endgame': 100,      # 极强信号：通关
    'survival_midgame': 30,       # 中期 60 月 +30
    'rank_progression': 5,        # 每升一级 +5
    'top_npc_recruit': 15,        # 顶级 NPC +15
    'major_event_trigger': 4,     # 历史事件 +4
    'upset_victory': 3,           # 越级胜 +3
    'safe_retreat': 2,            # 成功撤退 +2
    'skill_usage': 2,             # 主动技能 +2
    'economy_balance': 1,         # 资源为正 +1
}
```

---

## 5. 关键发现 & 建议（不修改代码，只汇报）

### 🚨 必须修复的 Bug

1. **HP 无法恢复** — 整个游戏没有任何 HP+ 的代码路径。`疗伤` 效果定义但永不发放，`heal()` 方法定义但永不被调用。建议：每个城里加 `医师` 选项（10 金回 20 HP），或在 `自然恢复` 中加 `p.hp = min(100, p.hp + 3)`。

### ⚠️ 设计层面的潜在问题

2. **220 年通关是数学不可能的** — 即使有完美策略，HP 单调下降意味着后期必死于累计伤害。建议：通关目标不是 220 年，而是「达成 5 项满业力 + 习得 3 个传承技能 + 招募 4 个顶级 NPC」之类的 meta 目标。

3. **战斗频率与伤害曲线不匹配** — 32% 战斗率 × 36 年 = 138 场战斗，但战败概率 ~30% × 战败触发 HP 损 ~30% = ~12 次 HP 损伤（120-360 HP 总计）。这与「期望通关」不兼容。

4. **playtest 策略空间过窄** — 4 个战术 × 5 个 NPC 策略 × 10+ 个技能使用时机 × 4 个市场决策 × 移动目标选择 = 千级状态空间，但当前 playtest 只用 1+1+0+随机。

### 💡 Evolution 实验建议

5. **Reward 重设计** — 见 4.2/4.3。核心：从「单点通关」改为「多目标加权」。

6. **策略参数化** — 当前 playtest 几乎是「写死」决策。建议抽出 8-12 个可调参数（如战斗 aggressive/safe 倾向、买粮阈值、招 NPC 偏好、旅行概率），让遗传算法去搜索。

7. **修复 HP bug 后再评估** — 任何策略搜索都必须先解决 HP 单调下降问题，否则 gradient 信号不可靠。

---

## 6. 引用文件速查

| 主题 | 文件 | 关键行 |
|---|---|---|
| 转世业力计算 | engine.py | 2010-2036, 1918-2080 |
| 死亡界面 | engine.py | 1918-2080 |
| 商店技能筛选 | skills.py | 167-208 |
| 战斗结算 | combat.py | 67-195 |
| 自然恢复 | engine.py | 1297-1335 |
| 负面事件 | random_events.py | 292-365 |
| 城池市集 | engine.py | 632-674 |
| 招募公式 | engine.py | 1635-1800 |
| 自动试玩 | skills/.../playtest.py | 全文 |
| HP 唯一恢复 | character.py | 155-156, 214-218 |
