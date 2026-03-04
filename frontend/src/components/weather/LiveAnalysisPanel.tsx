import React from "react";

const LiveAnalysisPanel: React.FC = () => (
  <div className="bg-gray-800 rounded-xl p-6 shadow w-full">
    <h3 className="font-bold text-lg text-gray-100 mb-2">Live AI Analysis</h3>
    <div className="bg-gray-900 p-3 rounded text-xs text-green-200 font-mono max-h-40 overflow-auto">
      {/* Replace with real agent output from Redux */}
      {`{
  "agent": "WeatherAI",
  "impact": "Minimal",
  "risk_factor": 0.16,
  "actions": ["Monitor", "Alert"]
}`}
    </div>
  </div>
);

export default LiveAnalysisPanel;
