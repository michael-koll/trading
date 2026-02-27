import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Trading Strategy Framework",
  description: "Backtesting, ML optimization and paper trading workbench",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
