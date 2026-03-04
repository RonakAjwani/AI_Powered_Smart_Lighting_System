import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import ToastProvider from "@/components/shared/ToastProvider";
import MissionControlLayout from "@/components/layout/MissionControlLayout";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "AI Smart Lighting System",
  description: "AI-Powered Smart Lighting Management System",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      {/* Leaflet CSS loaded globally to fix map rendering */}
      <head>
        <link
          rel="stylesheet"
          href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"
          integrity="sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY="
          crossOrigin=""
        />
      </head>
      <body className="bg-[#0a1628] text-white">
        <ToastProvider />
        <MissionControlLayout>
          {children}
        </MissionControlLayout>
      </body>
    </html>
  );
}
