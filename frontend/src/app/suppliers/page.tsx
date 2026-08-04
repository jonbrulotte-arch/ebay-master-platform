"use client";

import { useState, useCallback } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import {
  useAliExpressSearch,
  useImportProduct,
  AliExpressProduct,
} from "@/hooks/useAliExpress";
import {
  Search,
  Plus,
  ExternalLink,
  Star,
  ShoppingCart,
  Check,
  Loader2,
  Truck,
  Store,
  RefreshCw,
} from "lucide-react";

// ── Types ─────────────────────────────────────────────────────────────────────

interface Supplier {
  id: string;
  name: string;
  platform: string;
  store_url: string | null;
  store_id: string | null;
  reliability_rating: number | null;
  avg_shipping_days: number | null;
  notes: string | null;
  is_active: boolean;
  created_at: string;
}

interface SupplierCreate {
  name: string;
  platform: string;
  store_url: string | null;
  store_id: string | null;
  reliability_rating: number | null;
  avg_shipping_days: number | null;
  notes: string | null;
}

// ── Hooks ─────────────────────────────────────────────────────────────────────

function useSuppliers() {
  return useQuery<{ items: Supplier[]; total: number }>({
    queryKey: ["suppliers"],
    queryFn: async () => {
      const { data } = await apiClient.get("/suppliers");
      return data;
    },
  });
}

function useCreateSupplier() {
  const qc = useQueryClient();
  return useMutation<Supplier, Error, SupplierCreate>({
    mutationFn: async (body) => {
      const { data } = await apiClient.post("/suppliers", body);
      return data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["suppliers"] }),
  });
}

function useDeleteSupplier() {
  const qc = useQueryClient();
  return useMutation<void, Error, string>({
    mutationFn: async (id) => {
      await apiClient.delete(`/suppliers/${id}`);
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["suppliers"] }),
  });
}

// ── Helpers ───────────────────────────────────────────────────────────────────

const PLATFORM_LABELS: Record<string, string> = {
  ALIEXPRESS: "AliExpress",
  DIRECT: "Direct",
  WHOLESALE: "Wholesale",
};

function RatingStars({ rating }: { rating: number | null }) {
  if (rating == null) return <span className="text-gray-400 text-xs">No rating</span>;
  const filled = Math.round(rating * 5);
  return (
    <span className="flex items-center gap-0.5">
      {[1, 2, 3, 4, 5].map((i) => (
        <Star
          key={i}
          size={12}
          className={i <= filled ? "text-yellow-400 fill-yellow-400" : "text-gray-300"}
        />
      ))}
      <span className="text-xs text-gray-500 ml-1">{rating.toFixed(1)}</span>
    </span>
  );
}

// ── Supplier list tab ─────────────────────────────────────────────────────────

function AddSupplierModal({ onClose }: { onClose: () => void }) {
  const { mutate, isPending } = useCreateSupplier();
  const [form, setForm] = useState<SupplierCreate>({
    name: "",
    platform: "ALIEXPRESS",
    store_url: null,
    store_id: null,
    reliability_rating: null,
    avg_shipping_days: null,
    notes: null,
  });

  function submit(e: React.FormEvent) {
    e.preventDefault();
    mutate(form, { onSuccess: onClose });
  }

  return (
    <div className="fixed inset-0 bg-black/40 z-50 flex items-center justify-center">
      <div className="bg-white rounded-xl shadow-xl p-6 w-full max-w-md">
        <h2 className="font-semibold text-gray-800 text-lg mb-4">Add Supplier</h2>
        <form onSubmit={submit} className="space-y-3">
          <div>
            <label className="text-sm text-gray-600 block mb-1">Name *</label>
            <input
              required
              value={form.name}
              onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
              className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="text-sm text-gray-600 block mb-1">Platform</label>
            <select
              value={form.platform}
              onChange={(e) => setForm((f) => ({ ...f, platform: e.target.value }))}
              className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {Object.entries(PLATFORM_LABELS).map(([val, label]) => (
                <option key={val} value={val}>{label}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="text-sm text-gray-600 block mb-1">Store URL</label>
            <input
              type="url"
              value={form.store_url ?? ""}
              onChange={(e) => setForm((f) => ({ ...f, store_url: e.target.value || null }))}
              className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-sm text-gray-600 block mb-1">Rating (0–1)</label>
              <input
                type="number"
                step="0.01"
                min="0"
                max="1"
                value={form.reliability_rating ?? ""}
                onChange={(e) => setForm((f) => ({
                  ...f, reliability_rating: e.target.value ? Number(e.target.value) : null,
                }))}
                className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="text-sm text-gray-600 block mb-1">Avg Ship Days</label>
              <input
                type="number"
                min="1"
                value={form.avg_shipping_days ?? ""}
                onChange={(e) => setForm((f) => ({
                  ...f, avg_shipping_days: e.target.value ? Number(e.target.value) : null,
                }))}
                className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>
          <div>
            <label className="text-sm text-gray-600 block mb-1">Notes</label>
            <textarea
              rows={2}
              value={form.notes ?? ""}
              onChange={(e) => setForm((f) => ({ ...f, notes: e.target.value || null }))}
              className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
            />
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 border rounded-lg text-sm hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isPending}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700 disabled:opacity-50"
            >
              {isPending ? "Adding…" : "Add Supplier"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

function SupplierListTab() {
  const { data, isLoading, refetch } = useSuppliers();
  const deleteSupplier = useDeleteSupplier();
  const [showAdd, setShowAdd] = useState(false);

  const suppliers = data?.items ?? [];

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <p className="text-sm text-gray-500">{data?.total ?? 0} suppliers</p>
        <div className="flex gap-2">
          <button
            onClick={() => refetch()}
            className="inline-flex items-center gap-2 px-3 py-1.5 border rounded-lg text-sm hover:bg-gray-50 text-gray-600"
          >
            <RefreshCw size={14} /> Refresh
          </button>
          <button
            onClick={() => setShowAdd(true)}
            className="inline-flex items-center gap-2 px-3 py-1.5 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700"
          >
            <Plus size={14} /> Add Supplier
          </button>
        </div>
      </div>

      {showAdd && <AddSupplierModal onClose={() => setShowAdd(false)} />}

      {isLoading ? (
        <div className="space-y-3">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="h-20 bg-gray-50 rounded-lg animate-pulse" />
          ))}
        </div>
      ) : suppliers.length === 0 ? (
        <div className="text-center py-12 text-gray-400">
          <Truck className="mx-auto mb-3" size={32} />
          <p>No suppliers yet. Add one or import products from AliExpress.</p>
        </div>
      ) : (
        <div className="divide-y border rounded-lg bg-white">
          {suppliers.map((s) => (
            <div key={s.id} className="flex items-center justify-between p-4">
              <div className="flex items-start gap-3">
                <div className="p-2 bg-gray-50 rounded-lg">
                  <Store size={18} className="text-gray-500" />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <p className="font-medium text-gray-800">{s.name}</p>
                    <span className="text-xs px-2 py-0.5 bg-blue-100 text-blue-700 rounded-full">
                      {PLATFORM_LABELS[s.platform] ?? s.platform}
                    </span>
                    {!s.is_active && (
                      <span className="text-xs px-2 py-0.5 bg-red-100 text-red-600 rounded-full">Inactive</span>
                    )}
                  </div>
                  <div className="flex items-center gap-4 mt-1">
                    <RatingStars rating={s.reliability_rating} />
                    {s.avg_shipping_days && (
                      <span className="text-xs text-gray-400">~{s.avg_shipping_days}d ship</span>
                    )}
                    {s.store_url && (
                      <a
                        href={s.store_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-xs text-blue-600 hover:underline flex items-center gap-0.5"
                      >
                        Store <ExternalLink size={10} />
                      </a>
                    )}
                  </div>
                  {s.notes && <p className="text-xs text-gray-400 mt-1 max-w-sm truncate">{s.notes}</p>}
                </div>
              </div>
              <button
                onClick={() => {
                  if (confirm(`Delete supplier "${s.name}"?`)) {
                    deleteSupplier.mutate(s.id);
                  }
                }}
                className="text-xs text-red-500 hover:text-red-700 px-2 py-1 rounded hover:bg-red-50"
              >
                Delete
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ── AliExpress search tab ─────────────────────────────────────────────────────

function ProductCard({
  product,
  onImport,
  importing,
  imported,
}: {
  product: AliExpressProduct;
  onImport: (p: AliExpressProduct) => void;
  importing: boolean;
  imported: boolean;
}) {
  return (
    <div className="bg-white border rounded-lg overflow-hidden flex flex-col">
      {product.image_url ? (
        <img
          src={product.image_url}
          alt={product.title}
          className="w-full h-40 object-cover bg-gray-50"
        />
      ) : (
        <div className="w-full h-40 bg-gray-100 flex items-center justify-center text-gray-300">
          No image
        </div>
      )}
      <div className="p-3 flex flex-col flex-1">
        <p className="text-sm font-medium text-gray-800 line-clamp-2 flex-1 mb-2">{product.title}</p>
        <div className="space-y-1 mb-3">
          <p className="text-lg font-bold text-green-600">${product.sale_price_usd.toFixed(2)}</p>
          {product.store_name && (
            <p className="text-xs text-gray-400 flex items-center gap-1">
              <Store size={10} /> {product.store_name}
            </p>
          )}
          <div className="flex items-center gap-3">
            {product.avg_star_rating != null && (
              <span className="text-xs text-gray-500 flex items-center gap-0.5">
                <Star size={10} className="text-yellow-400 fill-yellow-400" />
                {product.avg_star_rating.toFixed(1)}
              </span>
            )}
            {product.total_orders != null && (
              <span className="text-xs text-gray-500 flex items-center gap-0.5">
                <ShoppingCart size={10} />
                {product.total_orders.toLocaleString()} orders
              </span>
            )}
          </div>
        </div>
        <div className="flex gap-2">
          {product.product_url && (
            <a
              href={product.product_url}
              target="_blank"
              rel="noopener noreferrer"
              className="flex-1 flex items-center justify-center gap-1 border rounded-lg px-2 py-1.5 text-xs hover:bg-gray-50"
            >
              <ExternalLink size={11} /> View
            </a>
          )}
          <button
            onClick={() => onImport(product)}
            disabled={importing || imported}
            className={`flex-1 flex items-center justify-center gap-1 rounded-lg px-2 py-1.5 text-xs font-medium transition-colors ${
              imported
                ? "bg-green-100 text-green-700 cursor-default"
                : "bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50"
            }`}
          >
            {importing ? (
              <><Loader2 size={11} className="animate-spin" /> Importing…</>
            ) : imported ? (
              <><Check size={11} /> Imported</>
            ) : (
              <><Plus size={11} /> Import</>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}

function AliExpressSearchTab() {
  const [query, setQuery] = useState("");
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [importedIds, setImportedIds] = useState<Set<string>>(new Set());

  const { data, isLoading, isFetching, error } = useAliExpressSearch(search, page, 20, !!search);
  const importProduct = useImportProduct();

  const handleSearch = useCallback((e: React.FormEvent) => {
    e.preventDefault();
    setSearch(query.trim());
    setPage(1);
  }, [query]);

  const handleImport = useCallback(async (product: AliExpressProduct) => {
    await importProduct.mutateAsync({
      product_id: product.product_id,
      title: product.title,
      sale_price_usd: product.sale_price_usd,
      image_url: product.image_url,
      product_url: product.product_url,
      store_name: product.store_name,
      store_id: product.store_id,
    });
    setImportedIds((prev) => new Set([...prev, product.product_id]));
  }, [importProduct]);

  const apiNotConfigured =
    error && (error as any)?.response?.status === 502;

  return (
    <div>
      <form onSubmit={handleSearch} className="flex gap-2 mb-6">
        <div className="relative flex-1">
          <Search
            size={16}
            className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400"
          />
          <input
            type="text"
            placeholder="Search AliExpress products…"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="w-full pl-9 pr-4 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
        <button
          type="submit"
          disabled={!query.trim() || isLoading}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700 disabled:opacity-50"
        >
          Search
        </button>
      </form>

      {apiNotConfigured && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 text-sm text-yellow-800 mb-4">
          AliExpress API keys are not configured. Set{" "}
          <code className="font-mono bg-yellow-100 px-1 rounded">ALIEXPRESS_APP_KEY</code> and{" "}
          <code className="font-mono bg-yellow-100 px-1 rounded">ALIEXPRESS_APP_SECRET</code> in your{" "}
          <code className="font-mono bg-yellow-100 px-1 rounded">.env</code> file.
        </div>
      )}

      {isLoading || (isFetching && !data) ? (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
          {[...Array(8)].map((_, i) => (
            <div key={i} className="h-72 bg-gray-100 rounded-lg animate-pulse" />
          ))}
        </div>
      ) : data && data.products.length === 0 ? (
        <p className="text-center py-12 text-gray-400">No results for &ldquo;{search}&rdquo;</p>
      ) : data ? (
        <>
          <p className="text-sm text-gray-500 mb-4">
            {data.total.toLocaleString()} results · page {data.page} of {data.total_pages}
          </p>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
            {data.products.map((p) => (
              <ProductCard
                key={p.product_id}
                product={p}
                onImport={handleImport}
                importing={
                  importProduct.isPending &&
                  importProduct.variables?.product_id === p.product_id
                }
                imported={importedIds.has(p.product_id)}
              />
            ))}
          </div>

          {data.total_pages > 1 && (
            <div className="flex items-center justify-center gap-2 mt-6">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1}
                className="px-3 py-1.5 border rounded-lg text-sm hover:bg-gray-50 disabled:opacity-40"
              >
                Previous
              </button>
              <span className="text-sm text-gray-500">
                {page} / {data.total_pages}
              </span>
              <button
                onClick={() => setPage((p) => Math.min(data.total_pages, p + 1))}
                disabled={page === data.total_pages}
                className="px-3 py-1.5 border rounded-lg text-sm hover:bg-gray-50 disabled:opacity-40"
              >
                Next
              </button>
            </div>
          )}
        </>
      ) : !search ? (
        <div className="text-center py-16 text-gray-400">
          <Search className="mx-auto mb-3" size={32} />
          <p>Search for products to import from AliExpress</p>
        </div>
      ) : null}
    </div>
  );
}

// ── Page ──────────────────────────────────────────────────────────────────────

const TABS = [
  { key: "suppliers", label: "Suppliers" },
  { key: "search", label: "AliExpress Search" },
] as const;
type Tab = (typeof TABS)[number]["key"];

export default function SuppliersPage() {
  const [activeTab, setActiveTab] = useState<Tab>("suppliers");

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">Suppliers</h1>
      </div>

      <div className="flex gap-1 border-b mb-6">
        {TABS.map((t) => (
          <button
            key={t.key}
            onClick={() => setActiveTab(t.key)}
            className={`px-4 py-2 text-sm font-medium border-b-2 -mb-px transition-colors ${
              activeTab === t.key
                ? "border-blue-600 text-blue-600"
                : "border-transparent text-gray-500 hover:text-gray-700"
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {activeTab === "suppliers" ? <SupplierListTab /> : <AliExpressSearchTab />}
    </div>
  );
}
