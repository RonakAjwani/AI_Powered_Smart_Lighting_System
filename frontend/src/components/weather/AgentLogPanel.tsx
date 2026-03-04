import React from "react";

const logs = [
  "07:45 Poll completed for Zone A (22°C)",
  "07:46 Heatwave warning triggered in Midtown.",
  "08:01 Light pole 038 offline (Airport)",
];

const AgentLogPanel: React.FC = () => (
  <div className="bg-gray-800 rounded-xl p-6 shadow w-full">
    <h3 className="font-bold text-lg text-gray-100 mb-2">Agent Log</h3>
    <div className="bg-gray-900 rounded p-2 h-32 overflow-y-auto mt-2 text-xs text-gray-300 font-mono">
      {logs.map((line, idx) => (
        <div key={idx} className="whitespace-pre text-gray-400">{line}</div>
      ))}
    </div>
  </div>
);

export default AgentLogPanel;
