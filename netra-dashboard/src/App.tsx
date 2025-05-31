import React, { useState, useEffect } from 'react';
import Header from './components/Header';
import LaneCard from './components/LaneCard';
import AccidentPanel from './components/AccidentPanel';
import DashboardStats from './components/DashboardStats';
import Footer from './components/Footer';

const App: React.FC = () => {
  const [lanes, setLanes] = useState([
    { id: 1, signal: 'green', timing: 45, src: "https://tjdvxjulzc.ufs.sh/f/idH6nnzGsO3LzW8QFi1C06XZbmNkMA5PUr8DVvFlSGTo3KYd" },
    { id: 2, signal: 'green', timing: 30 ,src:"https://tjdvxjulzc.ufs.sh/f/idH6nnzGsO3L8AldMjkv0F61KT45pzkiVrEwbPUQtJWN3Lx2"},
    { id: 3, signal: 'green', timing: 60 , src:"https://tjdvxjulzc.ufs.sh/f/idH6nnzGsO3LKhp8SYdh3nDfM0xbV2mYOpsqS5RtL67HXjZc"},
    { id: 4, signal: 'green', timing: 25 , src:"https://tjdvxjulzc.ufs.sh/f/idH6nnzGsO3L0zeFEkWTRDjK7uwly6cdiSUPBWqIr21nCLAh"},
  ]);
  const [accidents, setAccidents] = useState<string[]>([]);

  useEffect(() => {
    const timers = lanes.map((lane) =>
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
    return () => timers.forEach(clearInterval);
  }, []);

  useEffect(() => {
    const interval = setInterval(() => {
      const randomLane = Math.floor(Math.random() * 4) + 1;
      const randomChance = Math.random();
      if (randomChance > 0.8) {
        const type = randomChance > 0.95 ? 'Major collision' : 'Minor incident';
        const time = new Date().toLocaleTimeString();
        setAccidents([`${time}: ${type} in Lane ${randomLane}`]);
        setTimeout(() => setAccidents([]), 10000);
      }
    }, 15000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="min-h-screen bg-gray-900 text-white p-4 md:p-6 lg:p-8">
      <Header />
      <DashboardStats />
      <div className="flex flex-col lg:flex-row mt-10 gap-6">
        {/* Lane Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 flex-grow">
          {lanes.map((lane) => (
            <LaneCard key={lane.id} lane={lane} />
          ))}
        </div>

        {/* Accident Panel on the right */}
        <div className="w-full lg:w-2/5 h-full lg:h-auto">
          <div className="sticky top-0">
            <AccidentPanel accidents={accidents} />
          </div>
        </div>

      </div>


      <Footer />
    </div>
  );
};

export default App;
