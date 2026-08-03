"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const navItems = [
  { href: "/dashboard", label: "Dashboard", icon: "grid" },
  { href: "/products", label: "Products", icon: "package" },
  { href: "/listings", label: "Listings", icon: "tag" },
  { href: "/orders", label: "Orders", icon: "shopping-cart" },
  { href: "/inventory", label: "Inventory", icon: "warehouse" },
  { href: "/pricing", label: "Pricing", icon: "dollar-sign" },
  { href: "/suppliers", label: "Suppliers", icon: "truck" },
  { href: "/analytics", label: "Analytics", icon: "bar-chart" },
  { href: "/returns", label: "Returns", icon: "rotate-ccw" },
  { href: "/messages", label: "Messages", icon: "mail" },
  { href: "/jobs", label: "Jobs", icon: "clock" },
  { href: "/settings", label: "Settings", icon: "settings" },
];

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();

  return (
    <div className="flex h-screen">
      <aside className="w-64 bg-gray-900 text-gray-100 flex flex-col">
        <div className="p-4 border-b border-gray-700">
          <h1 className="text-xl font-bold">eBay Master</h1>
          <p className="text-xs text-gray-400 mt-1">Business Platform</p>
        </div>
        <nav className="flex-1 overflow-y-auto py-4">
          {navItems.map((item) => {
            const isActive =
              pathname === item.href ||
              (item.href !== "/dashboard" && pathname.startsWith(item.href));
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`flex items-center px-4 py-2.5 text-sm transition-colors ${
                  isActive
                    ? "bg-blue-600 text-white"
                    : "text-gray-300 hover:bg-gray-800 hover:text-white"
                }`}
              >
                {item.label}
              </Link>
            );
          })}
        </nav>
      </aside>

      <main className="flex-1 overflow-y-auto">
        <header className="bg-white border-b px-6 py-4 flex items-center justify-between">
          <h2 className="text-lg font-semibold">
            {navItems.find(
              (i) =>
                pathname === i.href ||
                (i.href !== "/dashboard" && pathname.startsWith(i.href))
            )?.label ?? "Dashboard"}
          </h2>
          <div className="flex items-center gap-4">
            <button className="relative text-gray-500 hover:text-gray-700">
              <span className="sr-only">Notifications</span>
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
              </svg>
            </button>
          </div>
        </header>
        <div className="p-6">{children}</div>
      </main>
    </div>
  );
}
