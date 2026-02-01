# api/management/commands/update_thumbs.py
from django.core.management.base import BaseCommand
from api.utils import generate_thumbnails_for_video
from api.models import Video, Thumbnail
import uuid
import os
from django.core.files import File

class Command(BaseCommand):
    help = 'Update thumbnails for a video'

    def add_arguments(self, parser):
        parser.add_argument('video_id', type=str, help='UUID of the video')
        # For demo, we hardcode data — in real use, read from JSON/file

        
    def update_thumbnails_for_video(self, video_id: str, thumbnail_data: list[dict]):
        """
        Replace all thumbnails for a video with new ones from provided data.
        
        Args:
            video_id (str): UUID string of the video
            thumbnail_data (list[dict]): List like:
                [
                    {
                        'image_id': '309ef35e-...',
                        'time_second': 446.4,
                        'image': './media/thumbnails/309ef35e-....jpg'
                    },
                    ...
                ]
        """
        # Validate and get video
        try:
            video_uuid = uuid.UUID(video_id)
            video = Video.objects.get(id=video_uuid)
        except (ValueError, Video.DoesNotExist) as e:
            raise ValueError(f"Invalid or missing video ID: {video_id}") from e

        # Delete existing thumbnails (cleanup old files too)
        old_thumbnails = Thumbnail.objects.filter(video=video)
        for thumb in old_thumbnails:
            if thumb.image and os.path.isfile(thumb.image.path):
                os.remove(thumb.image.path)  # Optional: delete old image file
        old_thumbnails.delete()

        # Create new thumbnails
        created_count = 0
        for item in thumbnail_data:
            try:
                # Validate fields
                img_id = uuid.UUID(item['image_id'])
                time_sec = float(item['time_second'])
                img_path = item['image']

                if not os.path.isfile(img_path):
                    print(f"⚠️ Image not found: {img_path}")
                    continue

                # Create new Thumbnail instance
                thumb = Thumbnail(
                    id=img_id,
                    video=video,
                    time_second=time_sec
                )

                # Open and assign file to ImageField
                with open(img_path, 'rb') as f:
                    # Save under correct upload path (e.g., 'thumbnails/filename.jpg')
                    filename = os.path.basename(img_path)
                    thumb.image.save(filename, File(f), save=True)

                created_count += 1

            except (KeyError, ValueError, TypeError, OSError) as e:
                print(f"❌ Skipping invalid thumbnail entry {item}: {e}")
                continue

        return created_count


    def handle(self, *args, **options):
        video_id = options['video_id']
    
        try:
            thumbnails = generate_thumbnails_for_video(
                video_file="/home/xuranus/workspace/PolyU-Video-Agent/server/app/media/videos/zoom.mp4",
                time_seconds=[93.12, 95.04, 264.96, 267.36, 306.24, 308.64, 439.68, 442.08, 446.4, 591.84],
                width=200,
                output_dir="./media/thumbnails"
            )

            for thumb in thumbnails:
                print(thumb)

            count = self.update_thumbnails_for_video(video_id, thumbnails)
            
            self.stdout.write(
                self.style.SUCCESS(f'Successfully updated {count} thumbnails')
            )
        except Exception as e:
            self.stderr.write(self.style.ERROR(f'Error: {e}'))