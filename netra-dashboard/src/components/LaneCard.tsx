import VideoPlayer from "./VideoPlayer";

interface Lane {
  id: number;
  signal: string;
  timing: number;
  src:string;
}

const LaneCard: React.FC<{ lane: Lane }> = ({ lane }) => (
  <div className="bg-gray-800 rounded-lg overflow-hidden shadow-lg">
    <div className="p-3 border-b border-gray-700 flex justify-between items-center">
      <span className="text-xl font-semibold">Lane {lane.id}</span>
      <div className="flex items-center gap-3">
        <div className={`font-bold uppercase ${lane.signal === 'green' ? 'text-green-500' : 'text-red-500'}`}> {lane.signal === 'green' ? 'Green Signal' : 'Red Signal'}</div>
        <div className={`w-6 h-6 rounded-full ${lane.signal === 'green' ? 'bg-green-500' : 'bg-red-500'} flex items-center justify-center`}>
           
          {lane.signal === 'green' && (
            <div className="w-4 h-4 rounded-full bg-green-400 animate-pulse"></div>
          )}
        </div>
        <span className="text-blue-400 text-xl font-mono">{lane.timing}s</span>
      </div>
    </div>
    <div className="relative aspect-video bg-gray-900 flex items-center justify-center">
      {/* <div className="absolute inset-0 flex items-center justify-center">
        <div className="w-full h-0.5 bg-gray-700 absolute transform rotate-45"></div>
        <div className="w-full h-0.5 bg-gray-700 absolute transform -rotate-45"></div>
      </div>
      <span className="text-orange-500 z-10 font-medium">video</span> */}
      <VideoPlayer shouldPlay={true} src={lane.src}/> 

    </div>
  </div>
);
export default LaneCard;
