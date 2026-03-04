import React from "react";

const incidents = [
  { id: 1, type: 'Electrical Fault', description: 'Transformer trip in Zone B', time: '07:45 AM' },
  { id: 2, type: 'Manual Override', description: 'Restored power in Zone C', time: '08:10 AM' },
  { id: 3, type: 'Scheduled Maintenance', description: 'Planned grid update, Zone A', time: '09:00 AM' },
];

const IncidentPanel: React.FC = () => (
  <div className="bg-gray-800 rounded-xl p-6 shadow w-full max-h-60 overflow-y-auto">
    <h3 className="font-bold text-lg text-gray-100 mb-4">Recent Incidents</h3>
    <ul className="space-y-3">
      {incidents.map(inc => (
        <li key={inc.id} className="flex flex-col px-2 py-1 rounded bg-gray-700">
          <span className="font-bold text-blue-300">{inc.type}</span>
          <span className="text-gray-200 text-xs">{inc.description}</span>
          <span className="text-xs text-gray-400">{inc.time}</span>
        </li>
      ))}
    </ul>
  </div>
);

export default IncidentPanel;
