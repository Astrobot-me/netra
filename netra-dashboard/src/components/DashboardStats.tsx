const DashboardStats = () => (
  <div className="mt-8 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
    {/* Traffic Density */}
    <div className="bg-gray-800 rounded-lg p-4 shadow-lg">
      <h3 className="text-lg font-medium mb-2 flex items-center">
        <i className="fas fa-tachometer-alt mr-2 text-blue-400"></i>
        Traffic Density
      </h3>
      <div className="flex justify-between items-center">
        <span className="text-gray-400">Current Average</span>
        <span className="text-xl font-mono">68%</span>
      </div>
      <div className="w-full bg-gray-700 rounded-full h-2.5 mt-2">
        <div className="bg-blue-500 h-2.5 rounded-full" style={{ width: '68%' }}></div>
      </div>
    </div>

    {/* System Status */}
    <div className="bg-gray-800 rounded-lg p-4 shadow-lg">
      <h3 className="text-lg font-medium mb-2 flex items-center">
        <i className="fas fa-clock mr-2 text-green-400"></i>
        System Status
      </h3>
      <div className="flex items-center">
        <div className="w-3 h-3 bg-green-500 rounded-full mr-2"></div>
        <span>All systems operational</span>
      </div>
      <p className="text-gray-400 text-sm mt-2">Last updated: 2 minutes ago</p>
    </div>

    {/* Alerts */}
    <div className="bg-gray-800 rounded-lg p-4 shadow-lg">
      <h3 className="text-lg font-medium mb-2 flex items-center">
        <i className="fas fa-bell mr-2 text-yellow-400"></i>
        Alerts
      </h3>
      <p className="text-sm text-gray-400">No active alerts</p>
      <button className="mt-3 text-sm text-blue-400 hover:text-blue-300 cursor-pointer !rounded-button whitespace-nowrap">
        View alert history
      </button>
    </div>

    {/* Quick Actions */}
    <div className="bg-gray-800 rounded-lg p-4 shadow-lg">
      <h3 className="text-lg font-medium mb-2 flex items-center">
        <i className="fas fa-cog mr-2 text-purple-400"></i>
        Quick Actions
      </h3>
      <div className="grid grid-cols-2 gap-2">
        <button className="bg-blue-600 hover:bg-blue-700 text-white py-2 px-3 rounded text-sm cursor-pointer !rounded-button whitespace-nowrap">
          <i className="fas fa-sync-alt mr-1"></i> Refresh
        </button>
        <button className="bg-gray-700 hover:bg-gray-600 text-white py-2 px-3 rounded text-sm cursor-pointer !rounded-button whitespace-nowrap">
          <i className="fas fa-expand-alt mr-1"></i> Fullscreen
        </button>
      </div>
    </div>
  </div>
);
export default DashboardStats;
