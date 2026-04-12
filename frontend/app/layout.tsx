import type { Metadata } from "next";
import "./globals.css";
import { QueryProvider } from "@/components/providers/QueryProvider";

export const metadata: Metadata = {
  title: "Ассистент NetOps",
  description: "Современное рабочее пространство для операций, отчётов, планов и таймера",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="ru">
      <body className="app-shell-root">
        <QueryProvider>{children}</QueryProvider>
      </body>
    </html>
  );
}
