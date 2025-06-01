import React, { useState, useEffect } from 'react';
import Header from './components/Header';
import LaneCard from './components/LaneCard';
import AccidentPanel, { type AccidentData } from './components/AccidentPanel';
import DashboardStats from './components/DashboardStats';
import Footer from './components/Footer';
// import { getDocs, collection } from 'firebase/firestore'
// import { db } from './firestore/firebaseClient';
import Toggle from './components/ui/ToggleButton';
import { fetchLatestSession } from './firestore/firebaseClient';
import YoloStream from './components/YoloSocket';

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
  type Session = { id: string } | null;
  const [latestSession, setLatestSession] = useState<Session>(null);


  useEffect(() => {
    let intervalIds: NodeJS.Timeout[] = [];

    const fetchLanes = async () => {
      try {
        // const snapshot = await getDocs(collection(db, 'traffic_sessions'));
        // const fetched = snapshot.docs.map(doc => ({ id: Number(doc.id), ...doc.data() }));
        // console.log(fetched);

        // setLanes(prevLanes =>
        //   prevLanes.map(lane => {
        //     const updated = fetched.find(f => f.id === lane.id);
        //     return updated
        //       ? {
        //         ...lane,
        //         signal: updated.signal ?? lane.signal,
        //         timing: updated.timing ?? lane.timing,
        //       }
        //       : lane;
        //   })
        // );
      } catch (error) {
        console.error("Error fetching lanes from Firestore:", error);
      }
    };

    const runRealtimeMode = async () => {
      const session = await fetchLatestSession();
      console.log("current Session", session)
      setLatestSession(session || null);

      await fetchLanes(); // initial fetch
      const firestoreInterval = setInterval(fetchLanes, 3000);
      intervalIds.push(firestoreInterval);
    };

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

    if (toggle) {
      runRealtimeMode();
    } else {
      // console.log("Running on Offline Mode");
      runOfflineMode();
    }

    return () => intervalIds.forEach(clearInterval); // Cleanup all intervals
  }, [toggle, lanes]);



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
      <DashboardStats percent={39} connectionStatus={toggle} />
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


      <Footer />
    </div>
  );
};

export default App;
