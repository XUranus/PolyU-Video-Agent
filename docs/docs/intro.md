---
id: intro
title: 欢迎来到 LectureMind
sidebar_label: 概述
---

# 欢迎来到 LectureMind

LectureMind 是一个 **AI 驱动的课堂视频分析平台**。它能将一堂完整的讲座视频自动转化为结构化的知识体系——包含逐字稿、课件幻灯片、知识点摘要、思维导图，并提供基于 RAG 的智能问答助手，让你随时与 AI 对话、回顾课程内容。

---

## 它能做什么？

LectureMind 的核心能力覆盖了从视频上传到知识输出的完整流程：

- **视频上传与转码** — 上传讲座视频，自动转码为 HLS 自适应流，支持在线流畅播放
- **语音识别 (ASR)** — 基于阿里云 DashScope Qwen3-ASR 生成带时间戳的逐字稿
- **幻灯片检测** — 基于 SSIM 算法自动识别画面切换，精准定位课件页面
- **幻灯片 OCR** — 使用视觉语言模型 (VL) 对高分辨率幻灯片截图进行文字识别
- **知识提取** — 通过 LLM 从分段内容中提取细粒度知识点和粗粒度摘要
- **思维导图生成** — 自动构建层次化的概念关系图
- **RAG 智能问答** — 基于检索增强生成的多模式对话助手（支持 Fast RAG 和 Agentic RAG）
- **向量语义检索** — 使用 ChromaDB 对知识点进行向量化存储，支持语义搜索

---

## 适合谁使用？

| 角色 | 使用场景 |
|------|---------|
| **学生** | 课后快速回顾课堂重点，通过 AI 问答解决疑惑 |
| **教育工作者** | 分析课程内容结构，优化教学设计 |
| **自学者** | 将在线课程转化为可检索的知识库，提高学习效率 |

---

## 你将学到什么？

本 Wiki 涵盖从零开始使用和开发 LectureMind 的完整指南：

- **[快速开始](./getting-started.md)** — 5 分钟内从零启动 LectureMind
- **[安装指南](./installation.md)** — 详细的环境搭建和依赖安装步骤
- **[配置详解](./configuration.md)** — 所有配置项的完整参考
- **[架构概览](./architecture)** — 系统架构、数据流和技术栈
- **[后端开发](./backend/overview)** — Django REST API、数据模型和任务管线
- **[AI 核心模块](./ai/overview)** — RAG 引擎、Agent 系统、向量存储、ASR/OCR
- **[前端开发](./frontend/overview)** — React 组件、聊天界面和 SSE 流式传输
- **[部署指南](./deployment/docker)** — Docker 部署和生产环境配置
- **[开发指南](./development/adding-tasks)** — 如何扩展任务管线和 Agent 工具

---

## 端到端用户旅程

从上传视频到与 AI 对话，整个流程如下：

```mermaid
graph LR
    A[上传视频] --> B[等待处理]
    B --> C[探索知识]
    C --> D[与 AI 对话]

    style A fill:#4CAF50,color:#fff
    style B fill:#FF9800,color:#fff
    style C fill:#2196F3,color:#fff
    style D fill:#9C27B0,color:#fff
```

### 上传视频

将讲座视频文件拖拽到 LectureMind 界面，系统会自动创建处理任务。

### 等待处理

后台任务管线会依次完成转码、语音识别、幻灯片检测、OCR、知识提取等步骤。你可以在界面中实时查看每个任务的进度。

### 探索知识

处理完成后，你将获得：带时间戳的逐字稿、按章节组织的知识点、课程摘要、自动生成的思维导图，以及课件幻灯片截图。

### 与 AI 对话

打开 RAG 聊天助手，用自然语言提问。AI 会基于课程内容检索相关知识点，给出带引用来源的精准回答。

---

:::tip 快速上手
如果你已经迫不及待，直接跳转到 [快速开始](./getting-started.md)，5 分钟内即可运行 LectureMind。
:::
