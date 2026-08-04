export interface Order {
  id: string;
  ebay_order_id: string;
  buyer_username: string;
  order_status: string;
  payment_status: string;
  total_amount: number;
  subtotal: number;
  shipping_cost: number;
  tax_amount: number;
  ebay_fees_total: number;
  shipping_carrier?: string;
  tracking_number?: string;
  shipped_at?: string;
  paid_at?: string;
  aliexpress_order_id?: string;
  aliexpress_order_status?: string;
  aliexpress_tracking_number?: string;
  shipping_address: ShippingAddress;
  line_items: OrderLineItem[];
  created_at: string;
  updated_at: string;
}

export interface ShippingAddress {
  name: string;
  addressLine1: string;
  addressLine2?: string;
  city: string;
  stateOrProvince: string;
  postalCode: string;
  countryCode: string;
}

export interface OrderLineItem {
  id: string;
  ebay_line_item_id: string;
  title: string;
  sku: string;
  quantity: number;
  unit_price: number;
  total_price: number;
  ebay_final_value_fee?: number;
  ebay_payment_processing_fee?: number;
  ebay_promoted_listing_fee?: number;
  listing_id?: string;
  product_id?: string;
}

export interface OrderListItem {
  id: string;
  ebay_order_id: string;
  buyer_username: string;
  order_status: string;
  payment_status: string;
  total_amount: number;
  tracking_number?: string;
  paid_at?: string;
  created_at: string;
}

export type OrderStatus =
  | "NOT_STARTED"
  | "IN_PROGRESS"
  | "FULFILLED"
  | "CANCELLED";

export type PaymentStatus = "PENDING" | "PAID" | "FAILED" | "REFUNDED";
