import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import type { Order, OrderListItem } from "@/types/order";

export function useOrders(params?: {
  page?: number;
  page_size?: number;
  status?: string;
}) {
  const page = params?.page ?? 1;
  const page_size = params?.page_size ?? 25;
  return useQuery<{ items: OrderListItem[]; total: number; page: number; page_size: number }>({
    queryKey: ["orders", page, page_size, params?.status],
    queryFn: async () => {
      const { data } = await apiClient.get("/orders", {
        params: { page, page_size, status: params?.status },
      });
      return data;
    },
  });
}

export function useOrder(id: string | null) {
  return useQuery<Order>({
    queryKey: ["orders", id],
    queryFn: async () => {
      const { data } = await apiClient.get(`/orders/${id}`);
      return data;
    },
    enabled: !!id,
  });
}

export function useSyncOrders() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async () => {
      const { data } = await apiClient.post("/ebay/sync/orders");
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["orders"] });
    },
  });
}
