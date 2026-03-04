'use client';

import React from "react";
import UnifiedMap from "@/components/shared/UnifiedMap";

const MapAndControls: React.FC = () => (
  <div className="flex flex-col items-center bg-gray-800 rounded-xl shadow-lg p-6 min-h-[320px]">
    <div className="flex-1 w-full flex items-center justify-center min-h-[200px] border border-gray-700 rounded bg-gray-700 text-gray-400 mb-4">
      <UnifiedMap />
    </div>
    <div className="flex space-x-4">
      <button className="px-4 py-2 rounded bg-blue-600 text-white hover:bg-blue-700 transition">Refresh</button>
      <button className="px-4 py-2 rounded bg-green-600 text-white hover:bg-green-700 transition">Zoom In</button>
      <button className="px-4 py-2 rounded bg-yellow-600 text-white hover:bg-yellow-700 transition">Zoom Out</button>
    </div>
  </div>
);

export default MapAndControls;
