import React, { useState } from 'react';

const AttackSimulator: React.FC = () => {
  const [lastAction, setLastAction] = useState('No simulated attack yet');

  return (
    <div className="bg-gray-800 rounded-xl p-6 shadow w-full flex flex-col items-center">
      <h3 className="font-bold text-lg text-gray-100 mb-4">Attack Simulator</h3>
      <button
        className="px-5 py-2 rounded bg-red-600 text-white hover:bg-red-700 font-semibold mb-3"
        onClick={() => setLastAction('Simulated cyberattack at ' + new Date().toLocaleTimeString())}
      >
        Simulate Attack
      </button>
      <div className="text-xs text-gray-300 mt-1">{lastAction}</div>
    </div>
  );
};

export default AttackSimulator;
