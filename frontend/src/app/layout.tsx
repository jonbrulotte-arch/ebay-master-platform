import type { Metadata } from "next";
import "./globals.css";
import { ErrorBoundary } from "@/components/ErrorBoundary";
import { Providers } from "@/components/Providers";

export const metadata: Metadata = {
  title: "eBay Master Platform",
  description: "eBay dropshipping business management platform",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="bg-gray-50 text-gray-900 antialiased">
        <Providers>
          <ErrorBoundary>{children}</ErrorBoundary>
        </Providers>
      </body>
    </html>
  );
}
