import React from 'react';
import { Sun } from 'lucide-react'; // Example icons

const Header: React.FC = () => {
  // Basic Header structure - add functionality later (e.g., theme toggle)
  return (
    <header className="bg-white dark:bg-gray-800 shadow-md p-4 flex justify-between items-center">
      <h1 className="text-xl font-semibold text-gray-800 dark:text-gray-100">
        Smart City Agent Dashboard
      </h1>
      <div>
        {/* Placeholder for theme toggle or other controls */}
        <button className="p-2 rounded-md text-gray-600 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700">
          <Sun className="h-5 w-5" /> {/* Or Moon based on theme */}
        </button>
      </div>
    </header>
  );
};

export default Header;
