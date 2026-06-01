# 绑定域名 aidev.dpdns.org 的部署说明

> 说明：域名绑定需要在你自己的服务器上完成，本项目已经提供可直接使用的 Nginx 配置模板。

## 1. 将域名解析到你的服务器

在 ddns 或 DNS 管理台中，将 `aidev.dpdns.org` 指向你的服务器公网 IP。

## 2. 启动应用

```bash
cd recsys_eval_system
sudo docker compose up -d --build
```

应用默认监听服务器本机 `127.0.0.1:8000`。

## 3. 安装并配置 Nginx

将 `deploy/nginx_aidev.dpdns.org.conf` 复制到：

```bash
/etc/nginx/sites-available/aidev.dpdns.org
```

然后执行：

```bash
sudo ln -s /etc/nginx/sites-available/aidev.dpdns.org /etc/nginx/sites-enabled/aidev.dpdns.org
sudo nginx -t
sudo systemctl reload nginx
```

## 4. （可选）申请 HTTPS 证书

```bash
sudo apt-get update
sudo apt-get install -y certbot python3-certbot-nginx
sudo certbot --nginx -d aidev.dpdns.org
```

完成后即可通过：

```text
http://aidev.dpdns.org
```

或启用 HTTPS 后：

```text
https://aidev.dpdns.org
```

访问系统。
