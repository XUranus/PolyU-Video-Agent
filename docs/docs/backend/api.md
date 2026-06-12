---
id: backend-api
title: REST API 参考
sidebar_label: API 参考
---

# REST API 参考

本文档列出 LectureMind 后端提供的所有 REST API 端点。所有端点以 `/api/` 为前缀。

## API 设计模式

LectureMind 的 API 遵循以下设计原则：

- **DRF 通用视图**：大部分端点使用 `generics.ListAPIView`、`generics.CreateAPIView` 等通用视图
- **URL 命名约定**：`/api/{资源名}/` 为列表，`/api/{资源名}/{id}/` 为单个资源
- **SSE 流式响应**：聊天相关端点使用 Server-Sent Events 实现实时流式输出
- **无认证**：当前版本未实现用户认证系统（适用于本地部署场景）

## 通用响应格式

**成功响应**：直接返回 JSON 对象或数组

**错误响应**：
```json
{
  "error": "错误描述信息"
}
```

---

## 健康检查

### GET /api/health/

检查系统健康状态（数据库连接和存储目录）。

**响应示例**（200 OK）：
```json
{
  "ok": true,
  "ready": true,
  "db": "connected",
  "storage": "/path/to/media"
}
```

**响应示例**（503 Service Unavailable）：
```json
{
  "ok": false,
  "ready": false,
  "db": "error",
  "storage": "error"
}
```

---

## 视频（Videos）

### GET /api/videos/

获取所有视频列表。

**响应**（200 OK）：
```json
[
  {
    "id": "uuid",
    "cover": "/media/thumbnails/xxx.jpg",
    "cover_url": "http://host/media/thumbnails/xxx.jpg",
    "title": "Lecture 1",
    "video_url": "http://host/media/videos/xxx.mp4",
    "duration": 3600.5
  }
]
```

---

### POST /api/videos/upload/

上传视频文件。

**请求**：`multipart/form-data`

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `title` | string | 是 | 视频标题 |
| `file` | file | 是 | 视频文件 |
| `episode` | uuid | 否 | 所属课程 ID |

**支持的文件格式**：`.mp4`, `.mkv`, `.avi`, `.mov`, `.webm`, `.flv`, `.wmv`

**文件大小限制**：5 GB

**响应**（201 Created）：
```json
{
  "id": "uuid",
  "cover": null,
  "cover_url": null,
  "title": "Lecture 1",
  "video_url": "http://host/media/videos/xxx.mp4",
  "duration": 0.0
}
```

**错误响应**（400 Bad Request）：
```json
{"error": "No file provided"}
{"error": "Unsupported file type '.txt'. Allowed: .avi, .flv, .mkv, .mov, .mp4, .webm, .wmv"}
{"error": "File too large (6.0GB). Maximum: 5GB"}
```

**curl 示例**：
```bash
curl -X POST http://localhost:8000/api/videos/upload/ \
  -F "title=Lecture 1" \
  -F "file=@/path/to/video.mp4" \
  -F "episode=<episode-uuid>"
```

---

### GET /api/videos/{uuid}/

获取单个视频详情。

**响应**（200 OK）：同视频列表中的单个对象格式。

---

### PUT /api/videos/update/{uuid}/

更新视频信息。

**请求体**：
```json
{
  "title": "新标题"
}
```

---

### DELETE /api/videos/delete/{uuid}/

删除视频及其所有关联数据（级联删除）。

**响应**（204 No Content）

---

### POST /api/videos/process/

触发视频处理管线（创建 10 个异步任务链）。

**请求体**：
```json
{
  "id": "video-uuid"
}
```

**响应**（201 Created）：
```json
{
  "id": "video-uuid"
}
```

**错误响应**：
- **409 Conflict**：该视频已有正在运行或等待中的任务
- **400 Bad Request**：视频 ID 不存在

**curl 示例**：
```bash
curl -X POST http://localhost:8000/api/videos/process/ \
  -H "Content-Type: application/json" \
  -d '{"id": "video-uuid"}'
```

---

## 视频子资源

### GET /api/videos/{uuid}/thumbnails/

获取视频的所有缩略图。

**响应**（200 OK）：
```json
[
  {
    "id": "uuid",
    "time_second": 12.5,
    "image_url": "http://host/media/thumbnails/xxx.jpg"
  }
]
```

---

### GET /api/videos/{uuid}/slide-ocr/

获取视频的所有幻灯片 OCR 结果。

**响应**（200 OK）：
```json
[
  {
    "id": "uuid",
    "thumbnail": "thumbnail-uuid",
    "video": "video-uuid",
    "ocr_text": "Extracted text content...",
    "time_second": 12.5,
    "thumbnail_url": "http://host/media/thumbnails/xxx.jpg",
    "created_at": "2024-01-01T00:00:00Z"
  }
]
```

---

### GET /api/videos/{uuid}/transcript/

获取视频的 ASR 转录数据（含所有句子）。

**响应**（200 OK）：
```json
{
  "video_id": "uuid",
  "file_url": "https://cos.xxx/audio/uuid.wav",
  "format": "wav",
  "sample_rate": 16000,
  "sentences": [
    {
      "channel_id": 0,
      "sentence_id": 1,
      "begin_time": 0,
      "end_time": 5000,
      "language": "en",
      "emotion": "neutral",
      "text": "Hello and welcome to this lecture."
    }
  ]
}
```

---

### GET /api/videos/{uuid}/sections/

获取视频的所有章节（按顺序排列）。

**响应**（200 OK）：
```json
[
  {
    "id": "uuid",
    "video": "video-uuid",
    "title": "Introduction",
    "begin_time": 0.0,
    "end_time": 120.5,
    "transcript_text": "Hello and welcome...",
    "thumbnail_url": "http://host/media/thumbnails/xxx.jpg",
    "order": 0
  }
]
```

---

### GET /api/videos/{uuid}/knowledge/

获取视频的所有知识点（扁平列表）。

**响应**（200 OK）：
```json
[
  {
    "id": "uuid",
    "section": "section-uuid",
    "video": "video-uuid",
    "title": "Gradient Descent",
    "summary": "Gradient descent is an optimization algorithm...",
    "key_terms": ["gradient", "learning rate", "convergence"],
    "importance": 0.9,
    "created_at": "2024-01-01T00:00:00Z",
    "section_title": "Optimization Methods",
    "section_order": 2,
    "begin_time": 240.0,
    "end_time": 360.0
  }
]
```

---

### GET /api/videos/{uuid}/knowledge/grouped/

获取视频的章节列表，每个章节嵌套包含其知识点。

**响应**（200 OK）：
```json
[
  {
    "id": "section-uuid",
    "video": "video-uuid",
    "title": "Optimization Methods",
    "begin_time": 240.0,
    "end_time": 360.0,
    "transcript_text": "...",
    "thumbnail_url": "http://...",
    "order": 2,
    "knowledge_points": [
      {
        "id": "kp-uuid",
        "title": "Gradient Descent",
        "summary": "...",
        "key_terms": ["gradient"],
        "importance": 0.9,
        ...
      }
    ]
  }
]
```

---

### GET /api/videos/{uuid}/summary/

获取视频级别的知识摘要。

**响应**（200 OK）：
```json
{
  "video": "video-uuid",
  "overview": "This lecture covers...",
  "key_topics": ["Neural Networks", "Backpropagation", "Optimization"],
  "learning_objectives": ["Understand gradient descent", "Implement backpropagation"],
  "prerequisites": ["Linear algebra basics", "Calculus fundamentals"],
  "difficulty_level": "intermediate",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

**404 响应**：`{"error": "No summary available."}`

---

### GET /api/videos/{uuid}/mindmap/

获取视频的思维导图数据。

**响应**（200 OK）：
```json
{
  "video": "video-uuid",
  "tree_data": {"id": "root", "label": "...", "children": [...]},
  "react_flow_nodes": [{"id": "root", "position": {...}, "data": {...}, "style": {...}}],
  "react_flow_edges": [{"id": "e-root-topic1", "source": "root", "target": "topic1"}],
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

**404 响应**：`{"error": "No mindmap available."}`

---

## 聊天（Chat）

### GET /api/videos/{uuid}/chat/sessions/

获取视频的所有聊天会话列表。

**响应**（200 OK）：
```json
[
  {
    "id": "session-uuid",
    "video": "video-uuid",
    "title": "What is gradient descent?",
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z",
    "message_count": 4
  }
]
```

---

### POST /api/videos/{uuid}/chat/sessions/

创建新的聊天会话。

**请求体**：
```json
{
  "title": "My Chat Session"
}
```

---

### GET /api/chat/sessions/{uuid}/

获取聊天会话详情（包含所有消息）。

**响应**（200 OK）：
```json
{
  "id": "session-uuid",
  "video": "video-uuid",
  "title": "My Chat Session",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z",
  "messages": [
    {
      "id": "msg-uuid",
      "session": "session-uuid",
      "role": "user",
      "content": "What is gradient descent?",
      "citations": [],
      "created_at": "2024-01-01T00:00:00Z"
    },
    {
      "id": "msg-uuid",
      "session": "session-uuid",
      "role": "assistant",
      "content": "Gradient descent is...",
      "citations": [{"title": "...", "begin_time": 120.0}],
      "created_at": "2024-01-01T00:01:00Z"
    }
  ]
}
```

---

### DELETE /api/chat/sessions/{uuid}/

删除聊天会话及其所有消息。

---

### GET /api/chat/sessions/{uuid}/messages/

获取会话中的消息列表。

---

### POST /api/videos/{uuid}/chat/stream/

SSE 流式 RAG 聊天端点。

**请求体**：
```json
{
  "message": "什么是梯度下降？",
  "session_id": "session-uuid (可选)"
}
```

如果省略 `session_id`，会自动创建新会话（以用户消息前 80 个字符作为标题）。

**响应**：`text/event-stream`

```
event: token
data: {"token": "梯度"}

event: token
data: {"token": "下降"}

event: token
data: {"token": "是..."}

event: citations
data: {"citations": [{"title": "...", "section_title": "...", "begin_time": 120.0}]}

event: done
data: {"message_id": "uuid", "session_id": "uuid"}
```

**curl 示例**：
```bash
curl -N -X POST http://localhost:8000/api/videos/{uuid}/chat/stream/ \
  -H "Content-Type: application/json" \
  -d '{"message": "What is gradient descent?"}'
```

---

### POST /api/videos/{uuid}/chat/ask/

非流式 RAG 聊天端点（等待完整回答后返回）。

**请求体**：同 `/chat/stream/`

**响应**（200 OK）：
```json
{
  "answer": "Gradient descent is an optimization algorithm...",
  "citations": [...],
  "session_id": "uuid",
  "message_id": "uuid"
}
```

---

### POST /api/videos/{uuid}/agent/stream/

SSE 流式 Agent 聊天端点（基于 LangGraph，支持工具调用）。

**请求体**：同 `/chat/stream/`

**响应**：`text/event-stream`，事件类型包括：
- `thinking` -- Agent 推理步骤
- `tool_call` -- Agent 决定调用工具
- `tool_result` -- 工具执行结果
- `token` -- 最终回答的 token
- `citations` -- 引用来源
- `done` -- 完成（含 tool_steps）

---

### POST /api/episodes/{uuid}/agent/stream/

SSE 流式课程级 Agent 聊天端点。可以跨该课程下所有视频搜索知识。

**请求体**：同上

---

## 课程（Episodes）

### GET /api/episodes/

获取所有课程列表（包含关联的视频）。

**响应**（200 OK）：
```json
[
  {
    "id": "uuid",
    "title": "Machine Learning 101",
    "description": "Intro to ML",
    "created_at": "2024-01-01T00:00:00Z",
    "videos": [
      {
        "id": "uuid",
        "title": "Lecture 1",
        "video_url": "...",
        "duration": 3600.0,
        ...
      }
    ]
  }
]
```

---

### POST /api/episodes/new/

创建新课程。

**请求体**：
```json
{
  "title": "Machine Learning 101",
  "description": "Introduction to machine learning concepts"
}
```

---

### GET /api/episodes/{uuid}/

获取课程详情。

---

### PUT /api/episodes/update/{uuid}/

更新课程信息。

---

### DELETE /api/episodes/delete/{uuid}/

删除课程。

---

## 章节（Sections）

### GET /api/sections/{uuid}/knowledge/

获取指定章节的所有知识点。

---

## 任务（Tasks）

### GET /api/tasks/video/{uuid}/

获取指定视频的所有异步任务。

**响应**（200 OK）：
```json
[
  {
    "id": "uuid",
    "video": "video-uuid",
    "title": "Extract audio & generate transcript",
    "description": "Extract audio, upload to COS, transcribe with Qwen-ASR",
    "func_name": "task_extract_audio_and_transcript",
    "result": "{\"video_id\": \"...\", ...}",
    "previous": null,
    "created_at": "2024-01-01T00:00:00Z",
    "finished_at": "2024-01-01T00:05:00Z",
    "status": "done",
    "progress": 100
  }
]
```

---

### POST /api/tasks/new/

创建新的异步任务。

**请求体**：
```json
{
  "video": "video-uuid",
  "title": "My Task",
  "func_name": "task_extract_audio_and_transcript",
  "param": "{\"video_id\": \"uuid\", \"file\": \"videos/xxx.mp4\"}",
  "previous": null
}
```

---

### GET /api/tasks/{uuid}/

获取单个任务详情。

---

### POST /api/tasks/{uuid}/retry/

重试失败的任务及其所有级联阻塞的下游任务。

**响应**（200 OK）：
```json
{
  "message": "Reset 3 task(s) to pending",
  "task_ids": ["uuid1", "uuid2", "uuid3"]
}
```

**错误响应**：
- **400 Bad Request**：只能重试 `error` 状态的任务
- **404 Not Found**：任务不存在

**curl 示例**：
```bash
curl -X POST http://localhost:8000/api/tasks/{uuid}/retry/
```

---

## 系统配置（Config）

### GET /api/config/

获取所有系统配置（敏感值会被掩码处理）。

**响应**（200 OK）：
```json
[
  {
    "key": "llm_model",
    "value": "qwen2.5-7b-instruct",
    "description": "Default LLM model for task pipeline",
    "is_secret": false,
    "source": "default"
  },
  {
    "key": "dashscope_api_key",
    "value": "sk-****",
    "description": "DashScope API key for LLM and ASR",
    "is_secret": true,
    "source": "database"
  }
]
```

---

### POST /api/config/update/

更新一个或多个配置值。会同时更新数据库和 `.env` 文件。

**请求体**（单个更新）：
```json
{
  "key": "llm_model",
  "value": "qwen2.5-14b-instruct",
  "description": "Default LLM model for task pipeline"
}
```

**请求体**（批量更新）：
```json
[
  {"key": "llm_model", "value": "qwen2.5-14b-instruct"},
  {"key": "chat_model", "value": "qwen3-max"}
]
```

**响应**（200 OK）：
```json
{
  "updated": [
    {"key": "llm_model", "value": "qwen2.5-14b-instruct", "description": "..."}
  ],
  "count": 1,
  "persisted_to_env": true
}
```

:::tip 即时生效
更新配置后，LLM 客户端会自动重置，新配置立即生效，无需重启服务。
:::

---

### POST /api/config/sync-from-env/

从 `.env` 文件同步所有配置到数据库。

**响应**（200 OK）：
```json
{
  "synced": {
    "dashscope_api_key": true,
    "llm_model": true,
    "cos_region": false
  },
  "success_count": 2,
  "failed_count": 1,
  "total": 3
}
```

---

## 端点速查表

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/health/` | 健康检查 |
| GET | `/api/videos/` | 视频列表 |
| POST | `/api/videos/upload/` | 上传视频 |
| GET | `/api/videos/{id}/` | 视频详情 |
| PUT | `/api/videos/update/{id}/` | 更新视频 |
| DELETE | `/api/videos/delete/{id}/` | 删除视频 |
| POST | `/api/videos/process/` | 触发处理管线 |
| GET | `/api/videos/{id}/thumbnails/` | 缩略图列表 |
| GET | `/api/videos/{id}/slide-ocr/` | 幻灯片 OCR |
| GET | `/api/videos/{id}/transcript/` | 转录数据 |
| GET | `/api/videos/{id}/sections/` | 章节列表 |
| GET | `/api/videos/{id}/knowledge/` | 知识点列表 |
| GET | `/api/videos/{id}/knowledge/grouped/` | 按章节分组的知识点 |
| GET | `/api/videos/{id}/summary/` | 知识摘要 |
| GET | `/api/videos/{id}/mindmap/` | 思维导图 |
| GET | `/api/videos/{id}/chat/sessions/` | 聊天会话列表 |
| POST | `/api/videos/{id}/chat/sessions/` | 创建聊天会话 |
| POST | `/api/videos/{id}/chat/stream/` | 流式 RAG 聊天 |
| POST | `/api/videos/{id}/chat/ask/` | 非流式 RAG 聊天 |
| POST | `/api/videos/{id}/agent/stream/` | Agent 流式聊天 |
| POST | `/api/episodes/{id}/agent/stream/` | 课程级 Agent 聊天 |
| GET | `/api/chat/sessions/{id}/` | 会话详情（含消息） |
| DELETE | `/api/chat/sessions/{id}/` | 删除会话 |
| GET | `/api/chat/sessions/{id}/messages/` | 消息列表 |
| GET | `/api/episodes/` | 课程列表 |
| POST | `/api/episodes/new/` | 创建课程 |
| GET | `/api/episodes/{id}/` | 课程详情 |
| PUT | `/api/episodes/update/{id}/` | 更新课程 |
| DELETE | `/api/episodes/delete/{id}/` | 删除课程 |
| GET | `/api/sections/{id}/knowledge/` | 章节知识点 |
| GET | `/api/tasks/video/{id}/` | 视频任务列表 |
| POST | `/api/tasks/new/` | 创建任务 |
| GET | `/api/tasks/{id}/` | 任务详情 |
| POST | `/api/tasks/{id}/retry/` | 重试任务 |
| GET | `/api/config/` | 获取配置 |
| POST | `/api/config/update/` | 更新配置 |
| POST | `/api/config/sync-from-env/` | 同步 .env 配置 |
