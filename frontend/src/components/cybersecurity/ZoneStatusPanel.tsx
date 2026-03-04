import React from "react";

const ZoneStatusPanel: React.FC = () => (
  <div className="bg-gray-800 rounded-xl p-6 shadow w-full">
    <h3 className="font-bold text-lg text-gray-100 mb-2">Zone Status</h3>
    <ul className="space-y-2">
      <li className="flex items-center justify-between">
        <span className="text-gray-200">Zone A</span>
        <span className="bg-green-500 text-white px-2 py-1 rounded text-xs font-bold">Safe</span>
      </li>
      <li className="flex items-center justify-between">
        <span className="text-gray-200">Zone B</span>
        <span className="bg-yellow-400 text-gray-900 px-2 py-1 rounded text-xs font-bold">At Risk</span>
      </li>
      <li className="flex items-center justify-between">
        <span className="text-gray-200">Zone C</span>
        <span className="bg-red-600 text-white px-2 py-1 rounded text-xs font-bold">Compromised</span>
      </li>
    </ul>
  </div>
);

export default ZoneStatusPanel;
