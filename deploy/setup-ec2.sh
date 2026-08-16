#!/usr/bin/env bash
set -euo pipefail
APP_DIR=/home/ubuntu/music-app
apt-get update
apt-get install -y nginx curl
curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
apt-get install -y nodejs
cd "$APP_DIR"
npm ci --omit=dev
chown -R ubuntu:ubuntu "$APP_DIR"
cat >/etc/systemd/system/music-app.service <<EOF
[Unit]
Description=AWS Music Subscription App
After=network.target
[Service]
Type=simple
User=ubuntu
WorkingDirectory=$APP_DIR
Environment=NODE_ENV=production
ExecStart=/usr/bin/node $APP_DIR/server.js
Restart=on-failure
[Install]
WantedBy=multi-user.target
EOF
cat >/etc/nginx/sites-available/music-app <<'EOF'
server {
  listen 80 default_server;
  server_name _;
  location / { proxy_pass http://127.0.0.1:3000; proxy_set_header Host $host; proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for; }
}
EOF
rm -f /etc/nginx/sites-enabled/default
ln -sf /etc/nginx/sites-available/music-app /etc/nginx/sites-enabled/music-app
nginx -t
systemctl daemon-reload
systemctl enable --now music-app
systemctl enable --now nginx
