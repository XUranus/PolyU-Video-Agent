# server.py
"""
Main Django application entry point for the PolyU Video Agent backend.

This module configures and runs the Django web server that provides RESTful APIs
for video processing, including video upload, analysis, and query functionalities.
The actual business logic is implemented in dedicated views and services; this
file focuses on server setup and URL routing.

Note:
    This file is intended to be used with Django's built-in development server
    via `python server.py runserver`. For production, use a proper WSGI server.
"""

import os
import sys
import django
from django.conf import settings
from django.core.management import execute_from_command_line
from django.urls import path
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
import json
from typing import Any, Dict


# ----------------------------
# Django Settings Configuration
# ----------------------------

def configure_django_settings() -> None:
    """
    Configures minimal Django settings required to run the server.

    This inline configuration avoids the need for a separate settings.py file
    during prototyping. In a full project, these settings should be moved to
    a dedicated settings module.
    """
    if not settings.configured:
        settings.configure(
            DEBUG=True,
            SECRET_KEY='polyu-video-agent-dev-secret-key-2026',
            ROOT_URLCONF=__name__,
            ALLOWED_HOSTS=['*'],
            INSTALLED_APPS=[
                'django.contrib.contenttypes',
                'django.contrib.auth',
            ],
            MIDDLEWARE=[
                'django.middleware.common.CommonMiddleware',
                'django.middleware.csrf.CsrfViewMiddleware',
                'django.middleware.clickjacking.XFrameOptionsMiddleware',
            ],
            DATABASES={
                'default': {
                    'ENGINE': 'django.db.backends.sqlite3',
                    'NAME': ':memory:',
                }
            },
            USE_TZ=True,
            LOGGING={
                'version': 1,
                'disable_existing_loggers': False,
                'handlers': {
                    'console': {
                        'class': 'logging.StreamHandler',
                    },
                },
                'root': {
                    'handlers': ['console'],
                },
            },
        )
        django.setup()


# ----------------------------
# API Views
# ----------------------------

@method_decorator(csrf_exempt, name='dispatch')
class HealthCheckView(View):
    """
    A simple health check endpoint.

    Returns:
        JsonResponse: A JSON response indicating the service status.
    """

    def get(self, request) -> JsonResponse:
        """
        Handle GET requests to the health check endpoint.

        Returns:
            JsonResponse: {"status": "ok", "service": "PolyU Video Agent"}
        """
        return JsonResponse({
            "status": "ok",
            "service": "PolyU Video Agent"
        })


@method_decorator(csrf_exempt, name='dispatch')
class VideoUploadView(View):
    """
    Handles video file uploads.

    Note:
        Actual file handling and storage logic is pending implementation.
    """

    def post(self, request) -> JsonResponse:
        """
        Handle POST requests to upload a video file.

        TODO:
            - Implement secure file upload with validation
            - Store video metadata in database
            - Trigger background processing pipeline

        Returns:
            JsonResponse: Confirmation of upload receipt or error.
        """
        # TODO: Implement file upload logic
        return JsonResponse({
            "message": "Video upload endpoint received (not implemented)",
            "video_id": "temp_id_12345"
        }, status=202)


@method_decorator(csrf_exempt, name='dispatch')
class VideoQueryView(View):
    """
    Processes natural language queries about uploaded videos.

    Note:
        Query processing and Video-RAG integration are pending.
    """

    def post(self, request) -> JsonResponse:
        """
        Handle POST requests containing a query about a video.

        Expected JSON body:
            {
                "video_id": "string",
                "query": "string"
            }

        TODO:
            - Validate input schema
            - Integrate with Video-RAG pipeline
            - Return structured results with timestamps

        Returns:
            JsonResponse: Query result or placeholder response.
        """
        try:
            data: Dict[str, Any] = json.loads(request.body)
            video_id: str = data.get('video_id', '')
            query_text: str = data.get('query', '')
        except (json.JSONDecodeError, KeyError):
            return JsonResponse(
                {"error": "Invalid JSON payload"},
                status=400
            )

        # TODO: Implement query processing logic
        return JsonResponse({
            "video_id": video_id,
            "query": query_text,
            "answer": "Placeholder answer from Video-RAG (not implemented)",
            "timestamps": [0.0, 10.5, 25.3]  # Example format
        })


# ----------------------------
# URL Routing
# ----------------------------

urlpatterns = [
    path('health/', HealthCheckView.as_view(), name='health_check'),
    path('api/upload/', VideoUploadView.as_view(), name='video_upload'),
    path('api/query/', VideoQueryView.as_view(), name='video_query'),
]


# ----------------------------
# Server Entry Point
# ----------------------------

def main() -> None:
    """
    Main entry point to run the Django development server.

    This function configures Django settings and delegates command execution
    to Django's management utility. It supports standard Django management
    commands (e.g., runserver, migrate).

    Usage:
        python server.py runserver
    """
    configure_django_settings()
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()