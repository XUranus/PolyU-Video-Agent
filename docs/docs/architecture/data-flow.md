---
id: data-flow
title: 数据流详解
sidebar_label: 数据流
---

# 数据流详解

本章深入讲解 LectureMind 中数据的完整生命周期——从用户上传视频开始，经过 AI 处理管线，到最终通过 RAG 聊天输出回答。理解数据流是排查问题和扩展系统的基础。

---

## 1. 视频上传流程

当用户上传一个视频文件时，数据经过以下步骤：

```mermaid
sequenceDiagram
    actor User as 👤 用户
    participant FE as 🖥️ 前端
    participant API as 📡 Django API
    participant FS as 💾 文件系统
    participant DB as 🗄️ SQLite

    User->>FE: 选择视频文件
    FE->>API: POST /api/videos/upload/<br/>(multipart/form-data)

    rect rgb(240, 248, 255)
        Note over API,DB: 后端处理
        API->>FS: 保存视频到 MEDIA_ROOT/videos/
        API->>DB: 创建 Video 记录
        API->>DB: 创建 AsyncTaskItem × N<br/>(ASR, HLS, SSIM, 缩略图, OCR,<br/>分段, 知识点, 摘要, 导图, 嵌入)
    end

    API-->>FE: 201 Created + Video JSON
    FE-->>User: 显示视频卡片 + 任务进度
```

**关键细节**：
- 视频文件保存到 `MEDIA_ROOT/videos/<uuid>/` 目录
- 一次性创建所有任务节点，通过 `previous` 字段建立 DAG 依赖关系
- 无依赖的任务（ASR、HLS、SSIM）可以被 Worker 并行执行
- 前端通过轮询 `GET /api/tasks/video/<uuid>/` 获取进度

<div className="pipeline-step">

**步骤 1** — 文件保存：视频二进制数据写入磁盘

</div>
<div className="pipeline-step">

**步骤 2** — 记录创建：Video + AsyncTaskItem 写入 SQLite

</div>
<div className="pipeline-step">

**步骤 3** — 响应返回：前端收到任务列表，开始轮询进度

</div>

---

## 2. 视频处理流程 (任务管线)

Worker 进程持续轮询数据库，按 DAG 顺序执行任务。以下是完整的处理流水线：

```mermaid
sequenceDiagram
    participant W as ⚙️ Worker
    participant DB as 🗄️ SQLite
    participant COS as ☁️ 腾讯云 COS
    participant ASR as 🎤 DashScope ASR
    participant FF as 🎬 FFmpeg
    participant VL as 👁️ VL 模型
    participant LLM as 🧠 LLM
    participant VC as 📊 ChromaDB

    Note over W,DB: 阶段一：并行任务（无依赖）

    rect rgb(232, 245, 233)
        W->>DB: 读取 pending 任务
        W->>FF: task_hls_streaming<br/>视频 → HLS 切片
        FF-->>W: HLS 流文件就绪
        W->>DB: 更新 HLS 任务为 done

        W->>COS: 上传音频文件
        COS-->>W: 返回 file_url
        W->>ASR: task_extract_audio_and_transcript
        ASR-->>W: 返回转录结果 (JSON)
        W->>DB: 保存 VideoTranscript + TranscriptSentence

        W->>FF: task_ssim_move_detection<br/>多线程 SSIM 帧比较
        FF-->>W: 返回切换点时间戳列表
        W->>DB: 更新 SSIM 任务
    end

    Note over W,DB: 阶段二：缩略图 + OCR（依赖 SSIM）

    rect rgb(255, 243, 224)
        W->>FF: task_generate_thumbnails<br/>提取帧 → 200px + 1920px
        FF-->>W: 缩略图文件
        W->>DB: 保存 Thumbnail 记录

        W->>VL: task_slides_ocr<br/>发送 1920px 图片
        VL-->>W: 返回 OCR 文本
        W->>DB: 保存 SlideOCR 记录
    end

    Note over W,DB: 阶段三：知识提取（依赖 OCR）

    rect rgb(243, 229, 245)
        W->>W: task_hybrid_chunking<br/>幻灯片切换 + 静音 + 语义相似度
        W->>DB: 保存 VideoSection 记录

        W->>LLM: task_fine_grained_knowledge<br/>每个分段提取知识点
        LLM-->>W: 结构化知识点 JSON
        W->>DB: 保存 KnowledgePoint 记录

        W->>LLM: task_coarse_grained_summary<br/>整课摘要
        LLM-->>W: 摘要 JSON
        W->>DB: 保存 KnowledgeSummary 记录

        W->>LLM: task_generate_mindmap<br/>思维导图结构
        LLM-->>W: 树形 JSON
        W->>DB: 保存 KnowledgeMindmap 记录
    end

    Note over W,DB: 阶段四：向量化（依赖知识点）

    rect rgb(227, 242, 253)
        W->>W: task_embed_knowledge<br/>调用 sentence-transformers
        W->>VC: 批量 upsert 向量<br/>(knowledge_point, section,<br/>transcript, slide_ocr, summary)
        VC-->>W: 存储确认
        W->>DB: 最后一个任务标记 done
    end
```

**任务状态机**：

```mermaid
stateDiagram-v2
    [*] --> pending : 创建任务
    pending --> running : Worker 获取任务<br/>(SELECT FOR UPDATE SKIP LOCKED)
    running --> done : 执行成功
    running --> error : 执行失败
    pending --> error : 前置任务失败<br/>(级联失败)

    note right of running : 进度通过 progress<br/>字段实时更新 (0-100)
```

---

## 3. Fast RAG 聊天流程

当用户选择 Fast RAG 模式时，系统执行单次检索 + 生成：

```mermaid
sequenceDiagram
    actor User as 👤 用户
    participant FE as 🖥️ 前端
    participant API as 📡 Django API
    participant Engine as 🤖 RAG 引擎
    participant VDB as 📊 ChromaDB
    participant LLM as 🧠 LLM

    User->>FE: 输入问题："什么是梯度下降？"
    FE->>API: POST /api/chat/<session>/message/<br/>{mode: "fast_rag", question: "..."}

    rect rgb(232, 245, 253)
        Note over Engine,VDB: 阶段一：向量检索
        Engine->>VDB: query("什么是梯度下降",<br/>video_id=..., top_k=5)
        VDB-->>Engine: 返回 5 个相关文档<br/>+ 余弦相似度分数

        Engine->>Engine: 过滤：<br/>相似度 >= MIN_RELEVANCE_THRESHOLD (0.3)<br/>且数量 >= MIN_DOCUMENTS_REQUIRED (2)

        alt 检索质量不足
            Engine->>Engine: 降级为 LLM Direct 模式
        end
    end

    rect rgb(255, 243, 224)
        Note over Engine,LLM: 阶段二：生成回答
        Engine->>Engine: 组装上下文：<br/>- 视频摘要<br/>- 检索到的文档 (带编号)<br/>- 用户问题
        Engine->>LLM: 发送 system prompt + context
        LLM-->>Engine: 流式返回回答
    end

    Engine-->>API: SSE 事件流：<br/>text_delta / sources / done
    API-->>FE: SSE 转发
    FE-->>User: 实时显示回答 + 引用来源
```

**降级策略**：如果向量检索返回的文档太少或相似度太低，Fast RAG 会自动降级为 LLM Direct（纯 LLM 回答，不使用任何上下文），避免基于不相关内容生成误导性回答。

---

## 4. Agentic RAG 聊天流程

Agentic RAG 是更强大的模式，LLM 可以多轮调用工具来收集信息：

```mermaid
sequenceDiagram
    actor User as 👤 用户
    participant FE as 🖥️ 前端
    participant API as 📡 Django API
    participant Agent as 🤖 LangGraph Agent
    participant Tools as 🔧 工具集
    participant VDB as 📊 ChromaDB
    participant DB as 🗄️ SQLite
    participant LLM as 🧠 LLM

    User->>FE: 输入问题："这门课的助教是谁？"
    FE->>API: POST /api/chat/<session>/message/<br/>{mode: "agentic"}

    rect rgb(243, 229, 245)
        Note over Agent,LLM: ReAct 循环（最多 5 轮）

        Agent->>LLM: system_prompt + question + chat_history
        LLM-->>Agent: 决策：调用 search_slides("助教")

        Agent->>Tools: search_slides("助教")
        Tools->>VDB: 语义搜索 slide_ocr 内容
        VDB-->>Tools: 返回匹配的幻灯片文本
        Tools-->>Agent: "Office Hours: Tue 2-4pm<br/>TA: John Smith (john@uni.edu)"

        Agent->>LLM: 工具结果 + 原始问题
        LLM-->>Agent: 最终回答（含引用）

        Note over Agent: _sanitize_answer()<br/>移除虚构的引用标记
    end

    Agent-->>API: {answer, citations, thinking_steps}
    API-->>FE: SSE 事件流
    FE-->>User: 显示回答 + 思考过程 + 引用
```

**可用的 Agent 工具**：

| 工具名称 | 输入 | 输出 | 适用场景 |
|----------|------|------|---------|
| `search_knowledge` | query, top_k | 知识点、章节、转录文本 | 概念性问题 |
| `search_slides` | query, top_k | 幻灯片 OCR 文本 | 课程信息、联系方式 |
| `get_section_detail` | section_id | 完整章节内容 | 深入了解某一段 |
| `get_transcript_range` | start_sec, end_sec | 时间范围内转录文本 | 定位特定内容 |

**思考过程可视化**：Agent 的每一轮"思考→工具调用→观察"都会通过 SSE 发送给前端，用户可以看到 AI 是如何一步步找到答案的。

---

## 5. 数据存储全景 (Data at Rest)

处理完成后，数据分布在三个存储位置：

### SQLite 表结构

```mermaid
erDiagram
    Episode ||--o{ Video : "包含"
    Video ||--|| VideoTranscript : "转录"
    VideoTranscript ||--o{ TranscriptSentence : "句子"
    Video ||--o{ Thumbnail : "缩略图"
    Thumbnail ||--o| SlideOCR : "OCR"
    Video ||--o{ VideoSection : "分段"
    VideoSection ||--o{ KnowledgePoint : "知识点"
    Video ||--o| KnowledgeSummary : "摘要"
    Video ||--o| KnowledgeMindmap : "导图"
    Video ||--o{ AsyncTaskItem : "任务"
    Video ||--o{ ChatSession : "聊天"
    ChatSession ||--o{ ChatMessage : "消息"
    Video ||--o{ ChatSession : "属于"
```

**主要表说明**：

| 表名 | 记录示例 | 数据量级 |
|------|---------|---------|
| `Video` | id, title, file, duration | 每个视频 1 条 |
| `VideoTranscript` | file_url, format, sample_rate | 每个视频 1 条 |
| `TranscriptSentence` | text, begin_time, end_time | 每个视频 100-1000 条 |
| `Thumbnail` | image, image_high_res, time_second | 每个视频 10-50 张 |
| `SlideOCR` | ocr_text, time_second | 每个视频 10-50 条 |
| `VideoSection` | title, begin_time, end_time, transcript_text | 每个视频 5-20 段 |
| `KnowledgePoint` | title, summary, key_terms, importance | 每个视频 20-100 个 |
| `KnowledgeSummary` | overview, key_topics, learning_objectives | 每个视频 1 条 |
| `KnowledgeMindmap` | tree_data, react_flow_nodes, react_flow_edges | 每个视频 1 条 |
| `AsyncTaskItem` | func_name, status, progress, previous | 每个视频约 10 个 |
| `ChatSession` | video_id, title | 每个视频多个 |
| `ChatMessage` | role, content, citations | 每个会话多条 |

### ChromaDB 向量存储

所有知识内容在向量化后存入 ChromaDB 的单一 collection `lecture_knowledge`。

| `content_type` 元数据 | 来源 | 用途 |
|----------------------|------|------|
| `knowledge_point` | 细粒度 LLM 提取 | 精确概念检索 |
| `section` | 混合分段摘要 | 段落级语义搜索 |
| `transcript` | ASR 逐句转录 | 原文定位 |
| `slide_ocr` | 幻灯片 OCR 文本 | 视觉内容检索 |
| `lecture_summary` | 粗粒度课程摘要 | 主题概览 |

**过滤机制**：所有查询都通过 `video_id` 元数据过滤，确保不同视频的知识不会混淆。

### 文件系统

```
MEDIA_ROOT/
├── videos/                 # 原始视频文件
│   └── <uuid>/
│       └── lecture.mp4
├── streams/                # HLS 自适应流
│   └── <uuid>/
│       ├── master.m3u8
│       ├── 720p/
│       ├── 480p/
│       └── 360p/
├── thumbnails/             # 缩略图
│   ├── <uuid>.jpg          # 200px 网页展示
│   └── high_res/
│       └── <uuid>.jpg      # 1920px OCR 输入
├── audio/                  # 提取的音频文件
│   └── <uuid>.wav
└── chromadb/               # 向量数据库持久化
    └── ...
```

---

## 6. 数据流转总结

下图展示了数据从上传到最终输出的完整生命周期：

```mermaid
graph LR
    subgraph 输入
        Upload["📤 视频文件"]
    end

    subgraph 处理
        direction TB
        ASR["🎤 ASR 转录"]
        HLS["🎬 HLS 转码"]
        SSIM["🔍 幻灯片检测"]
        OCR["📝 幻灯片 OCR"]
        Chunk["📦 智能分段"]
        Extract["💡 知识提取"]
        Vectorize["🔢 向量化"]
    end

    subgraph 输出
        direction TB
        Player["🎬 视频播放"]
        Notes["📋 知识笔记"]
        Map["🗺️ 思维导图"]
        Chat["💬 AI 对话"]
    end

    Upload --> ASR & HLS & SSIM
    SSIM --> OCR --> Chunk --> Extract --> Vectorize
    ASR --> Player
    HLS --> Player
    Chunk --> Notes
    Extract --> Notes
    Extract --> Map
    Vectorize --> Chat

    style Upload fill:#4CAF50,color:#fff
    style Player fill:#2196F3,color:#fff
    style Notes fill:#FF9800,color:#fff
    style Map fill:#9C27B0,color:#fff
    style Chat fill:#E91E63,color:#fff
```

:::tip 下一步
- 想了解每种技术的具体版本和用途？请阅读 [技术栈](./tech-stack.md)
- 想了解任务管线的代码实现？请阅读 [任务管线](../backend/task-pipeline.md)
:::
