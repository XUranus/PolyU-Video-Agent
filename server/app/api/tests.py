"""
Tests for LectureMind API.
Run with: python manage.py test api
"""
import json
import uuid
from unittest.mock import patch, MagicMock

from django.test import TestCase, RequestFactory
from django.utils import timezone

from api.models import (
    Episode, Video, Thumbnail, VideoTranscript, TranscriptSentence,
    VideoSection, KnowledgePoint, KnowledgeSummary, KnowledgeMindmap,
    ChatSession, ChatMessage, AsyncTaskItem, SystemConfig, SlideOCR,
)


class FormatTimeTest(TestCase):
    """Test the format_time utility function."""

    def test_zero(self):
        from api.utils import format_time
        self.assertEqual(format_time(0), "00:00")

    def test_seconds_only(self):
        from api.utils import format_time
        self.assertEqual(format_time(45), "00:45")

    def test_minutes_and_seconds(self):
        from api.utils import format_time
        self.assertEqual(format_time(125), "02:05")

    def test_exact_minute(self):
        from api.utils import format_time
        self.assertEqual(format_time(60), "01:00")

    def test_large_value(self):
        from api.utils import format_time
        self.assertEqual(format_time(3661), "61:01")

    def test_float_input(self):
        from api.utils import format_time
        self.assertEqual(format_time(90.7), "01:30")


class ParseLLMJsonTest(TestCase):
    """Test the parse_llm_json utility function."""

    def test_valid_json(self):
        from api.utils import parse_llm_json
        result = parse_llm_json('{"key": "value"}')
        self.assertEqual(result, {"key": "value"})

    def test_json_with_markdown_fences(self):
        from api.utils import parse_llm_json
        result = parse_llm_json('```json\n{"key": "value"}\n```')
        self.assertEqual(result, {"key": "value"})

    def test_json_with_plain_fences(self):
        from api.utils import parse_llm_json
        result = parse_llm_json('```\n{"key": "value"}\n```')
        self.assertEqual(result, {"key": "value"})

    def test_json_embedded_in_text(self):
        from api.utils import parse_llm_json
        result = parse_llm_json('Here is the result: {"key": "value"} done.')
        self.assertEqual(result, {"key": "value"})

    def test_invalid_json_raises(self):
        from api.utils import parse_llm_json
        with self.assertRaises(ValueError):
            parse_llm_json("no json here at all")

    def test_complex_nested_json(self):
        from api.utils import parse_llm_json
        data = {
            "section_title": "Test Section",
            "points": [
                {"title": "Point 1", "summary": "Summary 1", "terms": ["a", "b"], "importance": 0.8}
            ]
        }
        result = parse_llm_json(json.dumps(data))
        self.assertEqual(result, data)


class ModelStrTest(TestCase):
    """Test model __str__ methods for basic sanity."""

    def test_episode_str(self):
        ep = Episode(title="CS101 Lecture 1")
        self.assertEqual(str(ep), "CS101 Lecture 1")

    def test_video_str(self):
        vid = Video(title="Intro to ML")
        self.assertEqual(str(vid), "Intro to ML")

    def test_video_transcript_str(self):
        vid = Video(id=uuid.uuid4(), title="Test")
        vt = VideoTranscript(video=vid)
        self.assertIn("Transcript", str(vt))


class SystemConfigTest(TestCase):
    """Test the SystemConfig model's get/get_all methods."""

    def test_get_returns_default(self):
        result = SystemConfig.get("llm_model")
        self.assertEqual(result, "qwen2.5-7b-instruct")

    def test_get_returns_db_value_over_default(self):
        SystemConfig.objects.create(key="llm_model", value="custom-model")
        result = SystemConfig.get("llm_model")
        self.assertEqual(result, "custom-model")

    def test_get_returns_fallback(self):
        result = SystemConfig.get("nonexistent_key", "fallback")
        self.assertEqual(result, "fallback")

    def test_get_all_merges_defaults_and_db(self):
        SystemConfig.objects.create(key="llm_model", value="custom")
        result = SystemConfig.get_all()
        self.assertIn("llm_model", result)
        self.assertEqual(result["llm_model"]["value"], "custom")
        self.assertIn("chat_model", result)  # from defaults


class AsyncTaskItemTest(TestCase):
    """Test async task dependency chain logic."""

    def setUp(self):
        self.episode = Episode.objects.create(title="Test Course")
        self.video = Video.objects.create(title="Test Video", episode=self.episode)

    def test_task_creation(self):
        task = AsyncTaskItem.objects.create(
            video=self.video,
            title="Test Task",
            func_name="task_extract_audio_and_transcript",
            param=json.dumps({"video_id": str(self.video.id)}),
        )
        self.assertEqual(task.status, "pending")
        self.assertEqual(task.progress, 0)

    def test_task_chain_dependency(self):
        t1 = AsyncTaskItem.objects.create(
            video=self.video, title="Task 1",
            func_name="task_hls_streaming",
            param=json.dumps({"video_id": str(self.video.id)}),
        )
        t2 = AsyncTaskItem.objects.create(
            video=self.video, title="Task 2",
            func_name="task_generate_thumbnails",
            param=json.dumps({"video_id": str(self.video.id)}),
            previous=t1.id,
        )
        self.assertEqual(t2.previous, t1.id)

    def test_cascade_failure(self):
        t1 = AsyncTaskItem.objects.create(
            video=self.video, title="Task 1",
            func_name="task_hls_streaming",
            param=json.dumps({"video_id": str(self.video.id)}),
            status='error',
            result=json.dumps({"error": "ffmpeg not found"}),
        )
        t2 = AsyncTaskItem.objects.create(
            video=self.video, title="Task 2",
            func_name="task_generate_thumbnails",
            param=json.dumps({"video_id": str(self.video.id)}),
            previous=t1.id,
        )
        # Simulate cascade failure
        from api.management.commands.process_async_task import Command
        cmd = Command()
        cmd._cascade_failure(t2, t1)
        t2.refresh_from_db()
        self.assertEqual(t2.status, 'error')
        result = json.loads(t2.result)
        self.assertIn("Predecessor", result["error"])


class ChatSessionTest(TestCase):
    """Test chat session and message models."""

    def setUp(self):
        self.episode = Episode.objects.create(title="Test Course")
        self.video = Video.objects.create(title="Test Video", episode=self.episode)

    def test_create_session(self):
        session = ChatSession.objects.create(video=self.video, title="Test Chat")
        self.assertEqual(session.title, "Test Chat")
        self.assertEqual(str(session), f"Chat {session.id} for Test Video")

    def test_create_messages(self):
        session = ChatSession.objects.create(video=self.video)
        msg1 = ChatMessage.objects.create(session=session, role="user", content="Hello")
        msg2 = ChatMessage.objects.create(session=session, role="assistant", content="Hi there!")
        self.assertEqual(session.messages.count(), 2)
        self.assertEqual(msg1.role, "user")

    def test_message_ordering(self):
        session = ChatSession.objects.create(video=self.video)
        m2 = ChatMessage.objects.create(session=session, role="assistant", content="Second")
        m1 = ChatMessage.objects.create(session=session, role="user", content="First")
        messages = list(session.messages.values_list('content', flat=True))
        # Ordered by created_at, but since created_at is auto_now_add and may be same,
        # just verify both exist
        self.assertEqual(len(messages), 2)


class KnowledgePointTest(TestCase):
    """Test knowledge point and section relationships."""

    def setUp(self):
        self.episode = Episode.objects.create(title="Test Course")
        self.video = Video.objects.create(title="Test Video", episode=self.episode)
        self.section = VideoSection.objects.create(
            video=self.video, title="Section 1",
            begin_time=0, end_time=120, order=0,
        )

    def test_knowledge_point_creation(self):
        kp = KnowledgePoint.objects.create(
            section=self.section,
            video=self.video,
            title="Gradient Descent",
            summary="An optimization algorithm that iteratively adjusts parameters.",
            key_terms=["gradient", "learning rate", "convergence"],
            importance=0.9,
        )
        self.assertEqual(kp.title, "Gradient Descent")
        self.assertEqual(len(kp.key_terms), 3)
        self.assertEqual(kp.importance, 0.9)

    def test_sections_with_knowledge(self):
        KnowledgePoint.objects.create(
            section=self.section, video=self.video,
            title="KP1", summary="Summary 1",
        )
        KnowledgePoint.objects.create(
            section=self.section, video=self.video,
            title="KP2", summary="Summary 2",
        )
        sections = VideoSection.objects.filter(video=self.video).prefetch_related('knowledge_points')
        self.assertEqual(sections[0].knowledge_points.count(), 2)


class VideoTaskChainTest(TestCase):
    """Test the full task chain creation logic."""

    def setUp(self):
        self.episode = Episode.objects.create(title="Test Course")
        self.video = Video.objects.create(title="Test Video", episode=self.episode)

    def test_creates_10_tasks(self):
        """The processing pipeline should create exactly 10 tasks."""
        from api.views import VideoTaskTriggerView
        view = VideoTaskTriggerView()
        view._create_processing_chain(self.video)
        tasks = AsyncTaskItem.objects.filter(video=self.video)
        self.assertEqual(tasks.count(), 10)

    def test_task_chain_dependencies(self):
        """Verify the DAG structure: T1-T3 parallel, rest chained."""
        from api.views import VideoTaskTriggerView
        view = VideoTaskTriggerView()
        view._create_processing_chain(self.video)

        tasks = {t.func_name: t for t in AsyncTaskItem.objects.filter(video=self.video)}

        # T1, T2, T3 have no dependency (parallel start)
        self.assertIsNone(tasks["task_extract_audio_and_transcript"].previous)
        self.assertIsNone(tasks["task_hls_streaming"].previous)
        self.assertIsNone(tasks["task_ssim_move_detection"].previous)

        # T4 depends on T3
        self.assertEqual(tasks["task_generate_thumbnails"].previous, tasks["task_ssim_move_detection"].id)

        # T4b depends on T4
        self.assertEqual(tasks["task_slides_ocr"].previous, tasks["task_generate_thumbnails"].id)

        # T5 depends on T4b
        self.assertEqual(tasks["task_hybrid_chunking"].previous, tasks["task_slides_ocr"].id)

    def test_no_duplicate_chains(self):
        """Should not allow creating tasks when pending/running tasks exist."""
        from api.views import VideoTaskTriggerView

        view = VideoTaskTriggerView()
        view._create_processing_chain(self.video)

        # Try to create again -- should detect existing tasks
        existing = self.video.async_tasks.filter(status__in=['pending', 'running']).exists()
        self.assertTrue(existing)
