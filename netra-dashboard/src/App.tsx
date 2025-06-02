import React, { useState, useEffect } from 'react';
import Header from './components/Header';
import LaneCard from './components/LaneCard';
import AccidentPanel, { LOCAL_STORAGE_KEY, type AccidentData } from './components/AccidentPanel';
import DashboardStats from './components/DashboardStats';
import Footer from './components/Footer';
import { doc, getDoc } from 'firebase/firestore'
import { db } from './firestore/firebaseClient';
import Toggle from './components/ui/ToggleButton';
import { fetchLatestSession } from './firestore/firebaseClient';
import YoloStream from './components/YoloSocket';
import { calculateVehicleDensityFromLanes } from './util/calculateDensity';
import { toast } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';


type Lane = {
  id: number;
  lane_dir: string;
  signal: string;
  timing: number;
  src: string;
};

const App: React.FC = () => {


  const [toggle, setToggle] = useState<boolean>(false);
  const [lanes, setLanes] = useState<Lane[]>([
    { id: 1, lane_dir: "north", signal: 'green', timing: 45, src: "https://tjdvxjulzc.ufs.sh/f/idH6nnzGsO3LzW8QFi1C06XZbmNkMA5PUr8DVvFlSGTo3KYd" },
    { id: 2, lane_dir: "south", signal: 'green', timing: 30, src: "https://tjdvxjulzc.ufs.sh/f/idH6nnzGsO3L8AldMjkv0F61KT45pzkiVrEwbPUQtJWN3Lx2" },
    { id: 3, lane_dir: "east", signal: 'green', timing: 60, src: "https://tjdvxjulzc.ufs.sh/f/idH6nnzGsO3LKhp8SYdh3nDfM0xbV2mYOpsqS5RtL67HXjZc" },
    { id: 4, lane_dir: "west", signal: 'green', timing: 25, src: "https://tjdvxjulzc.ufs.sh/f/idH6nnzGsO3L0zeFEkWTRDjK7uwly6cdiSUPBWqIr21nCLAh" },
  ]);


  const [accidents, setAccidents] = useState<AccidentData[]>([]);
  const [stateData, setStateData] = useState<{ id: string;[key: string]: any }[]>([]);
  const [densityStats, setDensityStats] = useState({ totalVehicles: 24, densityPercent: 56 });

  type Session = { id: string } | null;
  const [latestSession, setLatestSession] = useState<Session>(null);


  const handleReset = () => {
   
    localStorage.setItem(LOCAL_STORAGE_KEY, JSON.stringify([])); // This sets the value to an empty array as a string
    
    // If you want to completely remove the item instead of setting to "null":
    // localStorage.removeItem(itemId);
    toast.warn(`LocalStorage item "${LOCAL_STORAGE_KEY}" has been reset.`);
    setAccidents([]); // Clear the accidents state
    console.log(`LocalStorage item "${LOCAL_STORAGE_KEY}" has been reset.`);
  };

  useEffect(() => {
    let intervalIds: NodeJS.Timeout[] = [];

    const runOfflineMode = () => {
      intervalIds = lanes.map((lane) =>
        setInterval(() => {
          setLanes(prev =>
            prev.map(l =>
              l.id === lane.id
                ? {
                  ...l,
                  timing: l.timing > 0 ? l.timing - 1 : 60,
                  signal: l.timing === 1 ? (l.signal === 'green' ? 'red' : 'green') : l.signal,
                }
                : l
            )
          );
        }, 1000)
      );
    };

    const runRealtimeMode = async () => {
      const session = await fetchLatestSession();
      console.log("Fetched Session:", session?.id);
      setLatestSession(session || null);
    };

    if (toggle) {
      runRealtimeMode();
    } else {
      runOfflineMode();
      setDensityStats({ totalVehicles: 45, densityPercent: 56 })
    }

    return () => {
      intervalIds.forEach(clearInterval);
      setLatestSession(null); // cleanup session when exiting realtime
    };
  }, [toggle]);



  useEffect(() => {
    if (!latestSession || !latestSession.id) return;

    const intervalId = setInterval(async () => {
      try {
        const sessionDocRef = doc(db, "traffic_sessions", latestSession.id);
        const sessionDocSnap = await getDoc(sessionDocRef);

        if (sessionDocSnap.exists()) {
          const sessionData = sessionDocSnap.data();
          console.log("Live Lane Data:", sessionData);
          setStateData([{ id: latestSession.id, ...sessionData }]);
          const laneData = sessionData.timesteps[sessionData.timesteps.length - 1].lanes;

          // calculating vehicle density
          if (laneData) {
            const stats = calculateVehicleDensityFromLanes(laneData);
            setDensityStats(stats);
          }


          setLanes(prevData => {

            const updated = prevData.map(item => {
              if (item.lane_dir == "north") {
                return {
                  ...item,
                  signal: String(laneData.north.state).toLowerCase(),
                  timing: Math.round(laneData.north.time_remaining) // Convert to seconds
                }

              } else if (item.lane_dir == "south") {
                return {
                  ...item,
                  signal: String(laneData.south.state).toLowerCase(),
                  timing: Math.round(laneData.south.time_remaining) // Convert to seconds
                }
              } else if (item.lane_dir == "east") {
                return {
                  ...item,
                  signal: String(laneData.east.state).toLowerCase(),
                  timing: Math.round(laneData.east.time_remaining)
                }
              } else if (item.lane_dir == "west") {
                return {
                  ...item,
                  signal: String(laneData.west.state).toLowerCase(),
                  timing: Math.round(laneData.west.time_remaining)
                }
              } else {
                return item
              }
            })


            return updated
          })


        }
      } catch (error) {
        console.error("Error fetching session document:", error);
      }
    }, 1000);

    return () => clearInterval(intervalId);
  }, [latestSession]);


  return (
    <div className="min-h-screen bg-gray-900 text-white p-4 md:p-6 lg:p-8">
      <Header />
      <div className='flex gap-4'>
        <Toggle label='Database Mode' onToggle={setToggle} isOn={toggle} />

        <div className='flex gap-3'>
          <button className="bg-blue-600 hover:bg-blue-700 text-white py-2 px-3 rounded text-sm cursor-pointer !rounded-button whitespace-nowrap">
            <i className="fas fa-sync-alt mr-1"></i> Refresh
          </button>
          <button className="bg-gray-700 hover:bg-gray-600 text-white py-2 px-3 rounded text-sm cursor-pointer !rounded-button whitespace-nowrap">
            <i className="fas fa-expand-alt mr-1"></i> Fullscreen
          </button>
        </div>

      </div>
      <DashboardStats densityStat={{...densityStats , percent: densityStats.densityPercent, vehicle_count : densityStats.totalVehicles}} connectionStatus={toggle} mapdata={{lat: accidents[accidents.length - 1]?.latitude , long: accidents[accidents.length - 1]?.longitude}} />

      
      <div className="flex flex-col lg:flex-row mt-10 gap-6">
        {/* Lane Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 flex-grow px-4 py-6 bg-gray-900">
          {lanes.map((lane) => (
            <LaneCard key={lane.id} lane={lane} />
          ))}

          {/* YOLO stream spans both columns */}
          <div className="md:col-span-2">
            <YoloStream setData={(data: AccidentData) => setAccidents(prev => [...prev, data])} />
          </div>
        </div>



        {/* Accident Panel on the right */}
        <div className="w-full lg:w-3/5 h-full lg:h-auto">
          <div className="sticky top-0">
            <AccidentPanel liveData={accidents[accidents.length - 1]} />
          </div>
        </div>



      </div>




      <Footer handleReset={handleReset} />
    </div>
  );
};

export default App;
