import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import type { Listing, ListingCreate } from "@/types/listing";

export function useListings(params?: {
  page?: number;
  page_size?: number;
  status?: string;
}) {
  const page = params?.page ?? 1;
  const page_size = params?.page_size ?? 25;
  return useQuery<{ items: Listing[]; total: number; page: number; page_size: number }>({
    queryKey: ["listings", page, page_size, params?.status],
    queryFn: async () => {
      const { data } = await apiClient.get("/listings", {
        params: { page, page_size, status: params?.status },
      });
      return data;
    },
  });
}

export function useListing(id: string | null) {
  return useQuery<Listing>({
    queryKey: ["listings", id],
    queryFn: async () => {
      const { data } = await apiClient.get(`/listings/${id}`);
      return data;
    },
    enabled: !!id,
  });
}

export function useCreateListing() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (payload: ListingCreate) => {
      const { data } = await apiClient.post("/listings", payload);
      return data as Listing;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["listings"] });
    },
  });
}

export function usePublishListing() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (listingId: string) => {
      const { data } = await apiClient.post(`/ebay/listings/${listingId}/publish`);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["listings"] });
    },
  });
}

export function useEndListing() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (listingId: string) => {
      const { data } = await apiClient.post(`/ebay/listings/${listingId}/end`);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["listings"] });
    },
  });
}

export function useSyncListings() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async () => {
      const { data } = await apiClient.post("/ebay/sync/listings");
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["listings"] });
    },
  });
}
