import type { Metadata } from "next";
import "./globals.css";
import Sidebar from "@/components/layout/Sidebar";

export const metadata: Metadata = {
  title: "Admin Dashboard | AI Smart Lighting System",
  description: "Configure and manage AI agents for the Smart Lighting System",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      {/* Leaflet CSS for cybersecurity network map */}
      <head>
        <link
          rel="stylesheet"
          href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"
          integrity="sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY="
          crossOrigin=""
        />
      </head>
      <body>
        {/* Sidebar */}
        <Sidebar />

        {/* Content Wrapper */}
        <div className="content-wrapper">
          {children}
        </div>
      </body>
    </html>
  );
}
