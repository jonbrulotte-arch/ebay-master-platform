"use client";

import { useTodaySummary } from "@/hooks/useAnalytics";
import { useOrders } from "@/hooks/useOrders";
import { TrendingUp, ShoppingBag, Tag, BarChart2, RefreshCw } from "lucide-react";

function fmt(n: number) {
  return n.toLocaleString("en-US", { style: "currency", currency: "USD" });
}

function KpiCard({
  title,
  value,
  icon: Icon,
  loading,
  color = "text-blue-600",
}: {
  title: string;
  value: string;
  icon: React.ElementType;
  loading: boolean;
  color?: string;
}) {
  return (
    <div className="bg-white rounded-lg border p-5">
      <div className="flex items-center justify-between mb-3">
        <p className="text-sm font-medium text-gray-500">{title}</p>
        <div className={`p-2 rounded-lg bg-gray-50 ${color}`}>
          <Icon size={18} />
        </div>
      </div>
      {loading ? (
        <div className="h-8 w-28 bg-gray-100 rounded animate-pulse" />
      ) : (
        <p className="text-2xl font-bold text-gray-900">{value}</p>
      )}
    </div>
  );
}

const STATUS_COLORS: Record<string, string> = {
  FULFILLED: "bg-green-100 text-green-700",
  SHIPPED: "bg-blue-100 text-blue-700",
  IN_PROGRESS: "bg-yellow-100 text-yellow-700",
  NOT_STARTED: "bg-gray-100 text-gray-600",
  CANCELLED: "bg-red-100 text-red-700",
};

export default function DashboardPage() {
  const { data: summary, isLoading: summaryLoading, refetch } = useTodaySummary();
  const { data: ordersData, isLoading: ordersLoading } = useOrders({ page: 1, page_size: 5 });

  const recentOrders = ordersData?.items ?? [];

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">Dashboard</h1>
        <button
          onClick={() => refetch()}
          className="inline-flex items-center gap-2 px-3 py-1.5 border rounded-lg text-sm hover:bg-gray-50 text-gray-600"
        >
          <RefreshCw size={14} />
          Refresh
        </button>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <KpiCard
          title="Today's Revenue"
          value={fmt(summary?.gross_revenue ?? 0)}
          icon={TrendingUp}
          loading={summaryLoading}
          color="text-blue-600"
        />
        <KpiCard
          title="Orders Today"
          value={String(summary?.order_count ?? 0)}
          icon={ShoppingBag}
          loading={summaryLoading}
          color="text-purple-600"
        />
        <KpiCard
          title="Units Sold"
          value={String(summary?.units_sold ?? 0)}
          icon={Tag}
          loading={summaryLoading}
          color="text-orange-600"
        />
        <KpiCard
          title="Avg Margin"
          value={`${(summary?.avg_margin_pct ?? 0).toFixed(1)}%`}
          icon={BarChart2}
          loading={summaryLoading}
          color="text-green-600"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Orders */}
        <div className="bg-white rounded-lg border p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold text-gray-800">Recent Orders</h3>
            <a href="/orders" className="text-sm text-blue-600 hover:underline">
              View all
            </a>
          </div>

          {ordersLoading ? (
            <div className="space-y-3">
              {[...Array(3)].map((_, i) => (
                <div key={i} className="h-12 bg-gray-50 rounded animate-pulse" />
              ))}
            </div>
          ) : recentOrders.length === 0 ? (
            <p className="text-gray-400 text-sm">
              No orders yet. Connect your eBay account to start syncing.
            </p>
          ) : (
            <ul className="divide-y">
              {recentOrders.map((order) => (
                <li key={order.id} className="py-3 flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-800">
                      {order.ebay_order_id}
                    </p>
                    <p className="text-xs text-gray-400">
                      {order.buyer_username || "—"} ·{" "}
                      {order.paid_at
                        ? new Date(order.paid_at).toLocaleDateString()
                        : "Pending payment"}
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-semibold text-gray-900">
                      {fmt(order.total_amount)}
                    </p>
                    <span
                      className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                        STATUS_COLORS[order.order_status] ?? "bg-gray-100 text-gray-600"
                      }`}
                    >
                      {order.order_status.replace(/_/g, " ")}
                    </span>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>

        {/* Today's Summary */}
        <div className="bg-white rounded-lg border p-6">
          <h3 className="font-semibold text-gray-800 mb-4">Today's Summary</h3>
          {summaryLoading ? (
            <div className="space-y-3">
              {[...Array(4)].map((_, i) => (
                <div key={i} className="h-6 bg-gray-50 rounded animate-pulse" />
              ))}
            </div>
          ) : (
            <dl className="space-y-3">
              <SummaryRow label="Gross Revenue" value={fmt(summary?.gross_revenue ?? 0)} />
              <SummaryRow label="Net Profit" value={fmt(summary?.net_profit ?? 0)} highlight />
              <SummaryRow label="Total eBay Fees" value={fmt(summary?.total_fees ?? 0)} />
              <SummaryRow label="Units Sold" value={String(summary?.units_sold ?? 0)} />
              <SummaryRow label="Avg Margin" value={`${(summary?.avg_margin_pct ?? 0).toFixed(1)}%`} />
              <SummaryRow label="Avg ROI" value={`${(summary?.avg_roi_pct ?? 0).toFixed(1)}%`} />
            </dl>
          )}

          <div className="mt-5 pt-4 border-t">
            <a
              href="/analytics"
              className="text-sm text-blue-600 hover:underline font-medium"
            >
              View full analytics →
            </a>
          </div>
        </div>
      </div>
    </div>
  );
}

function SummaryRow({
  label,
  value,
  highlight,
}: {
  label: string;
  value: string;
  highlight?: boolean;
}) {
  return (
    <div className="flex items-center justify-between">
      <dt className="text-sm text-gray-500">{label}</dt>
      <dd className={`text-sm font-semibold ${highlight ? "text-green-600" : "text-gray-800"}`}>
        {value}
      </dd>
    </div>
  );
}
