import React from "react";

const zones = [
  { id: "A", label: "Zone A", status: "Powered", color: "bg-green-500" },
  { id: "B", label: "Zone B", status: "Blackout", color: "bg-red-500" },
  { id: "C", label: "Zone C", status: "Restoring", color: "bg-yellow-400" },
];

const ZonePowerPanel: React.FC = () => (
  <div className="bg-gray-800 rounded-xl p-6 shadow w-full">
    <h3 className="font-bold text-lg text-gray-100 mb-4">Zone Power Status</h3>
    <ul className="space-y-3">
      {zones.map(z => (
        <li key={z.id} className="flex items-center justify-between">
          <span className="text-gray-200">{z.label}</span>
          <span className={`px-3 py-1 text-xs font-semibold rounded ${z.color} text-gray-900`}>{z.status}</span>
        </li>
      ))}
    </ul>
  </div>
);

export default ZonePowerPanel;
