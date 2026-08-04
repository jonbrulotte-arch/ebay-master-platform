"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { apiClient } from "@/lib/api-client";
import { Bell, Check } from "lucide-react";

const navItems = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/products", label: "Products" },
  { href: "/listings", label: "Listings" },
  { href: "/orders", label: "Orders" },
  { href: "/inventory", label: "Inventory" },
  { href: "/pricing", label: "Pricing" },
  { href: "/suppliers", label: "Suppliers" },
  { href: "/analytics", label: "Analytics" },
  { href: "/returns", label: "Returns" },
  { href: "/messages", label: "Messages" },
  { href: "/jobs", label: "Jobs" },
  { href: "/settings", label: "Settings" },
];

interface Notification {
  id: string;
  type: string;
  title: string;
  message: string | null;
  severity: string;
  is_read: boolean;
  created_at: string;
}

function NotificationBell() {
  const qc = useQueryClient();
  const [open, setOpen] = useState(false);

  const { data: unreadData } = useQuery<{ count: number }>({
    queryKey: ["notifications-unread"],
    queryFn: async () => {
      const { data } = await apiClient.get("/notifications/unread-count");
      return data;
    },
    refetchInterval: 30_000,
  });

  const { data: notifData } = useQuery<{ items: Notification[] }>({
    queryKey: ["notifications-recent"],
    queryFn: async () => {
      const { data } = await apiClient.get("/notifications", { params: { page_size: 10 } });
      return data;
    },
    enabled: open,
  });

  const markAll = useMutation({
    mutationFn: () => apiClient.post("/notifications/read-all"),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["notifications-unread"] });
      qc.invalidateQueries({ queryKey: ["notifications-recent"] });
    },
  });

  const unread = unreadData?.count ?? 0;
  const notifications = notifData?.items ?? [];

  const SEVERITY_COLORS: Record<string, string> = {
    INFO: "bg-blue-100 text-blue-700",
    WARNING: "bg-yellow-100 text-yellow-700",
    ERROR: "bg-red-100 text-red-700",
  };

  return (
    <div className="relative">
      <button
        onClick={() => setOpen((o) => !o)}
        className="relative p-1.5 text-gray-500 hover:text-gray-700 rounded-lg hover:bg-gray-100"
      >
        <Bell size={20} />
        {unread > 0 && (
          <span className="absolute -top-0.5 -right-0.5 bg-red-500 text-white text-xs rounded-full w-4 h-4 flex items-center justify-center font-medium">
            {unread > 9 ? "9+" : unread}
          </span>
        )}
      </button>

      {open && (
        <>
          <div className="fixed inset-0 z-40" onClick={() => setOpen(false)} />
          <div className="absolute right-0 top-10 w-80 bg-white rounded-xl shadow-xl border z-50">
            <div className="flex items-center justify-between px-4 py-3 border-b">
              <p className="font-semibold text-gray-800 text-sm">Notifications</p>
              <button
                onClick={() => markAll.mutate()}
                className="flex items-center gap-1 text-xs text-gray-500 hover:text-gray-700"
              >
                <Check size={12} /> Mark all read
              </button>
            </div>
            <div className="max-h-80 overflow-y-auto">
              {notifications.length === 0 ? (
                <p className="text-center py-8 text-sm text-gray-400">No notifications</p>
              ) : (
                notifications.map((n) => (
                  <div
                    key={n.id}
                    className={`px-4 py-3 border-b last:border-b-0 ${!n.is_read ? "bg-blue-50" : ""}`}
                  >
                    <div className="flex items-start gap-2">
                      <span
                        className={`text-xs px-1.5 py-0.5 rounded font-medium shrink-0 mt-0.5 ${
                          SEVERITY_COLORS[n.severity] ?? "bg-gray-100 text-gray-600"
                        }`}
                      >
                        {n.type.replace(/_/g, " ")}
                      </span>
                    </div>
                    <p className="text-sm font-medium text-gray-800 mt-1">{n.title}</p>
                    {n.message && (
                      <p className="text-xs text-gray-500 mt-0.5 line-clamp-2">{n.message}</p>
                    )}
                    <p className="text-xs text-gray-400 mt-1">
                      {new Date(n.created_at).toLocaleString()}
                    </p>
                  </div>
                ))
              )}
            </div>
            <div className="px-4 py-2 border-t">
              <Link
                href="/notifications"
                className="text-xs text-blue-600 hover:underline"
                onClick={() => setOpen(false)}
              >
                View all notifications →
              </Link>
            </div>
          </div>
        </>
      )}
    </div>
  );
}

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
          <div className="flex items-center gap-2">
            <NotificationBell />
          </div>
        </header>
        <div className="p-6">{children}</div>
      </main>
    </div>
  );
}
