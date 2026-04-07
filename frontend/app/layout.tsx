import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "NetOps Assistant",
  description: "Рабочий кабинет сетевого инженера",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="ru">
      <body>{children}</body>
    </html>
  );
}
