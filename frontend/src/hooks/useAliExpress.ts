"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";

export interface AliExpressProduct {
  product_id: string;
  title: string;
  sale_price_usd: number;
  original_price_usd: number | null;
  image_url: string | null;
  product_url: string | null;
  store_name: string | null;
  store_id: string | null;
  avg_star_rating: number | null;
  total_orders: number | null;
  shipping_lead_days: number | null;
}

export interface AliExpressSearchResponse {
  products: AliExpressProduct[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface ImportRequest {
  product_id: string;
  title: string;
  sale_price_usd: number;
  image_url?: string | null;
  product_url?: string | null;
  store_name?: string | null;
  store_id?: string | null;
  sku?: string | null;
  shipping_cost_usd?: number;
  supplier_id?: string | null;
}

export interface ImportResponse {
  product_id: string;
  supplier_id: string;
  product_supplier_id: string;
  sku: string;
  title: string;
}

export interface CurrencyRate {
  from_currency: string;
  to_currency: string;
  rate: number;
  safety_margin_pct: number;
  effective_rate: number;
  updated_at: string;
}

export function useAliExpressSearch(
  query: string,
  page = 1,
  page_size = 20,
  enabled = true
) {
  return useQuery<AliExpressSearchResponse>({
    queryKey: ["aliexpress-search", query, page, page_size],
    queryFn: async () => {
      const { data } = await apiClient.get<AliExpressSearchResponse>("/aliexpress/search", {
        params: { query, page, page_size },
      });
      return data;
    },
    enabled: enabled && query.trim().length >= 2,
    staleTime: 120_000,
  });
}

export function useImportProduct() {
  const qc = useQueryClient();
  return useMutation<ImportResponse, Error, ImportRequest>({
    mutationFn: async (body) => {
      const { data } = await apiClient.post<ImportResponse>("/aliexpress/import", body);
      return data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["products"] });
      qc.invalidateQueries({ queryKey: ["suppliers"] });
    },
  });
}

export function useForwardOrder() {
  return useMutation<
    { order_id: string; aliexpress_order_id: string; status: string },
    Error,
    { orderId: string; sku_id?: string; logistics_service?: string }
  >({
    mutationFn: async ({ orderId, sku_id, logistics_service }) => {
      const { data } = await apiClient.post(`/aliexpress/orders/${orderId}/forward`, {
        sku_id,
        logistics_service: logistics_service ?? "YANWEN_REGULAR_AIRMAIL",
      });
      return data;
    },
  });
}

export function useCurrencyRate(safety_margin_pct = 2.0) {
  return useQuery<CurrencyRate>({
    queryKey: ["aliexpress-currency", safety_margin_pct],
    queryFn: async () => {
      const { data } = await apiClient.get<CurrencyRate>("/aliexpress/currency", {
        params: { safety_margin_pct },
      });
      return data;
    },
    staleTime: 3_600_000, // 1 hour
  });
}
