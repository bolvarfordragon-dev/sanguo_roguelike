# 手机适配优化计划

## 任务清单（按顺序执行）

### 阶段一：核心适配（必须优先）
1. **自动存档（localStorage）** — 每tick API 请求后自动保存 game_state 到 localStorage，刷新页面无缝续玩
2. **下拉刷新** — 游戏主界面支持下拉/上滑触发"下月"操作
3. **底部上拉面板（Bottom Sheet）** — 战报/成就/市集等改为从底部滑出的面板
4. **按钮触控尺寸** — 所有按钮最低 44px 高度，战斗操作按钮加大
5. **防误触确认** — 撤退/转世等危险操作加"确认/取消"双按钮
6. **加载状态指示** — API 请求中显示 loading 圈
7. **禁止缩放** — `<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no">`

### 阶段二：体验增强
8. **属性面板增强** — 武力/智力/名望等属性显示彩色条形图，可视化成长
9. **事件预告** — 每次 tick 显示"下月将发生..."预告（战役倒计时/NPC出现）

### 阶段三：内容
10. **新手教程** — 首次游戏显示引导气泡（介绍核心操作）
11. **城市探索进度** — 地图显示已访问/未解锁城市，探索度进度条

## 实现规范

- 所有文件修改在 `/root/sanguo_roguelike/`
- 每次任务完成后 commit
- 触控优先，不依赖桌面端功能
- localStorage key 命名：`sanguo_game_v1`
- Bottom Sheet 使用 CSS transform + transition，禁止使用 fixed 弹窗遮挡游戏内容