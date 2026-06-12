import json
import logging
import os
from typing import Any, Dict

from django.conf import settings
from django.db import connection
from django.http import StreamingHttpResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from rest_framework import generics, status
from rest_framework.decorators import api_view
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response

from .models import (
    Video, Thumbnail, VideoTranscript, VideoSection, KnowledgePoint,
    KnowledgeSummary, KnowledgeMindmap, SlideOCR, ChatSession, ChatMessage,
    Episode, AsyncTaskItem, SystemConfig,
)
from .serializers import (
    VideoSerializer, ThumbnailSerializer, VideoUploadSerializer,
    VideoTranscriptSerializer, VideoSectionSerializer,
    KnowledgePointSerializer, SectionWithKnowledgeSerializer,
    SlideOCRSerializer, KnowledgeSummarySerializer, KnowledgeMindmapSerializer,
    ChatSessionSerializer, ChatSessionDetailSerializer, ChatMessageSerializer,
    EpisodeSerializer, AsyncTaskItemSerializer, TriggerTaskSerializer,
    SystemConfigSerializer,
)

logger = logging.getLogger('LectureMind')


# ======================
# HEALTH CHECK
# ======================

@api_view(['GET'])
def health_check(request):
    db_ok = True
    try:
        connection.ensure_connection()
    except Exception:
        db_ok = False
    storage_ok = os.path.isdir(settings.MEDIA_ROOT)
    all_ok = db_ok and storage_ok
    return Response({
        "ok": all_ok, "ready": all_ok,
        "db": "connected" if db_ok else "error",
        "storage": settings.MEDIA_ROOT if storage_ok else "error",
    }, status=status.HTTP_200_OK if all_ok else status.HTTP_503_SERVICE_UNAVAILABLE)


# ======================
# VIDEO VIEWS
# ======================

class VideoListView(generics.ListAPIView):
    queryset = Video.objects.all()
    serializer_class = VideoSerializer

class VideoDetailView(generics.RetrieveAPIView):
    queryset = Video.objects.all()
    serializer_class = VideoSerializer

class VideoDeleteView(generics.DestroyAPIView):
    queryset = Video.objects.all()
    serializer_class = VideoSerializer

class VideoUpdateView(generics.UpdateAPIView):
    queryset = Video.objects.all()
    serializer_class = VideoSerializer
    lookup_field = 'id'

class ThumbnailListView(generics.ListAPIView):
    serializer_class = ThumbnailSerializer
    def get_queryset(self):
        return Thumbnail.objects.filter(video_id=self.kwargs['video_id']).order_by('time_second')
    def get_serializer_context(self) -> Dict[str, Any]:
        return {'request': self.request}


class SlideOCRListView(generics.ListAPIView):
    """List all slide OCR results for a video, ordered by time."""
    serializer_class = SlideOCRSerializer
    def get_queryset(self):
        return SlideOCR.objects.filter(video_id=self.kwargs['video_id']).order_by('time_second')
    def get_serializer_context(self) -> Dict[str, Any]:
        return {'request': self.request}


class VideoUploadView(generics.CreateAPIView):
    queryset = Video.objects.all()
    serializer_class = VideoUploadSerializer
    parser_classes = [MultiPartParser, FormParser]
    def post(self, request, *args, **kwargs) -> Response:
        # Validate file
        uploaded_file = request.FILES.get('file')
        if not uploaded_file:
            return Response({"error": "No file provided"}, status=status.HTTP_400_BAD_REQUEST)

        # Check file extension
        allowed_extensions = {'.mp4', '.mkv', '.avi', '.mov', '.webm', '.flv', '.wmv'}
        ext = os.path.splitext(uploaded_file.name)[1].lower()
        if ext not in allowed_extensions:
            return Response(
                {"error": f"Unsupported file type '{ext}'. Allowed: {', '.join(sorted(allowed_extensions))}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check file size (max 5GB)
        max_size = 5 * 1024 * 1024 * 1024
        if uploaded_file.size > max_size:
            return Response(
                {"error": f"File too large ({uploaded_file.size / 1024 / 1024 / 1024:.1f}GB). Maximum: 5GB"},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            os.makedirs(os.path.join(settings.MEDIA_ROOT, "videos"), exist_ok=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class VideoTaskTriggerView(generics.GenericAPIView):
    """POST /api/videos/process/ — Trigger the full processing pipeline."""
    serializer_class = TriggerTaskSerializer

    def post(self, request, *args, **kwargs) -> Response:
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        video_id = serializer.validated_data['id']
        video = get_object_or_404(Video, id=video_id)
        if video.async_tasks.filter(status__in=['pending', 'running']).exists():
            return Response(
                {"error": "Tasks already exist for this video (pending or running)."},
                status=status.HTTP_409_CONFLICT
            )
        try:
            self._create_processing_chain(video)
        except Exception as e:
            logger.exception("Failed to create task chain for video %s: %s", video.id, e)
            return Response({"error": "Task initialization failed", "detail": str(e)},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def _create_processing_chain(self, video: Video) -> None:
        """
        Task DAG (10 tasks):
          T1 (ASR), T2 (HLS), T3 (SSIM) — parallel
          T4 (Thumbnails) <- T3
          T4b (Slides OCR) <- T4
          T5 (Hybrid Chunking) <- T4b
          T6 (Fine-Grained Knowledge) <- T5
          T7 (Embed Knowledge) <- T6
          T8 (Coarse Summary) <- T7
          T9 (Mindmap) <- T8
        """
        t1 = AsyncTaskItem.objects.create(video=video, title="Extract audio & generate transcript",
            description="Extract audio, upload to COS, transcribe with Qwen-ASR",
            func_name="task_extract_audio_and_transcript",
            param=json.dumps({"video_id": str(video.id), "file": video.file.name}), previous=None)
        t2 = AsyncTaskItem.objects.create(video=video, title="Generate HLS",
            description="Generate HLS multi-resolution streaming",
            func_name="task_hls_streaming",
            param=json.dumps({"video_id": str(video.id), "file": video.file.name}), previous=None)
        t3 = AsyncTaskItem.objects.create(video=video, title="SSIM Motion Detection",
            description="Detect significant frame changes with SSIM",
            func_name="task_ssim_move_detection",
            param=json.dumps({"video_id": str(video.id), "file": video.file.name}), previous=None)
        t4 = AsyncTaskItem.objects.create(video=video, title="Generate thumbnails",
            func_name="task_generate_thumbnails",
            param=json.dumps({"video_id": str(video.id)}), previous=t3.id)
        t4b = AsyncTaskItem.objects.create(video=video, title="OCR slide text extraction",
            description="Extract text from slide images using Qwen2.5-VL-72B-Instruct",
            func_name="task_slides_ocr",
            param=json.dumps({"video_id": str(video.id)}), previous=t4.id)
        t5 = AsyncTaskItem.objects.create(video=video, title="Hybrid video chunking",
            func_name="task_hybrid_chunking",
            param=json.dumps({"video_id": str(video.id)}), previous=t4b.id)
        t6 = AsyncTaskItem.objects.create(video=video, title="Extract knowledge points",
            func_name="task_fine_grained_knowledge",
            param=json.dumps({"video_id": str(video.id)}), previous=t5.id)
        t7 = AsyncTaskItem.objects.create(video=video, title="Embed knowledge vectors",
            func_name="task_embed_knowledge",
            param=json.dumps({"video_id": str(video.id)}), previous=t6.id)
        t8 = AsyncTaskItem.objects.create(video=video, title="Generate coarse summary",
            func_name="task_coarse_grained_summary",
            param=json.dumps({"video_id": str(video.id)}), previous=t7.id)
        t9 = AsyncTaskItem.objects.create(video=video, title="Generate knowledge mindmap",
            func_name="task_generate_mindmap",
            param=json.dumps({"video_id": str(video.id)}), previous=t8.id)


# ======================
# TRANSCRIPT / SECTION / KNOWLEDGE VIEWS
# ======================

class TranscriptDetailView(generics.GenericAPIView):
    def get(self, request, video_id, format=None):
        try:
            vt = VideoTranscript.objects.get(video_id=video_id)
        except VideoTranscript.DoesNotExist:
            return Response({"error": "No transcript found."}, status=status.HTTP_404_NOT_FOUND)
        return Response(VideoTranscriptSerializer(vt).data)

class VideoSectionListView(generics.ListAPIView):
    serializer_class = VideoSectionSerializer
    def get_queryset(self):
        return VideoSection.objects.filter(video_id=self.kwargs['video_id']).order_by('order')

class KnowledgePointsByVideoView(generics.ListAPIView):
    serializer_class = KnowledgePointSerializer
    def get_queryset(self):
        return KnowledgePoint.objects.filter(video_id=self.kwargs['video_id']).select_related('section').order_by('section__order')

class KnowledgePointsBySectionView(generics.ListAPIView):
    serializer_class = KnowledgePointSerializer
    def get_queryset(self):
        return KnowledgePoint.objects.filter(section_id=self.kwargs['section_id']).select_related('section')

class SectionsWithKnowledgeView(generics.ListAPIView):
    serializer_class = SectionWithKnowledgeSerializer
    def get_queryset(self):
        return VideoSection.objects.filter(video_id=self.kwargs['video_id']).prefetch_related('knowledge_points').order_by('order')


# ======================
# SUMMARY + MINDMAP
# ======================

class KnowledgeSummaryDetailView(generics.GenericAPIView):
    def get(self, request, video_id, format=None):
        try:
            s = KnowledgeSummary.objects.get(video_id=video_id)
        except KnowledgeSummary.DoesNotExist:
            return Response({"error": "No summary available."}, status=status.HTTP_404_NOT_FOUND)
        return Response(KnowledgeSummarySerializer(s).data)

class KnowledgeMindmapDetailView(generics.GenericAPIView):
    def get(self, request, video_id, format=None):
        try:
            m = KnowledgeMindmap.objects.get(video_id=video_id)
        except KnowledgeMindmap.DoesNotExist:
            return Response({"error": "No mindmap available."}, status=status.HTTP_404_NOT_FOUND)
        return Response(KnowledgeMindmapSerializer(m).data)


# ======================
# CHAT VIEWS
# ======================

class ChatSessionListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/videos/<uuid>/chat/sessions/  — List sessions for a video
    POST /api/videos/<uuid>/chat/sessions/  — Create a new session
    """
    serializer_class = ChatSessionSerializer

    def get_queryset(self):
        return ChatSession.objects.filter(video_id=self.kwargs['video_id']).prefetch_related('messages')

    def perform_create(self, serializer):
        serializer.save(video_id=self.kwargs['video_id'])


class ChatSessionDetailView(generics.RetrieveDestroyAPIView):
    """
    GET    /api/chat/sessions/<uuid>/  — Retrieve session with messages
    DELETE /api/chat/sessions/<uuid>/  — Delete a session
    """
    queryset = ChatSession.objects.all()
    serializer_class = ChatSessionDetailSerializer


class ChatMessageListView(generics.ListAPIView):
    """GET /api/chat/sessions/<uuid>/messages/ — List messages in a session."""
    serializer_class = ChatMessageSerializer

    def get_queryset(self):
        return ChatMessage.objects.filter(session_id=self.kwargs['session_id'])


# CSRF exempt: SSE streaming endpoints cannot send CSRF tokens via EventSource.
# Security should be handled by API key/token authentication instead.
@csrf_exempt
@api_view(['POST'])
def chat_stream_view(request, video_id):
    """
    POST /api/videos/<uuid>/chat/stream/

    SSE streaming endpoint for RAG-powered chat.

    Request body:
    {
        "message": "What is gradient descent?",
        "session_id": "uuid" (optional — creates new session if omitted)
    }

    Response: text/event-stream with SSE events:
        event: token
        data: {"token": "partial text"}

        event: citations
        data: {"citations": [...]}

        event: done
        data: {"message_id": "uuid", "session_id": "uuid"}
    """
    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return Response({"error": "Invalid JSON body"}, status=400)

    message = body.get("message", "").strip()
    if not message:
        return Response({"error": "Message is required"}, status=400)

    # Get or create video
    video = get_object_or_404(Video, id=video_id)

    # Get or create session
    session_id = body.get("session_id")
    if session_id:
        try:
            session = ChatSession.objects.get(id=session_id, video=video)
        except ChatSession.DoesNotExist:
            return Response({"error": "Session not found"}, status=404)
    else:
        # Auto-create session with truncated question as title
        title = message[:80] + ("..." if len(message) > 80 else "")
        session = ChatSession.objects.create(video=video, title=title)

    # Save user message
    ChatMessage.objects.create(session=session, role='user', content=message)

    # Build chat history from session
    history = list(
        ChatMessage.objects.filter(session=session)
        .order_by('created_at')
        .values('role', 'content')
    )
    # Exclude the user message we just saved (it'll be in the RAG context)
    chat_history = [{"role": m["role"], "content": m["content"]} for m in history[:-1]]

    def sse_generator():
        from api.rag_engine import RAGEngine

        engine = RAGEngine(video_id=str(video_id))
        full_response = []
        citations = []

        try:
            for token, cit in engine.ask_stream(message, chat_history=chat_history):
                if cit is not None:
                    # Final yield with citations
                    citations = cit
                elif token:
                    full_response.append(token)
                    yield f"event: token\ndata: {json.dumps({'token': token})}\n\n"

            # Save assistant message with citations
            assistant_msg = ChatMessage.objects.create(
                session=session,
                role='assistant',
                content=''.join(full_response),
                citations=citations,
            )

            # Send citations event
            yield f"event: citations\ndata: {json.dumps({'citations': citations})}\n\n"

            # Send done event
            yield f"event: done\ndata: {json.dumps({'message_id': str(assistant_msg.id), 'session_id': str(session.id)})}\n\n"

        except Exception as e:
            logger.error(f"SSE chat stream error: {e}")
            error_msg = ChatMessage.objects.create(
                session=session, role='assistant',
                content="I encountered an error processing your question. Please try again.",
                citations=[],
            )
            yield f"event: error\ndata: {json.dumps({'error': 'An error occurred processing your question.', 'message_id': str(error_msg.id)})}\n\n"

    response = StreamingHttpResponse(
        sse_generator(),
        content_type='text/event-stream',
    )
    response['Cache-Control'] = 'no-cache'
    response['X-Accel-Buffering'] = 'no'
    return response


# Non-streaming chat fallback
# CSRF exempt: SSE streaming endpoints cannot send CSRF tokens via EventSource.
# Security should be handled by API key/token authentication instead.
@csrf_exempt
@api_view(['POST'])
def chat_ask_view(request, video_id):
    """
    POST /api/videos/<uuid>/chat/ask/

    Non-streaming RAG chat endpoint. Returns complete answer.

    Request body:
    {
        "message": "What is gradient descent?",
        "session_id": "uuid" (optional)
    }
    """
    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return Response({"error": "Invalid JSON body"}, status=400)

    message = body.get("message", "").strip()
    if not message:
        return Response({"error": "Message is required"}, status=400)

    video = get_object_or_404(Video, id=video_id)

    session_id = body.get("session_id")
    if session_id:
        try:
            session = ChatSession.objects.get(id=session_id, video=video)
        except ChatSession.DoesNotExist:
            return Response({"error": "Session not found"}, status=404)
    else:
        title = message[:80] + ("..." if len(message) > 80 else "")
        session = ChatSession.objects.create(video=video, title=title)

    ChatMessage.objects.create(session=session, role='user', content=message)

    history = list(
        ChatMessage.objects.filter(session=session)
        .order_by('created_at').values('role', 'content')
    )
    chat_history = [{"role": m["role"], "content": m["content"]} for m in history[:-1]]

    from api.rag_engine import RAGEngine
    engine = RAGEngine(video_id=str(video_id))
    answer, citations = engine.ask(message, chat_history=chat_history)

    assistant_msg = ChatMessage.objects.create(
        session=session, role='assistant', content=answer, citations=citations,
    )

    return Response({
        "answer": answer,
        "citations": citations,
        "session_id": str(session.id),
        "message_id": str(assistant_msg.id),
    })


# ======================
# EPISODE VIEWS
# ======================

class EpisodeListView(generics.ListAPIView):
    queryset = Episode.objects.all()
    serializer_class = EpisodeSerializer

class EpisodeDetailView(generics.RetrieveAPIView):
    queryset = Episode.objects.all()
    serializer_class = EpisodeSerializer

class EpisodeCreateView(generics.CreateAPIView):
    queryset = Episode.objects.all()
    serializer_class = EpisodeSerializer

class EpisodeDeleteView(generics.DestroyAPIView):
    queryset = Episode.objects.all()
    serializer_class = EpisodeSerializer

class EpisodeUpdateView(generics.UpdateAPIView):
    queryset = Episode.objects.all()
    serializer_class = EpisodeSerializer
    lookup_field = 'id'


# ======================
# ASYNC TASK VIEWS
# ======================

class AsyncTaskItemCreateView(generics.CreateAPIView):
    queryset = AsyncTaskItem.objects.all()
    serializer_class = AsyncTaskItemSerializer

class AsyncTaskItemDetailView(generics.RetrieveAPIView):
    queryset = AsyncTaskItem.objects.all()
    serializer_class = AsyncTaskItemSerializer

class AsyncTaskItemsByVideoView(generics.ListAPIView):
    serializer_class = AsyncTaskItemSerializer
    def get_queryset(self):
        return AsyncTaskItem.objects.filter(video_id=self.kwargs['pk'])


# ======================
# AGENT CHAT VIEWS
# ======================

# CSRF exempt: SSE streaming endpoints cannot send CSRF tokens via EventSource.
# Security should be handled by API key/token authentication instead.
@csrf_exempt
@api_view(['POST'])
def agent_chat_stream_view(request, video_id):
    """
    POST /api/videos/<uuid>/agent/stream/

    SSE streaming endpoint for LangGraph agent-powered chat with tool orchestration.

    Request body:
    {
        "message": "Explain gradient descent in detail",
        "session_id": "uuid" (optional)
    }

    Response: text/event-stream with SSE events:
        event: thinking      — agent reasoning step
        event: tool_call     — agent decided to call a tool
        event: tool_result   — tool execution result (preview)
        event: token         — final answer token
        event: citations     — source citations
        event: done          — completion with tool_steps + ids
    """
    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return Response({"error": "Invalid JSON body"}, status=400)

    message = body.get("message", "").strip()
    if not message:
        return Response({"error": "Message is required"}, status=400)

    video = get_object_or_404(Video, id=video_id)

    session_id = body.get("session_id")
    if session_id:
        try:
            session = ChatSession.objects.get(id=session_id, video=video)
        except ChatSession.DoesNotExist:
            return Response({"error": "Session not found"}, status=404)
    else:
        title = message[:80] + ("..." if len(message) > 80 else "")
        session = ChatSession.objects.create(video=video, title=title)

    ChatMessage.objects.create(session=session, role='user', content=message)

    history = list(
        ChatMessage.objects.filter(session=session)
        .order_by('created_at').values('role', 'content')
    )
    chat_history = [{"role": m["role"], "content": m["content"]} for m in history[:-1]]

    def sse_generator():
        from api.agent_graph import run_agent_stream

        full_response = []
        citations = []
        tool_steps = []

        try:
            for event in run_agent_stream(str(video_id), message, chat_history):
                event_type = event.get("event", "")
                data = event.get("data", {})

                if event_type == "token":
                    full_response.append(data.get("token", ""))

                if event_type == "citations":
                    citations = data.get("citations", [])

                if event_type == "done":
                    tool_steps = data.get("tool_steps", [])

                yield f"event: {event_type}\ndata: {json.dumps(data)}\n\n"

            # Save assistant message
            assistant_msg = ChatMessage.objects.create(
                session=session,
                role='assistant',
                content=''.join(full_response),
                citations=citations,
            )

            yield f"event: complete\ndata: {json.dumps({'message_id': str(assistant_msg.id), 'session_id': str(session.id)})}\n\n"

        except Exception as e:
            logger.error(f"Agent SSE error: {e}")
            error_msg = ChatMessage.objects.create(
                session=session, role='assistant',
                content="I encountered an error processing your question. Please try again.",
                citations=[],
            )
            yield f"event: error\ndata: {json.dumps({'error': 'An error occurred processing your question.', 'message_id': str(error_msg.id)})}\n\n"

    response = StreamingHttpResponse(sse_generator(), content_type='text/event-stream')
    response['Cache-Control'] = 'no-cache'
    response['X-Accel-Buffering'] = 'no'
    return response


# ======================
# COURSE (EPISODE) CHAT VIEWS
# ======================

# CSRF exempt: SSE streaming endpoints cannot send CSRF tokens via EventSource.
# Security should be handled by API key/token authentication instead.
@csrf_exempt
@api_view(['POST'])
def course_agent_stream_view(request, episode_id):
    """
    POST /api/episodes/<uuid>/agent/stream/

    SSE streaming agent chat across ALL videos in a course/episode.
    The agent can search knowledge from any video in the course.

    Request body:
    {
        "message": "Compare the concepts from lecture 1 and lecture 3",
        "session_id": "uuid" (optional)
    }
    """
    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return Response({"error": "Invalid JSON body"}, status=400)

    message_text = body.get("message", "").strip()
    if not message_text:
        return Response({"error": "Message is required"}, status=400)

    from .models import Episode
    episode = get_object_or_404(Episode, id=episode_id)
    video_ids = list(episode.videos.values_list('id', flat=True))

    if not video_ids:
        return Response({"error": "This course has no videos."}, status=400)

    # Use the first video for session storage (course-level sessions share this)
    first_video = episode.videos.first()

    session_id = body.get("session_id")
    if session_id:
        try:
            session = ChatSession.objects.get(id=session_id)
        except ChatSession.DoesNotExist:
            return Response({"error": "Session not found"}, status=404)
    else:
        title = message_text[:80] + ("..." if len(message_text) > 80 else "")
        session = ChatSession.objects.create(video=first_video, title=f"[Course] {title}")

    ChatMessage.objects.create(session=session, role='user', content=message_text)

    history = list(
        ChatMessage.objects.filter(session=session)
        .order_by('created_at').values('role', 'content')
    )
    chat_history = [{"role": m["role"], "content": m["content"]} for m in history[:-1]]

    def sse_generator():
        from api.agent_graph import CourseAgentRunner

        # Course-level runner — searches across all video IDs
        runner = CourseAgentRunner(
            video_ids=[str(vid) for vid in video_ids],
            episode_title=episode.title,
            chat_history=chat_history,
        )

        full_response = []
        citations = []
        tool_steps = []

        try:
            for event in runner.run_stream(message_text):
                event_type = event.get("event", "")
                data = event.get("data", {})

                if event_type == "token":
                    full_response.append(data.get("token", ""))
                if event_type == "citations":
                    citations = data.get("citations", [])
                if event_type == "done":
                    tool_steps = data.get("tool_steps", [])

                yield f"event: {event_type}\ndata: {json.dumps(data)}\n\n"

            assistant_msg = ChatMessage.objects.create(
                session=session, role='assistant',
                content=''.join(full_response), citations=citations,
            )
            yield f"event: complete\ndata: {json.dumps({'message_id': str(assistant_msg.id), 'session_id': str(session.id)})}\n\n"

        except Exception as e:
            logger.error(f"Course agent SSE error: {e}")
            error_msg = ChatMessage.objects.create(
                session=session, role='assistant',
                content="I encountered an error processing your question. Please try again.", citations=[],
            )
            yield f"event: error\ndata: {json.dumps({'error': 'An error occurred processing your question.', 'message_id': str(error_msg.id)})}\n\n"

    response = StreamingHttpResponse(sse_generator(), content_type='text/event-stream')
    response['Cache-Control'] = 'no-cache'
    response['X-Accel-Buffering'] = 'no'
    return response


# ======================
# TASK RETRY
# ======================

# CSRF exempt: SSE streaming endpoints cannot send CSRF tokens via EventSource.
# Security should be handled by API key/token authentication instead.
@csrf_exempt
@api_view(['POST'])
def task_retry_view(request, pk):
    """
    Retry a failed task and all cascade-blocked downstream tasks.
    POST /api/tasks/<uuid>/retry/
    
    Resets the target task and all its downstream dependents to 'pending'.
    """
    try:
        task = AsyncTaskItem.objects.get(id=pk)
    except AsyncTaskItem.DoesNotExist:
        return Response({"error": "Task not found"}, status=status.HTTP_404_NOT_FOUND)

    if task.status not in ('error',):
        return Response(
            {"error": f"Can only retry tasks with status 'error', got '{task.status}'"},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Collect this task + all downstream cascade-blocked tasks
    tasks_to_reset = [task]
    _collect_downstream_tasks(task, tasks_to_reset)

    reset_ids = []
    for t in tasks_to_reset:
        t.status = 'pending'
        t.result = ''
        t.finished_at = None
        t.save(update_fields=['status', 'result', 'finished_at'])
        reset_ids.append(str(t.id))

    logger.info(
        f"RETRY: Reset {len(reset_ids)} task(s) to pending for video {task.video_id}: "
        f"{', '.join(reset_ids)}"
    )

    return Response({
        "message": f"Reset {len(reset_ids)} task(s) to pending",
        "task_ids": reset_ids,
    }, status=status.HTTP_200_OK)


def _collect_downstream_tasks(parent_task, collected):
    """Recursively find all tasks that depend on the given task."""
    dependents = AsyncTaskItem.objects.filter(
        previous=parent_task.id,
        status='error'
    )
    for dep in dependents:
        if dep not in collected:
            collected.append(dep)
            _collect_downstream_tasks(dep, collected)

# ======================
# SYSTEM CONFIGURATION
# ======================

@api_view(['GET'])
def system_config_list(request):
    """Get all system configuration with defaults. Secret values are masked."""
    from api.config_utils import ConfigManager

    all_config = ConfigManager.get_all(include_secrets=False)
    result = []
    for key, info in all_config.items():
        result.append({
            "key": key,
            "value": info["value"],
            "description": info.get("description", ""),
            "is_secret": info.get("is_secret", False),
            "source": info.get("source", "default"),
        })
    return Response(result)


@api_view(['POST'])
def system_config_update(request):
    """Update one or more configuration values. Persists to both DB and .env file."""
    from api.config_utils import ConfigManager

    configs = request.data if isinstance(request.data, list) else [request.data]
    updated = []

    for item in configs:
        key = item.get("key")
        value = item.get("value", "")
        if not key:
            continue

        # Get description if provided, otherwise use default
        desc = item.get("description", "")

        # Update using ConfigManager (persists to both DB and .env)
        success = ConfigManager.set(key, value, description=desc, persist_to_env=True)

        if success:
            updated.append({
                "key": key,
                "value": value,
                "description": desc or ConfigManager.MODEL_CONFIG_KEYS.get(key, ("", ""))[1]
            })

    # Reset LLM client singleton so new config takes effect immediately
    ConfigManager.reset_llm_client()

    return Response({
        "updated": updated,
        "count": len(updated),
        "persisted_to_env": True
    })


@api_view(['POST'])
def system_config_sync_from_env(request):
    """Sync all configuration from .env file to database."""
    from api.config_utils import ConfigManager

    results = ConfigManager.sync_from_env()

    success_count = sum(1 for success in results.values() if success)
    failed_count = len(results) - success_count

    # Reset LLM client singleton
    ConfigManager.reset_llm_client()

    return Response({
        "synced": results,
        "success_count": success_count,
        "failed_count": failed_count,
        "total": len(results)
    })

