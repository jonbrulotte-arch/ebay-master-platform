"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import { RefreshCw, RotateCcw } from "lucide-react";

interface Return {
  id: string;
  order_id: string;
  ebay_return_id: string | null;
  reason: string | null;
  buyer_comments: string | null;
  status: string;
  refund_amount: number | null;
  return_shipping_paid_by: string;
  return_tracking_number: string | null;
  created_at: string;
  updated_at: string;
}

const STATUS_COLORS: Record<string, string> = {
  REQUESTED: "bg-yellow-100 text-yellow-700",
  APPROVED: "bg-blue-100 text-blue-700",
  REFUNDED: "bg-green-100 text-green-700",
  CLOSED: "bg-gray-100 text-gray-600",
  DENIED: "bg-red-100 text-red-700",
};

function useReturns(status?: string) {
  return useQuery<{ items: Return[]; total: number }>({
    queryKey: ["returns", status],
    queryFn: async () => {
      const { data } = await apiClient.get("/returns", {
        params: status ? { status } : {},
      });
      return data;
    },
  });
}

function useUpdateReturn() {
  const qc = useQueryClient();
  return useMutation<Return, Error, { id: string; status?: string; refund_amount?: number; return_tracking_number?: string }>({
    mutationFn: async ({ id, ...body }) => {
      const { data } = await apiClient.patch(`/returns/${id}`, body);
      return data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["returns"] }),
  });
}

function fmt(n: number) {
  return n.toLocaleString("en-US", { style: "currency", currency: "USD" });
}

function UpdateModal({
  ret,
  onClose,
}: {
  ret: Return;
  onClose: () => void;
}) {
  const update = useUpdateReturn();
  const [form, setForm] = useState({
    status: ret.status,
    refund_amount: ret.refund_amount ?? "",
    return_tracking_number: ret.return_tracking_number ?? "",
  });

  function submit(e: React.FormEvent) {
    e.preventDefault();
    update.mutate(
      {
        id: ret.id,
        status: form.status,
        refund_amount: form.refund_amount !== "" ? Number(form.refund_amount) : undefined,
        return_tracking_number: form.return_tracking_number || undefined,
      },
      { onSuccess: onClose }
    );
  }

  return (
    <div className="fixed inset-0 bg-black/40 z-50 flex items-center justify-center">
      <div className="bg-white rounded-xl shadow-xl p-6 w-full max-w-sm">
        <h2 className="font-semibold text-gray-800 mb-4">Update Return</h2>
        <form onSubmit={submit} className="space-y-3">
          <div>
            <label className="text-sm text-gray-600 block mb-1">Status</label>
            <select
              value={form.status}
              onChange={(e) => setForm((f) => ({ ...f, status: e.target.value }))}
              className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {["REQUESTED", "APPROVED", "REFUNDED", "CLOSED", "DENIED"].map((s) => (
                <option key={s} value={s}>{s}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="text-sm text-gray-600 block mb-1">Refund Amount ($)</label>
            <input
              type="number"
              step="0.01"
              min="0"
              value={form.refund_amount}
              onChange={(e) => setForm((f) => ({ ...f, refund_amount: e.target.value }))}
              className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="text-sm text-gray-600 block mb-1">Return Tracking #</label>
            <input
              value={form.return_tracking_number}
              onChange={(e) => setForm((f) => ({ ...f, return_tracking_number: e.target.value }))}
              className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
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
              disabled={update.isPending}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700 disabled:opacity-50"
            >
              {update.isPending ? "Saving…" : "Save"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default function ReturnsPage() {
  const [statusFilter, setStatusFilter] = useState<string | undefined>(undefined);
  const [editing, setEditing] = useState<Return | null>(null);
  const { data, isLoading, refetch } = useReturns(statusFilter);

  const returns = data?.items ?? [];

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">Returns</h1>
        <button
          onClick={() => refetch()}
          className="inline-flex items-center gap-2 px-3 py-1.5 border rounded-lg text-sm hover:bg-gray-50 text-gray-600"
        >
          <RefreshCw size={14} /> Refresh
        </button>
      </div>

      {editing && <UpdateModal ret={editing} onClose={() => setEditing(null)} />}

      {/* Status filter */}
      <div className="flex flex-wrap gap-1 mb-4">
        {[undefined, "REQUESTED", "APPROVED", "REFUNDED", "CLOSED", "DENIED"].map((s) => (
          <button
            key={String(s)}
            onClick={() => setStatusFilter(s)}
            className={`px-3 py-1 rounded-lg text-sm ${
              statusFilter === s
                ? "bg-blue-600 text-white"
                : "border hover:bg-gray-50 text-gray-600"
            }`}
          >
            {s ?? "All"}
          </button>
        ))}
      </div>

      {isLoading ? (
        <div className="space-y-3">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="h-16 bg-gray-50 rounded-lg animate-pulse" />
          ))}
        </div>
      ) : returns.length === 0 ? (
        <div className="text-center py-16 bg-white rounded-lg border text-gray-400">
          <RotateCcw className="mx-auto mb-3" size={32} />
          <p>No returns {statusFilter ? `with status "${statusFilter}"` : "yet"}.</p>
        </div>
      ) : (
        <div className="bg-white rounded-lg border overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b">
              <tr>
                <th className="px-4 py-3 text-left font-medium text-gray-500">eBay Return ID</th>
                <th className="px-4 py-3 text-left font-medium text-gray-500">Reason</th>
                <th className="px-4 py-3 text-left font-medium text-gray-500">Status</th>
                <th className="px-4 py-3 text-right font-medium text-gray-500">Refund</th>
                <th className="px-4 py-3 text-left font-medium text-gray-500">Tracking</th>
                <th className="px-4 py-3 text-left font-medium text-gray-500">Created</th>
                <th className="px-4 py-3" />
              </tr>
            </thead>
            <tbody className="divide-y">
              {returns.map((r) => (
                <tr key={r.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 font-mono text-xs text-gray-700">
                    {r.ebay_return_id || r.id.slice(0, 8)}
                  </td>
                  <td className="px-4 py-3 text-gray-600 max-w-xs truncate">
                    {r.reason || "—"}
                  </td>
                  <td className="px-4 py-3">
                    <span
                      className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                        STATUS_COLORS[r.status] ?? "bg-gray-100 text-gray-600"
                      }`}
                    >
                      {r.status}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right text-gray-800">
                    {r.refund_amount != null ? fmt(r.refund_amount) : "—"}
                  </td>
                  <td className="px-4 py-3 font-mono text-xs text-gray-500">
                    {r.return_tracking_number || "—"}
                  </td>
                  <td className="px-4 py-3 text-xs text-gray-400">
                    {new Date(r.created_at).toLocaleDateString()}
                  </td>
                  <td className="px-4 py-3">
                    <button
                      onClick={() => setEditing(r)}
                      className="text-xs text-blue-600 hover:underline"
                    >
                      Update
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
