# api/serializers.py
from rest_framework import serializers
from .models import Video, Thumbnail, VideoTranscript, TranscriptSentence

class ThumbnailSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Thumbnail
        fields = ['id', 'time_second', 'image_url']

    def get_image_url(self, obj):
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None


class VideoSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    thumbnails = ThumbnailSerializer(many=True, read_only=True)
    video_url = serializers.SerializerMethodField()

    class Meta:
        model = Video
        fields = ['id', 'title', 'video_url', 'duration', 'thumbnails']

    def get_video_url(self, obj):
        if obj.file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.file.url)
            return obj.file.url
        return None


class VideoUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Video
        fields = ['title', 'file']  # Only accept these on upload
    
    def to_representation(self, instance):
        # Use the full serializer for output
        return VideoSerializer(instance, context=self.context).data
    

class TranscriptSentenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = TranscriptSentence
        fields = ['channel_id', 'sentence_id', 'begin_time', 'end_time', 'language', 'emotion', 'text']

class VideoTranscriptSerializer(serializers.ModelSerializer):
    sentences = TranscriptSentenceSerializer(many=True, read_only=True)

    class Meta:
        model = VideoTranscript
        fields = ['video_id', 'file_url', 'format', 'sample_rate', 'sentences']
