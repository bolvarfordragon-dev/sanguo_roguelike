# 腾讯云 Lighthouse 部署指南

> 目标：把三国文字 Roguelike 部署到腾讯云轻量服务器，20-50ms 延迟、不冷启动、月成本 ~¥30。

---

## 1. 准备工作

### 1.1 购买 Lighthouse 实例
- 腾讯云控制台 → 轻量应用服务器
- 套餐：**1核 2G 50G SSD** 够用（玩家不多）
- 镜像：**Ubuntu 22.04 LTS** 或 **Ubuntu 24.04 LTS**
- 地域：选玩家最近的（上海/北京/广州）
- 公网带宽：3-5 Mbps（文字游戏，几乎不吃带宽）
- 防火墙规则：开 **80 / 443 / 22** 三个端口

### 1.2 域名（可选但推荐）
- 在腾讯云 / Cloudflare 买个便宜域名（`.cn` 首年 ¥9）
- A 记录解析到 Lighthouse 公网 IP
- 不买也行，临时直接用 `http://<公网IP>:5000`

---

## 2. 服务器初始化（首次）

SSH 登录服务器后执行：

```bash
# 1. 更新系统
sudo apt update && sudo apt upgrade -y

# 2. 创建部署用户（可选，直接用 root 也行）
sudo useradd -m -s /bin/bash deploy
sudo usermod -aG sudo deploy

# 3. 把代码传上去（三种方式任选）

# 方式 A：Git（推荐）
cd /opt && sudo git clone <你的仓库地址> sanguo_roguelike
sudo chown -R deploy:deploy /opt/sanguo_roguelike

# 方式 B：scp（本机操作）
# scp -r ./sanguo_roguelike deploy@<server-ip>:/opt/

# 方式 C：rsync（本机操作）
# rsync -avz --exclude='.git' ./sanguo_roguelike/ deploy@<server-ip>:/opt/sanguo_roguelike/
```

---

## 3. 部署方式（选一个）

### 🚀 方式 A：Docker（推荐，最简单）

```bash
cd /opt/sanguo_roguelike
sudo docker compose up -d --build
```

- 第一次会拉 `python:3.11-slim` 镜像 + 装依赖（约 2-3 分钟）
- 完成后服务在 `:5000` 监听
- 启动/停止/日志：
  ```bash
  sudo docker compose ps
  sudo docker compose logs -f sanguo
  sudo docker compose restart
  ```

### ⚙️ 方式 B：systemd（不用 Docker）

```bash
# 一键脚本
bash deploy/scripts/setup-lighthouse.sh

# 或者手动
cd /opt/sanguo_roguelike
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt gunicorn
sudo cp deploy/systemd/sanguo.service /etc/systemd/system/
sudo systemctl enable --now sanguo
```

---

## 4. HTTPS（推荐，10 分钟搞定）

**前置**：域名已解析到服务器公网 IP（DNS 生效要 5-30 分钟）

```bash
# 安装 certbot
sudo apt install certbot python3-certbot-nginx

# 自动签证书 + 改 nginx 配置
sudo certbot --nginx -d your-domain.com

# 测试自动续期
sudo certbot renew --dry-run
```

- 之后直接访问 `https://your-domain.com`
- 证书 90 天自动续期

---

## 5. 验证部署

```bash
# 检查服务
sudo systemctl status sanguo          # systemd 方式
sudo docker compose ps                # docker 方式

# 看日志
sudo journalctl -u sanguo -f          # systemd
sudo docker compose logs -f sanguo    # docker

# 测试 API
curl http://127.0.0.1:5000/api/state
```

打开浏览器访问：
- 临时：`http://<服务器公网IP>:5000`
- 正式：`https://your-domain.com`

---

## 6. 运维小贴士

### 6.1 数据持久化
- `saves/` — 玩家存档目录（docker-compose 已挂载）
- `reincarnation.json` — 转世累计数据
- `achievements.json` — 成就数据
- 三个文件**不要**放进 `.gitignore`，但容器内会自动初始化

### 6.2 备份（推荐每天）
```bash
# 加到 crontab：每天凌晨 3 点打包
0 3 * * * cd /opt/sanguo_roguelike && tar czf /backup/sanguo-$(date +\%Y\%m\%d).tar.gz saves/ reincarnation.json achievements.json
```

### 6.3 更新代码
```bash
cd /opt/sanguo_roguelike
sudo git pull
sudo docker compose up -d --build       # docker
# 或：sudo systemctl restart sanguo      # systemd
```

### 6.4 性能调优
- 单 worker 是有意为之（游戏状态是单例）
- 1 核 2G 同时在线 3-5 人完全 OK
- 如果玩家多了需要扩展，先解决单例问题（见下文）

---

## 7. ⚠️ 重要：单例架构问题

`api.py` 第 767 行：
```python
api = SanguoAPI()        # 全进程共享一个实例
app = Flask(...)
```

**这意味着所有玩家共享同一个游戏世界**。2 个玩家同时玩会互相干扰。

**解决方向**（推广给真实玩家之前必须改）：
1. **方案 1（轻）**：用 cookie/session 区分玩家，每个会话一个 `SanguoAPI` 实例
   - 改动 ~30 行，需要给 `SanguoAPI` 加 session_id 参数
   - 改完 1 核 2G 能撑 5-10 人
2. **方案 2（重）**：抽离 game state 到外部存储（Redis/SQLite）
   - 改动大，但能撑几十人

**试玩阶段**（自己 / 朋友小范围玩）：单例够用，**不用改**。

---

## 8. 文件清单

```
sanguo_roguelike/
├── Dockerfile                       # Docker 镜像定义
├── docker-compose.yml               # 一键启动
├── .dockerignore                    # 减小镜像体积
├── deploy/
│   ├── DEPLOY_LIGHTHOUSE.md         # 本文档
│   ├── nginx/sanguo.conf            # nginx 反代
│   ├── systemd/sanguo.service       # systemd service
│   └── scripts/setup-lighthouse.sh  # 一键部署脚本
└── ... (游戏代码)
```
