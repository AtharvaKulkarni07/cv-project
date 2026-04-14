import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Pano, Elite Panorama Stitching",
  description: "The computer vision layer for panorama image stitching.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" data-theme="black">
      <body className={`${inter.className} min-h-screen antialiased selection:bg-orange-500/30 selection:text-orange-100`}>
        {children}
      </body>
    </html>
  );
}