# api/management/commands/update_thumbs.py
from django.core.management.base import BaseCommand
from api.models import  VideoTranscript, TranscriptSentence
from django.core.files import File
from typing import List, Dict, Any

class Command(BaseCommand):
    help = 'Update transcript for a video'

    def add_arguments(self, parser):
        parser.add_argument('video_id', type=str, help='UUID of the video')
        # For demo, we hardcode data — in real use, read from JSON/file

    def save_asr_result(self, video_id: str, data: Dict[str, Any]) -> None:
        """
        Save the ASR result data into the Django database.

        Args:
            data (Dict[str, Any]): ASR result as a dictionary.

        Raises:
            ValueError: If required fields are missing.
        """

        # Create or update the VideoTranscript
        video_transcript, created = VideoTranscript.objects.update_or_create(
            video_id=video_id,
            defaults={
                "file_url": data.get("file_url", ""),
                "format": data.get("audio_info", {}).get("format", ""),
                "sample_rate": data.get("audio_info", {}).get("sample_rate", 0),
            }
        )

        # Process each transcript entry
        for transcript in data.get("transcripts", []):
            channel_id = transcript.get("channel_id", 0)

            # Delete existing sentences for this channel
            TranscriptSentence.objects.filter(video_transcript=video_transcript, channel_id=channel_id).delete()

            # Add new sentences
            for sentence in transcript.get("sentences", []):
                TranscriptSentence.objects.create(
                    video_transcript=video_transcript,
                    channel_id=channel_id,
                    sentence_id=sentence.get("sentence_id", 0),
                    begin_time=sentence.get("begin_time", 0),
                    end_time=sentence.get("end_time", 0),
                    language=sentence.get("language", ""),
                    emotion=sentence.get("emotion", ""),
                    text=sentence.get("text", "")
                )


    def handle(self, *args, **options):
        video_id = options['video_id']
    
        try:
            import json
            with open("/home/xuranus/workspace/PolyU-Video-Agent/target/cde4c5c2-5ef0-4d03-93bf-83f5b255c8a7.json") as f:
                data = json.load(f)
            self.save_asr_result(video_id, data)
            
            self.stdout.write(
                self.style.SUCCESS(f'Successfully updated transcript')
            )
        except Exception as e:
            self.stderr.write(self.style.ERROR(f'Error: {e}'))