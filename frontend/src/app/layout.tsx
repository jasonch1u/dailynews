import type { Metadata, Viewport } from "next";
import "./globals.css";
import ServiceWorkerRegister from "./components/ServiceWorkerRegister";

export const metadata: Metadata = {
  title: "WORLDMONITOR — AI Market Intelligence",
  description: "Real-time AI-powered news aggregation, macro signals, and market intelligence dashboard",
  icons: {
    icon: [
      { url: "/icons/icon-192.png", sizes: "192x192", type: "image/png" },
      { url: "/icons/icon-512.png", sizes: "512x512", type: "image/png" },
    ],
  },
  manifest: "/manifest.json",
  appleWebApp: {
    capable: true,
    statusBarStyle: "black-translucent",
    title: "WorldMonitor",
  },
  openGraph: {
    title: "WORLDMONITOR — AI Market Intelligence",
    description: "Real-time AI-powered macro signals, geopolitical radar, and news aggregation.",
    type: "website",
    locale: "zh_TW",
    siteName: "WorldMonitor",
  },
  twitter: {
    card: "summary",
    title: "WORLDMONITOR",
    description: "AI-powered market intelligence dashboard",
  },
};

export const viewport: Viewport = {
  themeColor: '#0a0a0f',
  width: 'device-width',
  initialScale: 1,
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="zh-TW">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="" />
        <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;500;600;700&display=swap" rel="stylesheet" />
      </head>
      <body>
        {children}
        <ServiceWorkerRegister />
      </body>
    </html>
  );
}
