---
id: installation
title: 安装指南
sidebar_label: 安装
---

# 安装指南

本文档提供 LectureMind 的详细安装步骤，包括系统要求、依赖安装和验证方法。

---

## 系统要求

### 硬件要求

| 资源 | 最低要求 | 推荐配置 |
|------|---------|---------|
| **CPU** | 2 核 | 4 核+ |
| **内存** | 8 GB | 16 GB+ |
| **磁盘** | 20 GB 可用空间 | 50 GB+（视频和模型占用较多） |

:::info 内存说明
8 GB 内存可以运行基本功能，但混合分段（Hybrid Chunking）中的语义检查会自动关闭以节省内存。16 GB 或以上内存可获得最佳体验。
:::

### 操作系统

| 操作系统 | 支持情况 |
|----------|---------|
| Linux (Ubuntu 20.04+, Debian 11+) | 完全支持 |
| macOS 12+ | 完全支持 |
| Windows 10/11 (WSL2) | 通过 WSL2 支持 |

### 软件依赖

| 依赖 | 最低版本 | 用途 |
|------|---------|------|
| Docker | 20.10+ | 容器化部署（Docker 方式） |
| Docker Compose | 2.0+ | 多容器编排（Docker 方式） |
| Python | 3.10+ | 后端运行环境（本地开发） |
| Node.js | 18+ | 前端构建环境（本地开发） |
| pnpm | 8+ | 前端包管理器（本地开发） |
| ffmpeg | 4.0+ | 视频转码和音频提取 |
| ffprobe | 4.0+ | 视频元数据分析（随 ffmpeg 安装） |

---

## Docker 安装（推荐）

Docker 方式将自动处理所有系统依赖，是最简单的安装方式。

### 第一步：安装 Docker

:::tip 已安装 Docker？
如果已有 Docker 和 Docker Compose，直接跳到第二步。
:::

**Ubuntu / Debian：**

```bash
# 安装 Docker
curl -fsSL https://get.docker.com | sh

# 将当前用户加入 docker 组（免 sudo）
sudo usermod -aG docker $USER
newgrp docker

# 验证安装
docker --version
docker compose version
```

**macOS：**

下载并安装 [Docker Desktop for Mac](https://www.docker.com/products/docker-desktop/)。

**Windows：**

1. 启用 WSL2：`wsl --install`
2. 下载并安装 [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop/)
3. 在 Docker Desktop 设置中确认 WSL2 后端已启用

### 第二步：克隆仓库

```bash
git clone https://github.com/XUranus/LectureMind.git
cd LectureMind
```

### 第三步：配置环境变量

```bash
cp .env.example .env
```

编辑 `.env` 文件，填写必填配置：

```bash
# ── 必填项 ──────────────────────────────────────────

# 阿里云 DashScope API Key（用于 ASR + LLM）
DASHSCOPE_API_KEY=sk-xxxxxxxxxxxxxxxx

# 腾讯云 COS 配置（用于 ASR 音频文件上传）
COS_SECRECT_ID=AKIDxxxxxxxx
COS_SECRECT_KEY=xxxxxxxx
COS_REGION=ap-singapore        # 例如 ap-guangzhou, ap-singapore
COS_BUCKET=my-bucket-name
```

可选配置项（有默认值，无需修改即可运行）：

```bash
# ── 可选项 ──────────────────────────────────────────

# 端口配置
BACKEND_PORT=8000              # 后端 API 端口
FRONTEND_PORT=3000             # 前端页面端口

# LLM 模型选择
LLM_MODEL=qwen2.5-7b-instruct     # 任务管线使用的模型
CHAT_MODEL=qwen3-max               # 聊天/RAG 使用的模型
VL_MODEL=qwen2.5-vl-72b-instruct   # 幻灯片 OCR 使用的视觉模型
```

### 第四步：构建并启动

```bash
docker compose up --build
```

:::info 首次构建
首次构建需要下载 Python 依赖、Node.js 依赖并编译镜像，通常需要 3-10 分钟（取决于网络速度）。后续启动只需几秒。
:::

如需后台运行：

```bash
docker compose up -d           # 后台启动
docker compose logs -f web     # 查看后端日志
docker compose logs -f worker  # 查看任务处理器日志
```

### 第五步：验证安装

```bash
# 检查健康状态
curl http://localhost:8000/api/health/

# 预期返回
# {"status": "ok"}
```

浏览器访问 `http://localhost:3000`，看到 LectureMind 界面即表示安装成功。

---

## 本地开发安装

适合需要修改和调试代码的开发者。

### 1. 安装系统依赖

#### ffmpeg

```bash
# Ubuntu / Debian
sudo apt update && sudo apt install ffmpeg

# macOS
brew install ffmpeg

# Arch Linux
sudo pacman -S ffmpeg

# 验证安装
ffmpeg -version
ffprobe -version
```

#### Python 环境

推荐使用 Conda 管理 Python 环境：

```bash
# 安装 Miniconda（如未安装）
# https://docs.conda.io/en/latest/miniconda.html

# 方式 1: 使用 environment.yml 创建环境（推荐）
cd server
conda env create -f environment.yml
conda activate LectureMind

# 方式 2: 手动创建环境
conda create -n LectureMind python=3.10
conda activate LectureMind
pip install -r requirements.txt
```

:::tip 使用 venv 替代 Conda
如果你更习惯 venv，也可以：
```bash
cd server
python -m venv .venv
source .venv/bin/activate        # Linux / macOS
# .venv\Scripts\activate         # Windows
pip install -r requirements.txt
```
:::

#### Node.js 和 pnpm

```bash
# 安装 Node.js 18+（推荐使用 nvm）
# https://github.com/nvm-sh/nvm
nvm install 18
nvm use 18

# 安装 pnpm
npm install -g pnpm

# 验证安装
node --version    # v18.x.x 或更高
pnpm --version    # 8.x.x 或更高
```

### 2. 配置环境变量

```bash
# 在项目根目录创建 .env 文件
cp .env.example .env
# 编辑 .env 填写 DASHSCOPE_API_KEY 等必填项
```

### 3. 初始化数据库

LectureMind 开发环境默认使用 SQLite，无需额外安装数据库：

```bash
cd server/app
python manage.py migrate
```

你也可以创建一个管理员账号：

```bash
python manage.py createsuperuser
```

### 4. 启动后端

需要 **两个终端** 同时运行：

**终端 1 — API 服务器：**

```bash
cd server/app
conda activate LectureMind   # 激活环境
python manage.py runserver
```

**终端 2 — 任务处理器：**

```bash
cd server/app
conda activate LectureMind   # 激活环境
python manage.py process_async_task
```

### 5. 启动前端

**终端 3：**

```bash
cd frontend
pnpm install
pnpm start
```

### 6. 验证安装

```bash
# 后端健康检查
curl http://localhost:8000/api/health/

# 前端页面
# 浏览器打开 http://localhost:3000
```

---

## 数据库说明

| 环境 | 数据库 | 说明 |
|------|--------|------|
| 开发环境 | SQLite | 零配置，数据文件位于 `server/app/db.sqlite3` |
| 生产环境 (Docker) | SQLite | 通过 Docker volume 持久化 |
| 生产环境 (建议) | PostgreSQL | 更好的并发性能，需修改 `settings.py` |

:::tip 生产环境建议
如果你的 LectureMind 需要服务多个用户或处理大量视频，建议将数据库切换为 PostgreSQL。只需安装 `psycopg2` 并修改 `DATABASES` 配置即可。
:::

---

## 依赖说明

以下是项目主要依赖及其用途：

### 后端 (Python)

| 包 | 用途 |
|---|------|
| `django` | Web 框架 |
| `djangorestframework` | REST API 框架 |
| `gunicorn` | WSGI 生产服务器 |
| `openai` | DashScope OpenAI 兼容接口客户端 |
| `langchain` / `langgraph` | RAG 和 Agent 编排 |
| `chromadb` | 向量数据库 |
| `sentence-transformers` | 文本向量化模型 |
| `opencv-python` | 视频帧处理和 SSIM 计算 |
| `Pillow` | 图像处理 |
| `cos-python-sdk-v5` | 腾讯云 COS SDK |
| `python-dotenv` | 环境变量加载 |
| `django-cors-headers` | CORS 跨域支持 |

### 前端 (Node.js)

| 包 | 用途 |
|---|------|
| `react` | UI 框架 |
| `typescript` | 类型安全 |
| `antd` (Ant Design 6) | UI 组件库 |
| `tailwindcss` | 原子化 CSS |
| `@mux/mux-video-react` | HLS 视频播放器 |
| `react-router-dom` | 路由管理 |
| `axios` | HTTP 请求 |

---

## 常见安装问题

### Conda 环境创建失败

```bash
# 尝试清理缓存
conda clean --all
conda env create -f environment.yml
```

### pip 安装超时

```bash
# 使用国内镜像源
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### ffmpeg 版本过旧

```bash
# 检查版本
ffmpeg -version

# Ubuntu 升级方法
sudo add-apt-repository ppa:ubuntuhandbook1/ffmpeg6
sudo apt update && sudo apt upgrade ffmpeg
```

### ChromaDB 初始化错误

ChromaDB 在首次使用时会自动创建。如果遇到权限问题：

```bash
# 确保目录可写
mkdir -p server/app/media/chromadb
chmod 755 server/app/media/chromadb
```

### pnpm 命令不存在

```bash
# 确认 Node.js 已安装
node --version

# 重新安装 pnpm
npm install -g pnpm

# 或使用 corepack
corepack enable
corepack prepare pnpm@latest --activate
```

---

:::tip 下一步
安装完成后，查看 [配置详解](./configuration.md) 了解如何根据你的需求调整配置，或直接前往 [快速开始](./getting-started.md) 上传你的第一个视频。
:::
