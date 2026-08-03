export interface Product {
  id: string;
  sku: string;
  title: string;
  description?: string;
  category_id?: string;
  condition: string;
  condition_description?: string;
  brand?: string;
  mpn?: string;
  upc?: string;
  ean?: string;
  isbn?: string;
  item_specifics?: Record<string, string>;
  weight_oz?: number;
  dimensions?: { length: number; width: number; height: number; unit: string };
  is_active: boolean;
  tags?: string[];
  notes?: string;
  images: ProductImage[];
  created_at: string;
  updated_at: string;
}

export interface ProductImage {
  id: string;
  url: string;
  position: number;
  is_primary: boolean;
  original_filename?: string;
  width?: number;
  height?: number;
  created_at: string;
}

export interface ProductListItem {
  id: string;
  sku: string;
  title: string;
  brand?: string;
  condition: string;
  category_id?: string;
  is_active: boolean;
  created_at: string;
}
