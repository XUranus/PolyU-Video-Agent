---
id: backend-models
title: 数据模型
sidebar_label: 数据模型
---

# 数据模型

本文档详细介绍了 LectureMind 后端的全部 14 个 Django 模型。所有模型定义在 `server/app/api/models.py` 中。

## 模型总览

LectureMind 的数据模型可以分为五个功能域：

| 功能域 | 模型 | 说明 |
|--------|------|------|
| 视频管理 | `Episode`, `Video` | 视频及其所属课程 |
| 转录数据 | `VideoTranscript`, `TranscriptSentence` | ASR 语音识别结果 |
| 内容分析 | `Thumbnail`, `VideoSection`, `SlideOCR` | 缩略图、视频分段、幻灯片 OCR |
| 知识提取 | `KnowledgePoint`, `KnowledgeSummary`, `KnowledgeMindmap` | 知识点、摘要、思维导图 |
| 交互系统 | `ChatSession`, `ChatMessage` | RAG 智能问答 |
| 系统管理 | `AsyncTaskItem`, `SystemConfig` | 异步任务、系统配置 |

## 实体关系图（ER Diagram）

```mermaid
erDiagram
    Episode ||--o{ Video : "包含"
    Video ||--|| VideoTranscript : "转录"
    Video ||--o{ Thumbnail : "缩略图"
    Video ||--o{ VideoSection : "分段"
    Video ||--o{ KnowledgePoint : "知识点"
    Video ||--o| KnowledgeSummary : "摘要"
    Video ||--o| KnowledgeMindmap : "思维导图"
    Video ||--o{ SlideOCR : "幻灯片OCR"
    Video ||--o{ ChatSession : "聊天会话"
    Video ||--o{ AsyncTaskItem : "异步任务"

    VideoTranscript ||--o{ TranscriptSentence : "句子"
    Thumbnail ||--o| SlideOCR : "OCR"
    Thumbnail ||--o{ VideoSection : "代表幻灯片"
    VideoSection ||--o{ KnowledgePoint : "知识点"

    ChatSession ||--o{ ChatMessage : "消息"

    Episode {
        uuid id PK
        string title
        text description
        datetime created_at
    }

    Video {
        uuid id PK
        uuid episode_id FK
        string title
        file file
        float duration
        string cover
        datetime created_at
    }

    VideoTranscript {
        uuid video_id PK_FK
        url file_url
        string format
        int sample_rate
    }

    TranscriptSentence {
        uuid video_transcript_id FK
        int channel_id
        int sentence_id
        int begin_time
        int end_time
        string language
        string emotion
        text text
    }

    Thumbnail {
        uuid id PK
        uuid video_id FK
        float time_second
        image image
        image image_high_res
    }

    VideoSection {
        uuid id PK
        uuid video_id FK
        string title
        float begin_time
        float end_time
        text transcript_text
        uuid thumbnail_id FK
        int order
    }

    KnowledgePoint {
        uuid id PK
        uuid section_id FK
        uuid video_id FK
        string title
        text summary
        json key_terms
        float importance
        string embedding_id
        datetime created_at
    }

    KnowledgeSummary {
        uuid video_id PK_FK
        text overview
        json key_topics
        json learning_objectives
        json prerequisites
        string difficulty_level
        datetime created_at
        datetime updated_at
    }

    KnowledgeMindmap {
        uuid video_id PK_FK
        json tree_data
        json react_flow_nodes
        json react_flow_edges
        datetime created_at
        datetime updated_at
    }

    SlideOCR {
        uuid id PK
        uuid thumbnail_id FK
        uuid video_id FK
        text ocr_text
        float time_second
        datetime created_at
    }

    ChatSession {
        uuid id PK
        uuid video_id FK
        string title
        datetime created_at
        datetime updated_at
    }

    ChatMessage {
        uuid id PK
        uuid session_id FK
        string role
        text content
        json citations
        datetime created_at
    }

    AsyncTaskItem {
        uuid id PK
        uuid video_id FK
        string title
        text description
        string func_name
        text param
        text result
        uuid previous
        string status
        int progress
        datetime created_at
        datetime finished_at
    }

    SystemConfig {
        string key PK
        text value
        string description
        datetime updated_at
    }
```

## 模型层次结构

以下是 `Video` 为核心节点的模型层次树：

```
Episode
└── Video
    ├── VideoTranscript (一对一)
    │   └── TranscriptSentence (一对多)
    ├── Thumbnail (一对多)
    │   └── SlideOCR (一对一)
    ├── VideoSection (一对多)
    │   └── KnowledgePoint (一对多)
    ├── KnowledgePoint (一对多，反范式化 FK)
    ├── KnowledgeSummary (一对一)
    ├── KnowledgeMindmap (一对一)
    ├── SlideOCR (一对多，反范式化 FK)
    ├── ChatSession (一对多)
    │   └── ChatMessage (一对多)
    └── AsyncTaskItem (一对多)
```

---

## 逐模型详解

### Episode（课程/剧集）

**用途**：逻辑分组容器，代表一个课程系列或讲座集合。一个 Episode 可以包含多个 Video。

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | UUIDField (PK) | 主键，自动生成 |
| `title` | CharField(255) | 课程标题 |
| `description` | TextField | 课程描述（可为空） |
| `created_at` | DateTimeField | 创建时间，自动填充 |

- **排序**：按 `created_at` 降序（最新的在前）
- **级联删除**：当 Episode 被删除时，关联的 Video 的 `episode` 字段会被设为 `NULL`（`SET_NULL`）

---

### Video（视频）

**用途**：代表一个已上传的视频文件。是整个系统的核心实体，几乎所有其他模型都直接或间接关联到 Video。

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | UUIDField (PK) | 主键，自动生成 |
| `episode` | ForeignKey → Episode | 所属课程（可为空） |
| `title` | CharField(255) | 视频标题 |
| `file` | FileField | 视频文件，上传到 `videos/` 目录 |
| `duration` | FloatField | 视频时长（秒），默认 0.0 |
| `cover` | CharField(1024) | 封面图 URL（由缩略图任务自动设置） |
| `created_at` | DateTimeField | 创建时间，自动填充 |

- **排序**：按 `created_at` 降序
- **关联关系**：通过 `related_name` 可以反向查询：`video.thumbnails`、`video.sections`、`video.knowledge_points` 等

---

### VideoTranscript（视频转录）

**用途**：存储 ASR（自动语音识别）的元数据。与 Video 是**一对一**关系。

| 字段 | 类型 | 说明 |
|------|------|------|
| `video` | OneToOneField → Video (PK) | 主键即外键 |
| `file_url` | URLField | 处理后的音频文件 URL（COS 签名 URL） |
| `format` | CharField(50) | 音频编码格式 |
| `sample_rate` | IntegerField | 音频采样率（Hz） |

:::tip 主键即外键
`VideoTranscript` 使用 `OneToOneField` 作为主键，这意味着 `video_id` 既是主键也是外键。这是一种常见的 Django 一对一建模模式。
:::

---

### TranscriptSentence（转录句子）

**用途**：存储 ASR 输出的单条转录句子。一个 VideoTranscript 包含多个句子。

| 字段 | 类型 | 说明 |
|------|------|------|
| `video_transcript` | ForeignKey → VideoTranscript | 所属转录 |
| `channel_id` | IntegerField | 音频通道 ID |
| `sentence_id` | IntegerField | 句子在转录中的序号 |
| `begin_time` | IntegerField | 开始时间（**毫秒**） |
| `end_time` | IntegerField | 结束时间（**毫秒**） |
| `language` | CharField(10) | 语言代码 |
| `emotion` | CharField(20) | 检测到的情感（可为空） |
| `text` | TextField | 转录文本内容 |

- **排序**：按 `begin_time` 升序
- **索引**：`(video_transcript, begin_time)` 联合索引

:::warning 时间单位
`begin_time` 和 `end_time` 的单位是**毫秒**（不是秒）。在与 `VideoSection` 的秒级时间比较时需要转换。
:::

---

### Thumbnail（缩略图）

**用途**：从视频特定时间点截取的预览图片。每个缩略图有低分辨率（网页展示）和高分辨率（OCR 任务）两个版本。

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | UUIDField (PK) | 主键 |
| `video` | ForeignKey → Video | 所属视频 |
| `time_second` | FloatField | 截取时间点（秒） |
| `image` | ImageField | 低分辨率图片，存入 `thumbnails/` |
| `image_high_res` | ImageField | 高分辨率图片，存入 `thumbnails/high_res/` |

- **排序**：按 `time_second` 升序
- **索引**：`(video, time_second)` 联合索引

---

### SlideOCR（幻灯片 OCR）

**用途**：使用视觉语言模型（Qwen2.5-VL-72B）从幻灯片缩略图中提取的文字内容。

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | UUIDField (PK) | 主键 |
| `thumbnail` | OneToOneField → Thumbnail | 关联的缩略图 |
| `video` | ForeignKey → Video | 反范式化外键，便于直接按视频查询 |
| `ocr_text` | TextField | OCR 提取的原始文本 |
| `time_second` | FloatField | 时间戳（秒），从缩略图复制 |
| `created_at` | DateTimeField | 创建时间 |

- **索引**：`(video, time_second)` 联合索引
- **说明**：`video` 字段是反范式化的（冗余存储），目的是避免每次都通过 `thumbnail` 表做 JOIN 查询

---

### VideoSection（视频分段）

**用途**：由混合分块算法（hybrid chunker）生成的智能章节。结合了幻灯片切换检测和 ASR 转录的时间信息。

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | UUIDField (PK) | 主键 |
| `video` | ForeignKey → Video | 所属视频 |
| `title` | CharField(512) | AI 生成的章节标题 |
| `begin_time` | FloatField | 开始时间（秒） |
| `end_time` | FloatField | 结束时间（秒） |
| `transcript_text` | TextField | 拼接后的转录文本 |
| `thumbnail` | ForeignKey → Thumbnail | 代表性的幻灯片缩略图 |
| `order` | IntegerField | 章节排序索引 |

- **排序**：先按 `order`，再按 `begin_time`
- **索引**：`(video, begin_time)` 和 `(video, order)` 两个联合索引

---

### KnowledgePoint（知识点）

**用途**：由 LLM 从单个 VideoSection 中提取的细粒度知识。是 RAG 系统的核心数据单元。

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | UUIDField (PK) | 主键 |
| `section` | ForeignKey → VideoSection | 所属章节 |
| `video` | ForeignKey → Video | 反范式化外键 |
| `title` | CharField(512) | 知识点标题（简洁，3-8 词） |
| `summary` | TextField | 详细解释（2-3 句话） |
| `key_terms` | JSONField | 关键术语列表，默认 `[]` |
| `importance` | FloatField | 重要性评分 0.0-1.0，默认 0.5 |
| `embedding_id` | CharField(255) | 向量数据库中的引用 ID |
| `created_at` | DateTimeField | 创建时间 |

- **排序**：按 `section.order` 再按 `created_at`
- **索引**：`(video, section)` 和 `(video, created_at)`

---

### KnowledgeSummary（知识摘要）

**用途**：整个视频的粗粒度摘要，通过聚合所有章节的知识点由 LLM 生成。与 Video **一对一**。

| 字段 | 类型 | 说明 |
|------|------|------|
| `video` | OneToOneField → Video (PK) | 主键即外键 |
| `overview` | TextField | 概述段落（3-5 句话） |
| `key_topics` | JSONField | 主要话题列表，如 `["神经网络", "反向传播"]` |
| `learning_objectives` | JSONField | 学习目标列表 |
| `prerequisites` | JSONField | 前置知识列表 |
| `difficulty_level` | CharField(32) | 难度等级：`beginner`/`intermediate`/`advanced` |
| `created_at` | DateTimeField | 创建时间 |
| `updated_at` | DateTimeField | 更新时间（自动） |

---

### KnowledgeMindmap（知识思维导图）

**用途**：视频的层次化思维导图结构，由 LLM 生成。存储为 JSON 树形结构，前端使用 React Flow 渲染。

| 字段 | 类型 | 说明 |
|------|------|------|
| `video` | OneToOneField → Video (PK) | 主键即外键 |
| `tree_data` | JSONField | 思维导图树形 JSON |
| `react_flow_nodes` | JSONField | 预计算的 React Flow 节点数组 |
| `react_flow_edges` | JSONField | 预计算的 React Flow 边数组 |
| `created_at` | DateTimeField | 创建时间 |
| `updated_at` | DateTimeField | 更新时间 |

`tree_data` 的结构示例：
```json
{
  "id": "root",
  "label": "课程标题",
  "children": [
    {
      "id": "topic-1",
      "label": "主题名称",
      "children": [
        {"id": "sub-1-1", "label": "子主题", "children": []}
      ]
    }
  ]
}
```

---

### ChatSession（聊天会话）

**用途**：用户与 RAG 聊天机器人之间的对话会话。一个会话绑定到一个视频。

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | UUIDField (PK) | 主键 |
| `video` | ForeignKey → Video | 关联视频 |
| `title` | CharField(255) | 会话标题，默认 "New Chat" |
| `created_at` | DateTimeField | 创建时间 |
| `updated_at` | DateTimeField | 最后更新时间 |

- **排序**：按 `updated_at` 降序（最近活跃的在前）
- **索引**：`(video, -updated_at)`

---

### ChatMessage（聊天消息）

**用途**：聊天会话中的单条消息，支持 `user` 和 `assistant` 两种角色。

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | UUIDField (PK) | 主键 |
| `session` | ForeignKey → ChatSession | 所属会话 |
| `role` | CharField(16) | 角色：`user` 或 `assistant` |
| `content` | TextField | 消息内容（支持 Markdown） |
| `citations` | JSONField | 引用来源列表，默认 `[]` |
| `created_at` | DateTimeField | 创建时间 |

- **排序**：按 `created_at` 升序
- **索引**：`(session, created_at)`

---

### AsyncTaskItem（异步任务）

**用途**：任务管线中的一个工作单元。支持通过 `previous` 字段建立任务依赖链。

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | UUIDField (PK) | 主键 |
| `video` | ForeignKey → Video | 关联视频 |
| `title` | CharField(255) | 任务标题 |
| `description` | TextField | 任务描述 |
| `func_name` | CharField(64) | 要执行的任务函数名 |
| `param` | TextField | JSON 编码的输入参数 |
| `result` | TextField | JSON 编码的执行结果或错误信息 |
| `previous` | UUIDField | 前置任务的 UUID（依赖链） |
| `status` | CharField(32) | 状态：`pending`/`running`/`done`/`error` |
| `progress` | IntegerField | 进度百分比 0-100 |
| `created_at` | DateTimeField | 创建时间 |
| `finished_at` | DateTimeField | 完成时间（可为空） |

- **排序**：按 `created_at` 升序
- **索引**：`(status, created_at)`、`(previous)`、`(video, status)`

:::tip 任务依赖链
`previous` 字段存储前置任务的 UUID。当一个任务完成后，处理器会检查所有 `previous` 指向该任务的 pending 任务，将它们标记为可执行。如果前置任务失败，所有下游任务会级联失败。
:::

---

### SystemConfig（系统配置）

**用途**：键值对形式的系统配置存储（单例模式）。支持通过 API 动态修改，修改后自动同步到 `.env` 文件。

| 字段 | 类型 | 说明 |
|------|------|------|
| `key` | CharField(128) (PK) | 配置键名（主键） |
| `value` | TextField | 配置值（字符串形式） |
| `description` | CharField(512) | 人类可读的描述 |
| `updated_at` | DateTimeField | 最后更新时间 |

**内置默认配置项**：

| 键名 | 默认值 | 说明 |
|------|--------|------|
| `llm_model` | `qwen2.5-7b-instruct` | 管线任务使用的 LLM 模型 |
| `llm_api_base` | `https://dashscope.aliyuncs.com/compatible-mode/v1` | LLM API 地址 |
| `chat_model` | `qwen3-max` | 聊天/Agent 使用的模型 |
| `vl_model` | `qwen2.5-vl-72b-instruct` | 幻灯片 OCR 使用的视觉语言模型 |
| `dashscope_api_key` | (空) | DashScope API 密钥 |
| `cos_secret_id` | (空) | 腾讯云 COS SecretId |
| `cos_secret_key` | (空) | 腾讯云 COS SecretKey |
| `cos_region` | (空) | 腾讯云 COS 地域 |
| `cos_bucket` | (空) | 腾讯云 COS 存储桶名称 |

:::warning 敏感配置
`dashscope_api_key`、`cos_secret_id`、`cos_secret_key` 属于敏感配置，API 返回时会被掩码处理。
:::

---

## 设计要点总结

1. **UUID 主键**：所有模型使用 UUID 而非自增整数作为主键，避免了 ID 猜测和数据合并冲突
2. **反范式化外键**：`KnowledgePoint` 和 `SlideOCR` 同时持有 `video` 和 `section`/`thumbnail` 外键，以空间换查询效率
3. **JSON 字段**：灵活使用 `JSONField` 存储结构化数据（`key_terms`、`tree_data`、`citations` 等）
4. **索引优化**：高频查询路径上设置了联合索引
5. **级联策略**：使用 `CASCADE` 删除关联数据（视频删除时清理所有子数据），使用 `SET_NULL` 保留可选关联
