"use client";

import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";

export interface SummaryResponse {
  order_count: number;
  gross_revenue: number;
  net_profit: number;
  avg_margin_pct: number;
  avg_roi_pct: number;
  units_sold: number;
  total_fees: number;
  previous_period?: SummaryResponse;
}

export interface RevenueDataPoint {
  period: string;
  revenue: number;
  profit: number;
  orders: number;
  units: number;
}

export interface TopProduct {
  product_id: string;
  title: string;
  sku: string | null;
  units_sold: number;
  revenue: number;
  profit: number;
  avg_margin_pct: number;
}

export interface FeeBreakdown {
  final_value_fees: number;
  promoted_fees: number;
  international_fees: number;
  cogs: number;
  shipping_costs: number;
  net_profit: number;
}

function toParam(d: Date) {
  return d.toISOString().split("T")[0];
}

export function useAnalyticsSummary(fromDate: Date, toDate: Date) {
  return useQuery<SummaryResponse>({
    queryKey: ["analytics-summary", toParam(fromDate), toParam(toDate)],
    queryFn: async () => {
      const { data } = await apiClient.get<SummaryResponse>("/analytics/summary", {
        params: {
          from_date: toParam(fromDate),
          to_date: toParam(toDate),
          include_previous: true,
        },
      });
      return data;
    },
    staleTime: 60_000,
  });
}

export function useRevenueOverTime(
  fromDate: Date,
  toDate: Date,
  granularity: "day" | "week" | "month" = "day"
) {
  return useQuery<RevenueDataPoint[]>({
    queryKey: ["analytics-revenue", toParam(fromDate), toParam(toDate), granularity],
    queryFn: async () => {
      const { data } = await apiClient.get<RevenueDataPoint[]>("/analytics/revenue-over-time", {
        params: { from_date: toParam(fromDate), to_date: toParam(toDate), granularity },
      });
      return data;
    },
    staleTime: 60_000,
  });
}

export function useTopProducts(
  fromDate: Date,
  toDate: Date,
  sortBy: "revenue" | "profit" | "units" = "revenue",
  limit = 10
) {
  return useQuery<TopProduct[]>({
    queryKey: ["analytics-top-products", toParam(fromDate), toParam(toDate), sortBy, limit],
    queryFn: async () => {
      const { data } = await apiClient.get<TopProduct[]>("/analytics/top-products", {
        params: {
          from_date: toParam(fromDate),
          to_date: toParam(toDate),
          sort_by: sortBy,
          limit,
        },
      });
      return data;
    },
    staleTime: 60_000,
  });
}

export function useFeeBreakdown(fromDate: Date, toDate: Date) {
  return useQuery<FeeBreakdown>({
    queryKey: ["analytics-fees", toParam(fromDate), toParam(toDate)],
    queryFn: async () => {
      const { data } = await apiClient.get<FeeBreakdown>("/analytics/fee-breakdown", {
        params: { from_date: toParam(fromDate), to_date: toParam(toDate) },
      });
      return data;
    },
    staleTime: 60_000,
  });
}

export function useTodaySummary() {
  const today = new Date();
  return useAnalyticsSummary(today, today);
}
