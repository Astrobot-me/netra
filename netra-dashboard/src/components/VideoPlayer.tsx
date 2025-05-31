import React, { useEffect, useRef } from 'react';

interface VideoPlayerProps {
  shouldPlay: boolean;
  src?: string;
}

const VideoPlayer: React.FC<VideoPlayerProps> = ({ shouldPlay, src }) => {
  const videoRef = useRef<HTMLVideoElement | null>(null);

  useEffect(() => {
    if (!videoRef.current) return;
    
    if (shouldPlay) {
      videoRef.current.play().catch(err => console.error('Play error:', err));
    } else {
      videoRef.current.pause();
    }
  }, [shouldPlay]);

  return (
    <video
      ref={videoRef}
      src={src || 'https://www.w3schools.com/html/mov_bbb.mp4'} // fallback video
      className="w-full h-auto rounded"
      loop
      muted
    />
  );
};

export default VideoPlayer;
