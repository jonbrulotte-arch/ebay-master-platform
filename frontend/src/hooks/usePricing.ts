"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";

export interface FeeCalculationRequest {
  sold_price: number;
  item_cost?: number;
  actual_shipping_cost?: number;
  store_level?: string;
  category_name?: string;
  shipping_charge_to_buyer?: number;
  seller_discount_pct?: number;
  promoted_rate?: number;
  sales_tax_rate?: number;
  is_top_rated_seller?: boolean;
}

export interface FeeCalculationResponse {
  sold_price: number;
  seller_discount_amount: number;
  effective_sold_price: number;
  shipping_charge_to_buyer: number;
  pre_tax_total: number;
  sales_tax_amount: number;
  total_sale: number;
  final_value_fee: number;
  promoted_fee: number;
  total_fees: number;
  payout: number;
  item_cost: number;
  actual_shipping_cost: number;
  net_profit: number;
  profit_margin_pct: number;
  roi_pct: number;
}

export interface UserSettings {
  ebay_store_level: string;
  is_top_rated_seller: boolean;
  default_promoted_rate: number;
  default_sales_tax_rate: number;
  default_fee_category: string;
}

export interface PricingRule {
  id: string;
  product_id: string | null;
  name: string;
  rule_type: string;
  min_margin_pct: number | null;
  min_price: number | null;
  max_price: number | null;
  target_margin_pct: number | null;
  reprice_strategy: string;
  is_active: boolean;
  priority: number;
  last_triggered_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface PriceChangeLog {
  id: string;
  listing_id: string;
  product_id: string;
  pricing_rule_id: string | null;
  old_price: number;
  new_price: number;
  reason: string;
  reason_detail: string | null;
  applied_to_ebay: boolean;
  ebay_update_error: string | null;
  triggered_by: string;
  created_at: string;
}

export function useFeeCalculator() {
  return useMutation<FeeCalculationResponse, Error, FeeCalculationRequest>({
    mutationFn: async (req) => {
      const { data } = await apiClient.post<FeeCalculationResponse>(
        "/pricing/fee-calculator",
        req
      );
      return data;
    },
  });
}

export function useUserSettings() {
  return useQuery<UserSettings>({
    queryKey: ["pricing-settings"],
    queryFn: async () => {
      const { data } = await apiClient.get<UserSettings>("/pricing/settings");
      return data;
    },
  });
}

export function useUpdateUserSettings() {
  const qc = useQueryClient();
  return useMutation<UserSettings, Error, Partial<UserSettings>>({
    mutationFn: async (updates) => {
      const { data } = await apiClient.put<UserSettings>(
        "/pricing/settings",
        updates
      );
      return data;
    },
    onSuccess: (data) => {
      qc.setQueryData(["pricing-settings"], data);
    },
  });
}

export function usePricingRules() {
  return useQuery<PricingRule[]>({
    queryKey: ["pricing-rules"],
    queryFn: async () => {
      const { data } = await apiClient.get<PricingRule[]>("/pricing/rules");
      return data;
    },
  });
}

export function useCreatePricingRule() {
  const qc = useQueryClient();
  return useMutation<PricingRule, Error, Partial<PricingRule>>({
    mutationFn: async (rule) => {
      const { data } = await apiClient.post<PricingRule>("/pricing/rules", rule);
      return data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["pricing-rules"] }),
  });
}

export function useUpdatePricingRule() {
  const qc = useQueryClient();
  return useMutation<PricingRule, Error, { id: string; updates: Partial<PricingRule> }>({
    mutationFn: async ({ id, updates }) => {
      const { data } = await apiClient.put<PricingRule>(
        `/pricing/rules/${id}`,
        updates
      );
      return data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["pricing-rules"] }),
  });
}

export function useDeletePricingRule() {
  const qc = useQueryClient();
  return useMutation<void, Error, string>({
    mutationFn: async (id) => {
      await apiClient.delete(`/pricing/rules/${id}`);
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["pricing-rules"] }),
  });
}

export function usePriceChangeLog(page = 1) {
  return useQuery({
    queryKey: ["price-change-log", page],
    queryFn: async () => {
      const { data } = await apiClient.get(
        `/pricing/change-log?page=${page}&page_size=50`
      );
      return data as { items: PriceChangeLog[]; total: number; total_pages: number };
    },
  });
}

export function useFeeCategories() {
  return useQuery<string[]>({
    queryKey: ["fee-categories"],
    queryFn: async () => {
      const { data } = await apiClient.get<string[]>("/pricing/categories");
      return data;
    },
    staleTime: Infinity,
  });
}
