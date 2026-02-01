
import { useState, useRef, useEffect } from 'react';
import { Spin, message } from 'antd';
import { LoadingOutlined } from '@ant-design/icons';

export interface Thumbnail {
  time_second: number;
  image_url: string;
}

export interface VideoData {
  id: number;
  title: string;
  video_url: string;
  thumbnails: Thumbnail[];
}

interface VideoPlayProps {
  videoId: string;
}

const PlayGround: React.FC<VideoPlayProps> = ({ videoId }) => {
  const [videoData, setVideoData] = useState<VideoData | null>(null);
  const [loading, setLoading] = useState(true);
  const videoRef = useRef<HTMLVideoElement>(null);

  // Fetch video + thumbnails
  useEffect(() => {
    const fetchData = async () => {
      try {
        const [videoRes, thumbsRes] = await Promise.all([
          fetch(`/api/videos/${videoId}/`),
          fetch(`/api/videos/${videoId}/thumbnails/`)
        ]);
        const video = await videoRes.json();
        const thumbnails = await thumbsRes.json();
        setVideoData({ ...video, thumbnails });
      } catch (err) {
        message.error('Failed to load video resources');
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [videoId]);

  const handleSeek = (time: number) => {
    if (videoRef.current && !isNaN(videoRef.current.duration)) {
      videoRef.current.currentTime = time;
      if (videoRef.current.paused) videoRef.current.play(); // Optional: auto-play on seek
    }
  };

  const formatTime = (seconds: number) => 
    new Date(seconds * 1000).toISOString().slice(14, 19); // "01:23"

  if (loading) return (
    <div className="flex justify-center py-12">
      <Spin indicator={<LoadingOutlined style={{ fontSize: 48 }} spin />} />
    </div>
  );

  if (!videoData) return <div className="text-center py-8 text-red-500">Video not found</div>;

  return (
    <div className="max-w-5xl mx-auto px-4 py-6">
      {/* Video Player */}
      <div className="aspect-video bg-gray-900 rounded-lg overflow-hidden mb-6">
        <video
          ref={videoRef}
          src={videoData.video_url}
          controls
          className="w-full h-full object-contain"
          preload="metadata"
        >
          Your browser does not support the video tag.
        </video>
      </div>

      {/* Thumbnails */}
      <div 
        role="region" 
        aria-label="Video chapter thumbnails"
        className="flex flex-nowrap gap-3 overflow-x-auto pb-3 px-1 scrollbar-thin scrollbar-thumb-gray-400 scrollbar-track-gray-100"
      >
        {videoData.thumbnails.map((thumb, idx) => (
          <button
            key={idx}
            onClick={() => handleSeek(thumb.time_second)}
            className="flex-shrink-0 group focus:outline-none focus:ring-2 focus:ring-blue-500 rounded"
            aria-label={`Jump to ${formatTime(thumb.time_second)}`}
            title={`Seek to ${formatTime(thumb.time_second)}`}
          >
            <div className="relative w-24 md:w-28">
              <img
                src={thumb.image_url}
                alt={`Preview at ${formatTime(thumb.time_second)}`}
                className="w-full h-16 object-cover rounded transition-transform group-hover:scale-105"
                loading={idx < 3 ? "eager" : "lazy"} // Prioritize first thumbnails
              />
              <span className="absolute bottom-1 left-1/2 transform -translate-x-1/2 
                             text-[10px] font-mono bg-black/70 text-white px-1 py-0.5 rounded">
                {formatTime(thumb.time_second)}
              </span>
            </div>
          </button>
        ))}
      </div>
    </div>);
}

export default PlayGround;