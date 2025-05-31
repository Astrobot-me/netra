const Footer = () => (
  <footer className="mt-8 pt-6 border-t border-gray-800 text-gray-500 text-sm">
    <div className="flex flex-col md:flex-row justify-between items-center">
      <p>© 2025 Traffic Monitoring System. All rights reserved.</p>
      <div className="mt-4 md:mt-0">
        <button className="text-gray-400 hover:text-white mr-4 cursor-pointer !rounded-button whitespace-nowrap">Help</button>
        <button className="text-gray-400 hover:text-white cursor-pointer !rounded-button whitespace-nowrap">Settings</button>
      </div>
    </div>
  </footer>
);
export default Footer;
