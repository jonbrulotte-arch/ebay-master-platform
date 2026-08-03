export interface Listing {
  id: string;
  product_id: string;
  marketplace: string;
  ebay_item_id?: string;
  ebay_offer_id?: string;
  listing_type: string;
  status: ListingStatus;
  title: string;
  price: number;
  currency: string;
  quantity_listed: number;
  quantity_sold: number;
  shipping_policy_id?: string;
  return_policy_id?: string;
  payment_policy_id?: string;
  listing_duration: string;
  promoted_listing_rate?: number;
  ebay_category_id?: string;
  description_html?: string;
  started_at?: string;
  ends_at?: string;
  last_synced_at?: string;
  error_messages?: Record<string, string>;
  created_at: string;
  updated_at: string;
}

export interface ListingCreate {
  product_id: string;
  title: string;
  price: number;
  quantity_listed?: number;
  ebay_category_id?: string;
  shipping_policy_id?: string;
  return_policy_id?: string;
  payment_policy_id?: string;
  description_html?: string;
  promoted_listing_rate?: number;
}

export type ListingStatus = "DRAFT" | "ACTIVE" | "ENDED" | "ERROR" | "SOLD";

export const LISTING_STATUS_COLORS: Record<ListingStatus, string> = {
  DRAFT: "bg-gray-100 text-gray-700",
  ACTIVE: "bg-green-100 text-green-700",
  ENDED: "bg-red-100 text-red-700",
  ERROR: "bg-orange-100 text-orange-700",
  SOLD: "bg-blue-100 text-blue-700",
};
