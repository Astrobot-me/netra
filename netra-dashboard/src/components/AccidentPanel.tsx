const AccidentPanel: React.FC<{ accidents: string[] }> = ({ accidents }) => (
  <div className="bg-gray-800 rounded-lg overflow-hidden shadow-lg md:col-span-2">
    <div className="p-3 border-b border-gray-700">
      <h2 className="text-xl font-semibold">Accident</h2>
    </div>
    <div className="p-4 min-h-[200px]">
      {accidents.length > 0 ? (
        <ul className="space-y-2">
          {accidents.map((accident, index) => (
            <li key={index} className="p-3 bg-red-900/30 border border-red-700 rounded text-red-100">
              <i className="fas fa-exclamation-triangle mr-2 text-yellow-500"></i>
              {accident}
            </li>
          ))}
        </ul>
      ) : (
        <div className="h-full flex items-center justify-center text-gray-500">
          <p>No accidents detected</p>
        </div>
      )}
    </div>
  </div>
);
export default AccidentPanel;
