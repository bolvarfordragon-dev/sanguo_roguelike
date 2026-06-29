#!/bin/bash
# 三国文字Roguelike — Lighthouse 一键部署脚本
# 适用：Ubuntu 22.04/24.04 LTS 腾讯云轻量服务器
#
# 使用：
#   bash deploy/scripts/setup-lighthouse.sh
#
# 完成后：
#   - 服务跑在 :5000
#   - 静态资源由 nginx 反代（HTTPS 需要先解析域名 + certbot）
#   - systemd 守护，自动重启

set -euo pipefail

APP_DIR="/opt/sanguo_roguelike"
APP_USER="www-data"

echo "==> 1/6 系统更新 + 基础包"
sudo apt update -qq
sudo apt install -y python3-pip python3-venv nginx certbot python3-certbot-nginx git

echo "==> 2/6 拉取最新代码（如果目录不存在则 git clone）"
if [ -d "$APP_DIR" ]; then
    cd "$APP_DIR" && sudo -u "$APP_USER" git pull --ff-only
else
    sudo git clone <your-repo-url> "$APP_DIR"
    sudo chown -R "$APP_USER:$APP_USER" "$APP_DIR"
fi

echo "==> 3/6 Python 虚拟环境 + 依赖"
cd "$APP_DIR"
[ ! -d venv ] && sudo -u "$APP_USER" python3 -m venv venv
sudo -u "$APP_USER" venv/bin/pip install --upgrade pip -q
sudo -u "$APP_USER" venv/bin/pip install -r requirements.txt gunicorn -q

echo "==> 4/6 systemd service"
sudo cp deploy/systemd/sanguo.service /etc/systemd/system/sanguo.service
sudo systemctl daemon-reload
sudo systemctl enable sanguo
sudo systemctl restart sanguo

echo "==> 5/6 nginx 反代"
sudo cp deploy/nginx/sanguo.conf /etc/nginx/conf.d/sanguo.conf
# 占位域名替换
sudo sed -i "s/your-domain.com/${DOMAIN:-your-domain.com}/g" /etc/nginx/conf.d/sanguo.conf
sudo nginx -t
sudo systemctl reload nginx

echo "==> 6/6 防火墙（lighthouse 控制台 + iptables 双层）"
sudo ufw allow 80/tcp  2>/dev/null || true
sudo ufw allow 443/tcp 2>/dev/null || true
# 提醒：腾讯云控制台"防火墙"也要开 80/443

echo ""
echo "✅ 部署完成！"
echo "  - 服务状态：sudo systemctl status sanguo"
echo "  - 实时日志：sudo journalctl -u sanguo -f"
echo "  - 临时访问：http://<server-ip>:5000"
echo "  - HTTPS：export DOMAIN=your-domain.com && sudo certbot --nginx -d \$DOMAIN"
