import type { Metadata } from "next";
import { Manrope, Oswald } from "next/font/google";
import "./globals.css";

const manrope = Manrope({
  subsets: ["latin", "cyrillic"],
  weight: ["500"],
  variable: "--font-body",
});

const oswald = Oswald({
  subsets: ["latin", "cyrillic"],
  weight: ["700"],
  variable: "--font-display",
});

export const metadata: Metadata = {
  title: "Резюме AI — профессиональное резюме под вакансию",
  description:
    "Создайте профессиональное русскоязычное резюме под конкретную вакансию.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="ru">
      <body className={`${manrope.variable} ${oswald.variable}`}>{children}</body>
    </html>
  );
}
