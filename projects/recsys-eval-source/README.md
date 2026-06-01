# 大模型增强推荐链路能力评测与归因系统

这是一个可直接运行的完整项目包，包含：

- 合成日志数据集生成
- 端到端结果评测
- 模块级指标评测
- 归因分析
- 可运行的前后端评测平台
- 任务创建、模式选择、日志上传、结构校验、链路解析、链路确认、评测配置、结果展示完整流程
- Docker 部署支持
- 域名绑定配置模板
- 多份测试用 JSON / JSONL 日志文件

## 一、目录结构

```text
recsys_eval_system/
├── backend/
│   ├── app.py
│   ├── task_service.py
│   └── benchmark/
├── frontend/
│   ├── index.html
│   ├── app.js
│   └── styles.css
├── generated/
├── sample_logs/
├── deploy/
├── scripts/
├── Dockerfile
├── docker-compose.yml
├── run_experiments.py
└── requirements.txt
```

## 二、快速开始

### 方式 1：本地直接运行

```bash
pip install -r requirements.txt
python3 run_experiments.py
python3 backend/app.py
```

浏览器打开：

```text
http://127.0.0.1:8000
```

### 方式 2：一键脚本

Linux / macOS:

```bash
bash scripts/start_local.sh
```

Windows:

```bat
scripts\start_local.bat
```

### 方式 3：Docker 部署

```bash
docker compose up --build
```

默认端口：

```text
http://127.0.0.1:8000
```

## 三、前端平台功能

当前版本前端已经支持以下完整流程：

- 任务列表页
- 新建评测任务页
- 评测模式选择页
- Trace 日志上传页
- 日志结构校验页
- 推荐链路解析页
- 链路结构图确认页
- 评测配置页
  - 自动评测配置
  - LLM 裁判评测配置
  - 人工评测配置
- 评测结果页
  - 总览
  - 评测详情
  - 可视化分析

其中：

- **LLM 裁判评测** 和 **人工评测** 属于评测配置页中的评测方式；
- 评测结果页只保留 **总览、评测详情、可视化分析** 三个一级标签页；
- 可视化分析页已改为直接复用评测详情页中的指标数值，而不是单独造一套无关图表。

## 四、实验输出文件

运行 `python run_experiments.py` 后会在 `generated/` 下生成：

- `benchmark_main_v1.jsonl`：完整 trace 数据集
- `benchmark_main_v1_manifest.csv`：清单文件
- `per_trace_metrics.csv`：逐条样本指标
- `table_end_to_end.csv`：端到端结果表
- `table_module_response.csv`：模块响应表
- `table_attribution_case.csv`：归因样例表
- `table_attribution_summary.csv`：归因总体统计
- `summary.json`：前端概览读取文件
- `chart_end_to_end.png`
- `chart_module_heatmap.png`
- `chart_attribution.png`
- `chart_system_cost.png`
- `chart_system_latency.png`

## 五、测试用日志文件

项目提供了多份可直接上传测试的样例日志，位于 `sample_logs/` 目录：

- `sample_single_small.jsonl`：32 条 trace，适合快速演示单链路评测
- `sample_single_medium.jsonl`：128 条 trace，适合普通单链路测试
- `sample_compare_primary.jsonl`：192 条 trace，适合链路对比评测中的主日志
- `sample_compare_secondary.jsonl`：288 条 trace，适合链路对比评测中的对比日志
- `sample_focus_llm_composite.jsonl`：128 条 trace，偏向大模型混合链路与复合增强链路

## 六、域名绑定（aidev.dpdns.org）

> 说明：我已经把域名配置模板写好，但**真正的域名绑定必须在你自己的服务器上完成**，因为这一步需要你的公网服务器、DNS 解析权限和 Nginx/证书权限。

项目已附：

- `deploy/nginx_aidev.dpdns.org.conf`
- `deploy/DEPLOY_DOMAIN_README.md`

推荐部署方式：

1. 把 `aidev.dpdns.org` 解析到你的服务器公网 IP
2. 在服务器上启动项目：

```bash
sudo docker compose up -d --build
```

3. 将 `deploy/nginx_aidev.dpdns.org.conf` 复制到 Nginx 站点配置中
4. 重载 Nginx
5. 如需 HTTPS，再用 Certbot 申请证书

完成后即可通过：

```text
http://aidev.dpdns.org
```

访问；配置 HTTPS 后可使用：

```text
https://aidev.dpdns.org
```

## 七、论文实验对应关系

### 1. 端到端结果评测
对应文件：

- `generated/table_end_to_end.csv`
- `generated/chart_end_to_end.png`

### 2. 模块级指标响应
对应文件：

- `generated/table_module_response.csv`
- `generated/chart_module_heatmap.png`

### 3. 归因结果分析
对应文件：

- `generated/table_attribution_case.csv`
- `generated/table_attribution_summary.csv`
- `generated/chart_attribution.png`

### 4. 系统工程指标
对应文件：

- `generated/chart_system_cost.png`
- `generated/chart_system_latency.png`

## 八、方法定位说明

这套系统本质上是一个**可控合成日志实验平台 + 评测平台原型系统**，适合支持：

- 模块能力评测
- 异常注入实验
- 归因验证
- 教师演示
- 前后端原型展示

它不主张替代真实线上日志，而是作为一个**可解释、可重复、可控扰动**的实验载体和演示系统。
