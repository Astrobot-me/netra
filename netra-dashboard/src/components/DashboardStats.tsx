import LiveGraph from "./LiveGraph";
import MiniMap from "./MiniMap";

interface DashboardProps {
  densityStat: {
    percent: number
    vehicle_count:number
  }
  connectionStatus: boolean
  mapdata : {
    lat : number;
    long: number; 
  }
}

const DashboardStats = ({ densityStat, connectionStatus,mapdata }: DashboardProps) => (

  

  <div className="mt-8 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
    {/* Traffic Density */}
    <div className="bg-gray-800 rounded-lg p-4 shadow-lg">
      <h3 className="text-lg font-medium mb-2 flex items-center">
        <i className="fas fa-tachometer-alt mr-2 text-blue-400"></i>
        Traffic Details
      </h3>
      <div className="flex justify-between items-center">
        <span className="text-gray-400">Current Average</span>
        <span className="text-xl font-mono">{densityStat.percent}%</span>
      </div>
      <div className="w-full bg-gray-700 rounded-full h-2.5 mt-2">
        <div className="bg-blue-500 h-2.5 rounded-full" style={{ width: `${densityStat.percent}%` }}></div>
      </div>
      <div className="flex justify-between items-center mt-5">
        <span className="text-gray-400 "> Total Vehicle Count</span>
        <span className="text-xl font-mono ">{ densityStat.vehicle_count } </span>
      </div>
      <div className="w-full bg-gray-700 rounded-full h-2.5 mt-2">
        <div className="bg-blue-500 h-2.5 rounded-full" style={{ width: `${densityStat.vehicle_count % 100}%` }}></div>
      </div>
      <p className="text-gray-400 text-sm mt-7">Last updated: 2 minutes ago</p>
    </div>

    <div className="bg-gray-800 rounded-lg p-4 shadow-lg">
      <h3 className="text-lg font-medium mb-2 flex items-center">
        <i className="fas fa-tachometer-alt mr-2 text-blue-400"></i>
        Traffic Density
      </h3>
      <LiveGraph percent={densityStat.percent} />
      <p className="text-gray-400 text-sm mt-2">Updating live every second</p>
    </div>

    {/* System Status */}
    <div className="bg-gray-800 rounded-lg p-4 shadow-lg">
      <h3 className="text-lg font-medium mb-2 flex items-center">
        <i className="fas fa-clock mr-2 text-green-400"></i>
        System Status
      </h3>
      <div className="flex items-center uppercase font-medium">
        <div className="w-3 h-3 bg-green-500 rounded-full mr-2"></div>
        <span>All systems operational</span>
      </div>
      <div className="flex items-center text-xl uppercase font-medium mt-5">
        <div className="w-3 h-3 bg-green-500 rounded-full mr-2" style={{ alignSelf: "center" }}></div>
        {connectionStatus ? <span>Connected to Central Cloud</span> : <span>Running on autonomous mode</span>}
      </div>
      <p className="text-gray-400 text-sm mt-8">Last updated: 2 minutes ago</p>
    </div>



    {/* Quick Actions */}
    <MiniMap lat={mapdata.lat ||  28.6139} lng={ mapdata.long || 77.2090} toggle={connectionStatus}/>

  </div>
);
export default DashboardStats;
