// === React Frontend (YoloStream.jsx) ===
import React, { useEffect, useRef } from 'react';
import type { AccidentData } from './AccidentPanel';
type YoloStreamProps = {
    setData: (data: AccidentData) => void
}

const YoloStream = ({ setData }: YoloStreamProps) => {
    const imgRef = useRef<HTMLImageElement>(null);

    useEffect(() => {
        const socket = new WebSocket('ws://localhost:8000/ws');


        socket.onopen = () =>{
            console.log("Socket Connection Oppened")
        }

        socket.onmessage = (event) => {
            const data = JSON.parse(event.data);
            setData(data)
            if (imgRef.current) {
                if (imgRef.current) {
                    imgRef.current.src = `data:image/jpeg;base64,${data.frame}`;
                }


            }
            console.log("Data recieved on local Instance", data)
        };

        socket.onerror = (err) => {
            console.error('WebSocket error:', err);
        };

        return () => socket.close();
    }, []);

    return (
        <div className="w-full flex justify-center px-4 py-6 bg-gray-900 text-white">
            <div className="w-full max-w-7xl p-4 border border-gray-700 rounded-2xl shadow-2xl bg-gray-800">
                <h2 className="text-3xl font-bold mb-4 text-center">🔴 Live YOLO Stream</h2>

                <div className="relative w-full aspect-video overflow-hidden rounded-xl border border-gray-600 bg-gray-700">
                    <img
                        ref={imgRef}
                        alt="Live YOLO Feed"
                        src="https://placehold.co/1280x720?text=YOLO+server+instance+offline"
                        className="w-full h-full object-cover transition-all duration-300"
                        onError={(e) => {
                            (e.target as HTMLImageElement).src = "https://placehold.co/1280x720?text=YOLO+server+instance+offline";
                        }}
                    />
                    {/* Optional overlay text for status (if needed in the future) */}
                    {/* 
      <div className="absolute inset-0 bg-black bg-opacity-60 flex items-center justify-center">
        <p className="text-white text-xl font-semibold">YOLO server instance offline</p>
      </div> 
      */}
                </div>
            </div>
        </div>

    );
};

export default YoloStream;
