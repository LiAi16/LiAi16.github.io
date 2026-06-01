# GitHub Pages / Cloudflare Pages 说明

## 结论

当前项目是“前端 + Python 后端 API + 文件上传 + 评测计算”的完整系统，**不能只靠 GitHub Pages 单独部署**。

GitHub Pages 和 Cloudflare Pages 都更适合部署：

- 纯静态前端页面
- 演示型页面
- 不需要后端实时计算的展示页面

如果你希望保留现在这个“上传日志并运行评测”的完整能力，推荐两种方式：

### 方案一：完整系统部署到服务器

- 域名：`aidev.dpdns.org`
- Nginx：反向代理到 Flask/Gunicorn
- 前端静态文件和后端 API 同域部署

优点：部署后最省心，前后端同域，不需要额外处理跨域。

### 方案二：前后端分离部署

- 前端：GitHub Pages 或 Cloudflare Pages
- 后端：自己的云服务器
- 前端域名：`aidev.dpdns.org`
- 后端域名：`api.aidev.dpdns.org`

优点：前端上线更方便。

缺点：

- 需要处理跨域
- 需要分别维护两套部署
- 需要修改前端 API 地址

## 推荐

如果你当前最重要的是让老师能完整体验“上传日志 → 配置评测 → 查看结果”，建议优先使用**服务器整站部署**。

如果你后面想把它拆成“展示页”和“计算服务”两部分，再考虑 GitHub Pages / Cloudflare Pages 会更合适。
