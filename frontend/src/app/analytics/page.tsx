"use client";

import { useState } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  BarChart,
  Bar,
  ResponsiveContainer,
  Cell,
} from "recharts";
import {
  useAnalyticsSummary,
  useRevenueOverTime,
  useTopProducts,
  useFeeBreakdown,
  type TopProduct,
} from "@/hooks/useAnalytics";
import { apiClient } from "@/lib/api-client";
import { Download, TrendingUp, TrendingDown, Minus } from "lucide-react";

// ── Helpers ────────────────────────────────────────────────────────────────────

function fmt(n: number) {
  return n.toLocaleString("en-US", { style: "currency", currency: "USD" });
}

function pct(n: number) {
  return `${n.toFixed(1)}%`;
}

function toISO(d: Date) {
  return d.toISOString().split("T")[0];
}

function addDays(d: Date, days: number) {
  const r = new Date(d);
  r.setDate(r.getDate() + days);
  return r;
}

const QUICK_RANGES = [
  { label: "7d", days: 7 },
  { label: "30d", days: 30 },
  { label: "90d", days: 90 },
];

const FEE_COLORS = ["#3b82f6", "#8b5cf6", "#ec4899", "#f59e0b", "#10b981", "#6b7280"];

// ── Date range bar ─────────────────────────────────────────────────────────────

function DateRangeBar({
  from,
  to,
  onFrom,
  onTo,
}: {
  from: Date;
  to: Date;
  onFrom: (d: Date) => void;
  onTo: (d: Date) => void;
}) {
  return (
    <div className="flex flex-wrap items-center gap-3 mb-6">
      <div className="flex items-center gap-2">
        <label className="text-sm text-gray-500">From</label>
        <input
          type="date"
          value={toISO(from)}
          max={toISO(to)}
          onChange={(e) => onFrom(new Date(e.target.value))}
          className="border rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>
      <div className="flex items-center gap-2">
        <label className="text-sm text-gray-500">To</label>
        <input
          type="date"
          value={toISO(to)}
          min={toISO(from)}
          max={toISO(new Date())}
          onChange={(e) => onTo(new Date(e.target.value))}
          className="border rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>
      <div className="flex gap-1">
        {QUICK_RANGES.map(({ label, days }) => (
          <button
            key={label}
            onClick={() => {
              const t = new Date();
              onTo(t);
              onFrom(addDays(t, -days));
            }}
            className="px-3 py-1.5 border rounded-lg text-sm hover:bg-gray-50 font-medium"
          >
            Last {label}
          </button>
        ))}
      </div>
    </div>
  );
}

// ── KPI cards ──────────────────────────────────────────────────────────────────

function ChangeBadge({ current, previous }: { current: number; previous?: number }) {
  if (previous == null || previous === 0) return null;
  const delta = ((current - previous) / Math.abs(previous)) * 100;
  const positive = delta >= 0;
  const Icon = delta === 0 ? Minus : positive ? TrendingUp : TrendingDown;
  return (
    <span
      className={`inline-flex items-center gap-0.5 text-xs font-medium ${
        positive ? "text-green-600" : "text-red-500"
      }`}
    >
      <Icon size={12} />
      {Math.abs(delta).toFixed(1)}%
    </span>
  );
}

function KpiCard({
  label,
  value,
  current,
  previous,
  loading,
}: {
  label: string;
  value: string;
  current: number;
  previous?: number;
  loading: boolean;
}) {
  return (
    <div className="bg-white rounded-lg border p-4">
      <p className="text-sm text-gray-500 mb-1">{label}</p>
      {loading ? (
        <div className="h-7 w-24 bg-gray-100 rounded animate-pulse" />
      ) : (
        <>
          <p className="text-2xl font-bold text-gray-900">{value}</p>
          <div className="mt-1 h-4">
            <ChangeBadge current={current} previous={previous} />
          </div>
        </>
      )}
    </div>
  );
}

// ── Revenue chart ──────────────────────────────────────────────────────────────

function RevenueChart({ from, to }: { from: Date; to: Date }) {
  const days = Math.round((to.getTime() - from.getTime()) / 86_400_000);
  const granularity = days > 90 ? "month" : days > 30 ? "week" : "day";
  const { data = [], isLoading } = useRevenueOverTime(from, to, granularity);

  const formatted = data.map((d) => ({
    ...d,
    label: new Date(d.period).toLocaleDateString("en-US", {
      month: "short",
      day: granularity === "month" ? undefined : "numeric",
    }),
  }));

  return (
    <div className="bg-white rounded-lg border p-6">
      <h2 className="font-semibold text-gray-800 mb-4">Revenue & Profit</h2>
      {isLoading ? (
        <div className="h-56 flex items-center justify-center text-gray-300 text-sm">Loading…</div>
      ) : formatted.length === 0 ? (
        <div className="h-56 flex items-center justify-center text-gray-400 text-sm">
          No data for this period.
        </div>
      ) : (
        <ResponsiveContainer width="100%" height={220}>
          <LineChart data={formatted}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis dataKey="label" tick={{ fontSize: 11 }} />
            <YAxis tick={{ fontSize: 11 }} tickFormatter={(v) => `$${v}`} width={60} />
            <Tooltip formatter={(v: number) => fmt(v)} />
            <Legend />
            <Line
              type="monotone"
              dataKey="revenue"
              name="Revenue"
              stroke="#3b82f6"
              strokeWidth={2}
              dot={false}
            />
            <Line
              type="monotone"
              dataKey="profit"
              name="Profit"
              stroke="#10b981"
              strokeWidth={2}
              dot={false}
            />
          </LineChart>
        </ResponsiveContainer>
      )}
    </div>
  );
}

// ── Fee breakdown chart ────────────────────────────────────────────────────────

function FeeBreakdownChart({ from, to }: { from: Date; to: Date }) {
  const { data, isLoading } = useFeeBreakdown(from, to);

  const chartData = data
    ? [
        { name: "Final Value Fee", value: data.final_value_fees },
        { name: "Promoted Fee", value: data.promoted_fees },
        { name: "Intl Fee", value: data.international_fees },
        { name: "COGS", value: data.cogs },
        { name: "Shipping", value: data.shipping_costs },
        { name: "Net Profit", value: data.net_profit },
      ].filter((d) => d.value > 0)
    : [];

  return (
    <div className="bg-white rounded-lg border p-6">
      <h2 className="font-semibold text-gray-800 mb-4">Cost & Profit Breakdown</h2>
      {isLoading ? (
        <div className="h-56 flex items-center justify-center text-gray-300 text-sm">Loading…</div>
      ) : chartData.length === 0 ? (
        <div className="h-56 flex items-center justify-center text-gray-400 text-sm">
          No data for this period.
        </div>
      ) : (
        <ResponsiveContainer width="100%" height={220}>
          <BarChart data={chartData} layout="vertical">
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" horizontal={false} />
            <XAxis type="number" tick={{ fontSize: 11 }} tickFormatter={(v) => `$${v}`} />
            <YAxis type="category" dataKey="name" tick={{ fontSize: 11 }} width={110} />
            <Tooltip formatter={(v: number) => fmt(v)} />
            <Bar dataKey="value" name="Amount" radius={[0, 4, 4, 0]}>
              {chartData.map((_, i) => (
                <Cell key={i} fill={FEE_COLORS[i % FEE_COLORS.length]} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      )}
    </div>
  );
}

// ── Top products ───────────────────────────────────────────────────────────────

function TopProductsTable({ from, to }: { from: Date; to: Date }) {
  const [sortBy, setSortBy] = useState<"revenue" | "profit" | "units">("revenue");
  const { data: products = [], isLoading } = useTopProducts(from, to, sortBy, 10);

  const SortBtn = ({ field, label }: { field: typeof sortBy; label: string }) => (
    <button
      onClick={() => setSortBy(field)}
      className={`px-3 py-1 rounded-lg text-sm ${
        sortBy === field
          ? "bg-blue-600 text-white"
          : "border hover:bg-gray-50 text-gray-600"
      }`}
    >
      {label}
    </button>
  );

  return (
    <div className="bg-white rounded-lg border p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="font-semibold text-gray-800">Top Products</h2>
        <div className="flex gap-1.5">
          <SortBtn field="revenue" label="Revenue" />
          <SortBtn field="profit" label="Profit" />
          <SortBtn field="units" label="Units" />
        </div>
      </div>

      {isLoading ? (
        <div className="text-gray-300 text-sm text-center py-8">Loading…</div>
      ) : products.length === 0 ? (
        <div className="text-gray-400 text-sm text-center py-8">
          No sales data for this period.
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="border-b">
              <tr>
                <th className="pb-2 text-left font-medium text-gray-500">Product</th>
                <th className="pb-2 text-right font-medium text-gray-500">Units</th>
                <th className="pb-2 text-right font-medium text-gray-500">Revenue</th>
                <th className="pb-2 text-right font-medium text-gray-500">Profit</th>
                <th className="pb-2 text-right font-medium text-gray-500">Margin</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {products.map((p: TopProduct) => (
                <tr key={p.product_id} className="hover:bg-gray-50">
                  <td className="py-2.5 pr-4">
                    <p className="font-medium text-gray-800 truncate max-w-xs">{p.title}</p>
                    {p.sku && <p className="text-xs text-gray-400">{p.sku}</p>}
                  </td>
                  <td className="py-2.5 text-right text-gray-600">{p.units_sold}</td>
                  <td className="py-2.5 text-right font-medium text-gray-800">{fmt(p.revenue)}</td>
                  <td className="py-2.5 text-right text-green-600">{fmt(p.profit)}</td>
                  <td className="py-2.5 text-right">
                    <span
                      className={`inline-block px-2 py-0.5 rounded-full text-xs font-medium ${
                        p.avg_margin_pct >= 20
                          ? "bg-green-100 text-green-700"
                          : p.avg_margin_pct >= 10
                          ? "bg-yellow-100 text-yellow-700"
                          : "bg-red-100 text-red-700"
                      }`}
                    >
                      {pct(p.avg_margin_pct)}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

// ── Export buttons ─────────────────────────────────────────────────────────────

function ExportButtons({ from, to }: { from: Date; to: Date }) {
  async function download(endpoint: string, filename: string) {
    const resp = await apiClient.get(endpoint, {
      params: { from_date: toISO(from), to_date: toISO(to) },
      responseType: "blob",
    });
    const url = URL.createObjectURL(resp.data as Blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
  }

  return (
    <div className="flex gap-3">
      <button
        onClick={() =>
          download("/export/orders", `orders_${toISO(from)}_${toISO(to)}.csv`)
        }
        className="inline-flex items-center gap-2 px-4 py-2 border rounded-lg text-sm hover:bg-gray-50"
      >
        <Download size={15} /> Export Orders CSV
      </button>
      <button
        onClick={() =>
          download(
            "/export/profitability",
            `profitability_${toISO(from)}_${toISO(to)}.csv`
          )
        }
        className="inline-flex items-center gap-2 px-4 py-2 border rounded-lg text-sm hover:bg-gray-50"
      >
        <Download size={15} /> Export Profitability CSV
      </button>
    </div>
  );
}

// ── Page ───────────────────────────────────────────────────────────────────────

export default function AnalyticsPage() {
  const [from, setFrom] = useState(() => addDays(new Date(), -30));
  const [to, setTo] = useState(() => new Date());

  const { data: summary, isLoading: summaryLoading } = useAnalyticsSummary(from, to);
  const prev = summary?.previous_period;

  return (
    <div>
      <div className="flex items-center justify-between mb-2">
        <h1 className="text-2xl font-bold">Analytics</h1>
        <ExportButtons from={from} to={to} />
      </div>

      <DateRangeBar from={from} to={to} onFrom={setFrom} onTo={setTo} />

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <KpiCard
          label="Revenue"
          value={fmt(summary?.gross_revenue ?? 0)}
          current={summary?.gross_revenue ?? 0}
          previous={prev?.gross_revenue}
          loading={summaryLoading}
        />
        <KpiCard
          label="Net Profit"
          value={fmt(summary?.net_profit ?? 0)}
          current={summary?.net_profit ?? 0}
          previous={prev?.net_profit}
          loading={summaryLoading}
        />
        <KpiCard
          label="Orders"
          value={String(summary?.order_count ?? 0)}
          current={summary?.order_count ?? 0}
          previous={prev?.order_count}
          loading={summaryLoading}
        />
        <KpiCard
          label="Avg Margin"
          value={pct(summary?.avg_margin_pct ?? 0)}
          current={summary?.avg_margin_pct ?? 0}
          previous={prev?.avg_margin_pct}
          loading={summaryLoading}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        <RevenueChart from={from} to={to} />
        <FeeBreakdownChart from={from} to={to} />
      </div>

      <TopProductsTable from={from} to={to} />
    </div>
  );
}
