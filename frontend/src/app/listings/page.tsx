"use client";

import { useState } from "react";
import { RefreshCw, Plus, Zap, Square, AlertCircle } from "lucide-react";
import { useListings, usePublishListing, useEndListing, useSyncListings } from "@/hooks/useListings";
import type { Listing, ListingStatus } from "@/types/listing";
import { LISTING_STATUS_COLORS } from "@/types/listing";

function formatCurrency(amount: number) {
  return new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" }).format(amount);
}

function formatDate(iso?: string) {
  if (!iso) return "—";
  return new Date(iso).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
}

function StatusBadge({ status }: { status: ListingStatus }) {
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${LISTING_STATUS_COLORS[status] ?? "bg-gray-100 text-gray-600"}`}>
      {status}
    </span>
  );
}

export default function ListingsPage() {
  const [page, setPage] = useState(1);
  const [statusFilter, setStatusFilter] = useState<string>("");
  const pageSize = 25;

  const { data, isLoading } = useListings({ page, page_size: pageSize, status: statusFilter || undefined });
  const publishMutation = usePublishListing();
  const endMutation = useEndListing();
  const syncMutation = useSyncListings();

  const listings: Listing[] = data?.items ?? [];
  const total = data?.total ?? 0;
  const totalPages = Math.ceil(total / pageSize);

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold">Listings</h1>
          <p className="text-sm text-gray-500 mt-1">{total.toLocaleString()} total listings</p>
        </div>
        <div className="flex gap-3">
          <button
            onClick={() => syncMutation.mutate()}
            disabled={syncMutation.isPending}
            className="inline-flex items-center gap-2 px-4 py-2 border rounded-lg text-sm font-medium hover:bg-gray-50 disabled:opacity-50"
          >
            <RefreshCw size={16} className={syncMutation.isPending ? "animate-spin" : ""} />
            Sync Status
          </button>
          <a
            href="/products"
            className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700"
          >
            <Plus size={16} />
            New Listing
          </a>
        </div>
      </div>

      {/* Filters */}
      <div className="mb-4">
        <select
          value={statusFilter}
          onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }}
          className="border rounded-lg px-3 py-2 text-sm"
        >
          <option value="">All statuses</option>
          <option value="DRAFT">Draft</option>
          <option value="ACTIVE">Active</option>
          <option value="ENDED">Ended</option>
          <option value="ERROR">Error</option>
        </select>
      </div>

      <div className="bg-white rounded-lg border overflow-hidden">
        {isLoading ? (
          <div className="p-12 text-center text-gray-400">
            <RefreshCw size={24} className="animate-spin mx-auto mb-2" />
            Loading listings…
          </div>
        ) : listings.length === 0 ? (
          <div className="p-12 text-center">
            <Plus size={40} className="mx-auto mb-3 text-gray-300" />
            <p className="text-gray-500 text-sm">
              No listings yet. Go to Products and create a listing from a product.
            </p>
          </div>
        ) : (
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b">
              <tr>
                <th className="px-4 py-3 text-left font-medium text-gray-600">Title</th>
                <th className="px-4 py-3 text-left font-medium text-gray-600">Status</th>
                <th className="px-4 py-3 text-right font-medium text-gray-600">Price</th>
                <th className="px-4 py-3 text-right font-medium text-gray-600">Qty</th>
                <th className="px-4 py-3 text-right font-medium text-gray-600">Sold</th>
                <th className="px-4 py-3 text-left font-medium text-gray-600">eBay ID</th>
                <th className="px-4 py-3 text-left font-medium text-gray-600">Last Sync</th>
                <th className="px-4 py-3 text-left font-medium text-gray-600">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {listings.map((listing) => (
                <tr key={listing.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 max-w-xs">
                    <span className="truncate block font-medium" title={listing.title}>
                      {listing.title}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-1">
                      <StatusBadge status={listing.status} />
                      {listing.status === "ERROR" && listing.error_messages?.error && (
                        <span title={listing.error_messages.error}>
                          <AlertCircle size={14} className="text-orange-500" />
                        </span>
                      )}
                    </div>
                  </td>
                  <td className="px-4 py-3 text-right font-medium">
                    {formatCurrency(listing.price)}
                  </td>
                  <td className="px-4 py-3 text-right">{listing.quantity_listed}</td>
                  <td className="px-4 py-3 text-right">{listing.quantity_sold}</td>
                  <td className="px-4 py-3 text-gray-500 text-xs">
                    {listing.ebay_item_id ? (
                      <a
                        href={`https://www.ebay.com/itm/${listing.ebay_item_id}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-blue-600 hover:underline"
                      >
                        {listing.ebay_item_id}
                      </a>
                    ) : "—"}
                  </td>
                  <td className="px-4 py-3 text-gray-400 text-xs">
                    {formatDate(listing.last_synced_at)}
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex gap-2">
                      {(listing.status === "DRAFT" || listing.status === "ERROR") && (
                        <button
                          onClick={() => publishMutation.mutate(listing.id)}
                          disabled={publishMutation.isPending}
                          title="Publish to eBay"
                          className="inline-flex items-center gap-1 px-2 py-1 bg-green-50 text-green-700 border border-green-200 rounded text-xs hover:bg-green-100 disabled:opacity-50"
                        >
                          <Zap size={12} />
                          Publish
                        </button>
                      )}
                      {listing.status === "ACTIVE" && (
                        <button
                          onClick={() => endMutation.mutate(listing.id)}
                          disabled={endMutation.isPending}
                          title="End listing on eBay"
                          className="inline-flex items-center gap-1 px-2 py-1 bg-red-50 text-red-700 border border-red-200 rounded text-xs hover:bg-red-100 disabled:opacity-50"
                        >
                          <Square size={12} />
                          End
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}

        {totalPages > 1 && (
          <div className="px-4 py-3 border-t flex items-center justify-between text-sm text-gray-600">
            <span>Page {page} of {totalPages}</span>
            <div className="flex gap-2">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1}
                className="px-3 py-1 border rounded hover:bg-gray-50 disabled:opacity-40"
              >
                Previous
              </button>
              <button
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                disabled={page === totalPages}
                className="px-3 py-1 border rounded hover:bg-gray-50 disabled:opacity-40"
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
