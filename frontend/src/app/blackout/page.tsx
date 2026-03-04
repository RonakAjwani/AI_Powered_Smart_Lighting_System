"use client";
import React from "react";
import PowerDashboard from "@/components/power/PowerDashboard";
import ZonePowerPanel from "@/components/shared/ZonePowerPanel";
import IncidentPanel from "@/components/shared/IncidentPanel";
import BlackoutSimulator from "@/components/shared/BlackoutSimulator";
import MapAndControls from "@/components/shared/MapAndControls";

export default function BlackoutDashboardPage() {
  return (
    <div className="flex items-center justify-center h-full w-full text-gray-400 text-xl">
      Please use the sidebar to view the Blackout dashboard on the main page.
    </div>
  );
}
