const Header = () => (
  <header className="mb-6">
    <h1 className="text-2xl md:text-3xl font-bold mb-2">Traffic Monitoring Dashboard</h1>
    <p className="text-gray-400">
      Live status dashboard - {new Date().toLocaleDateString('en-US', {
        weekday: 'long', year: 'numeric', month: 'long', day: 'numeric'
      })}
    </p>
  </header>
);
export default Header;
