# api/urls.py
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    path('videos/', views.VideoListView.as_view(), name='video-list'),
    path('videos/upload/', views.VideoUploadView.as_view(), name='video-upload'),
    path('videos/<uuid:pk>/', views.VideoDetailView.as_view(), name='video-detail'),
    path('videos/<uuid:video_id>/thumbnails/', views.ThumbnailListView.as_view(), name='thumbnail-list'),
    path('videos/<uuid:video_id>/transcript/', views.TranscriptDetailView.as_view(), name='transcript-detail'),
]



# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)