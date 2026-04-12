import type { Metadata } from "next";
import "./globals.css";
import { QueryProvider } from "@/components/providers/QueryProvider";

export const metadata: Metadata = {
  title: "Ассистент NetOps",
  description: "Рабочее пространство для ежедневных операций, отчётов и планов ночных работ",
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
