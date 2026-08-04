"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import { Clock, Play, RefreshCw, CheckCircle, XCircle, Loader2 } from "lucide-react";

interface JobHistory {
  id: string;
  job_type: string;
  status: string;
  started_at: string | null;
  completed_at: string | null;
  items_processed: number;
  items_failed: number;
  result_summary: Record<string, unknown> | null;
  triggered_by: string;
  celery_task_id: string | null;
  created_at: string;
}

const TRIGGERABLE_JOBS = [
  { key: "sync_orders", label: "Sync eBay Orders" },
  { key: "sync_listings", label: "Sync eBay Listings" },
  { key: "refresh_tokens", label: "Refresh eBay Tokens" },
  { key: "reprice_check", label: "Reprice Check" },
  { key: "check_low_stock", label: "Check Low Stock" },
  { key: "check_supplier_prices", label: "Check Supplier Prices" },
  { key: "sync_tracking", label: "Sync AliExpress Tracking" },
  { key: "daily_profitability_recalc", label: "Recalculate Profitability" },
  { key: "generate_daily_summary", label: "Generate Daily Summary" },
];

const STATUS_COLORS: Record<string, string> = {
  PENDING: "bg-gray-100 text-gray-600",
  RUNNING: "bg-blue-100 text-blue-700",
  SUCCESS: "bg-green-100 text-green-700",
  FAILURE: "bg-red-100 text-red-700",
  RETRY: "bg-yellow-100 text-yellow-700",
};

function StatusIcon({ status }: { status: string }) {
  if (status === "SUCCESS") return <CheckCircle size={14} className="text-green-600" />;
  if (status === "FAILURE") return <XCircle size={14} className="text-red-500" />;
  if (status === "RUNNING") return <Loader2 size={14} className="text-blue-600 animate-spin" />;
  return <Clock size={14} className="text-gray-400" />;
}

function useJobs(jobType?: string) {
  return useQuery<{ items: JobHistory[]; total: number }>({
    queryKey: ["jobs", jobType],
    queryFn: async () => {
      const { data } = await apiClient.get("/jobs", {
        params: { page_size: 100, ...(jobType ? { job_type: jobType } : {}) },
      });
      return data;
    },
    refetchInterval: 10_000,
  });
}

function useTriggerJob() {
  const qc = useQueryClient();
  return useMutation<{ task_id: string; job_type: string; status: string }, Error, string>({
    mutationFn: async (job_type) => {
      const { data } = await apiClient.post("/jobs/trigger", { job_type });
      return data;
    },
    onSuccess: () => setTimeout(() => qc.invalidateQueries({ queryKey: ["jobs"] }), 1000),
  });
}

export default function JobsPage() {
  const [typeFilter, setTypeFilter] = useState<string | undefined>(undefined);
  const { data, isLoading, refetch } = useJobs(typeFilter);
  const triggerJob = useTriggerJob();
  const [lastTriggered, setLastTriggered] = useState<string | null>(null);

  const jobs = data?.items ?? [];

  function handleTrigger(jobKey: string) {
    triggerJob.mutate(jobKey, {
      onSuccess: () => {
        setLastTriggered(jobKey);
        setTimeout(() => setLastTriggered(null), 3000);
      },
    });
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">Jobs</h1>
        <button
          onClick={() => refetch()}
          className="inline-flex items-center gap-2 px-3 py-1.5 border rounded-lg text-sm hover:bg-gray-50 text-gray-600"
        >
          <RefreshCw size={14} /> Refresh
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Manual trigger panel */}
        <div className="bg-white rounded-lg border p-4">
          <h2 className="font-semibold text-gray-800 mb-3">Manual Trigger</h2>
          <div className="space-y-2">
            {TRIGGERABLE_JOBS.map(({ key, label }) => (
              <button
                key={key}
                onClick={() => handleTrigger(key)}
                disabled={triggerJob.isPending}
                className="w-full flex items-center justify-between px-3 py-2 border rounded-lg text-sm hover:bg-gray-50 disabled:opacity-50 transition-colors group"
              >
                <span className="text-gray-700">{label}</span>
                {lastTriggered === key ? (
                  <CheckCircle size={14} className="text-green-500" />
                ) : (
                  <Play
                    size={14}
                    className="text-gray-300 group-hover:text-blue-600 transition-colors"
                  />
                )}
              </button>
            ))}
          </div>
        </div>

        {/* Job history */}
        <div className="lg:col-span-2 bg-white rounded-lg border">
          <div className="p-4 border-b flex items-center justify-between">
            <h2 className="font-semibold text-gray-800">History</h2>
            <select
              value={typeFilter ?? ""}
              onChange={(e) => setTypeFilter(e.target.value || undefined)}
              className="border rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All types</option>
              {TRIGGERABLE_JOBS.map(({ key, label }) => (
                <option key={key} value={key}>{label}</option>
              ))}
            </select>
          </div>

          {isLoading ? (
            <div className="p-4 space-y-3">
              {[...Array(5)].map((_, i) => (
                <div key={i} className="h-12 bg-gray-50 rounded animate-pulse" />
              ))}
            </div>
          ) : jobs.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 text-gray-400">
              <Clock size={32} className="mb-2" />
              <p className="text-sm">No job history yet</p>
            </div>
          ) : (
            <div className="divide-y">
              {jobs.map((job) => (
                <div key={job.id} className="flex items-center gap-4 px-4 py-3">
                  <StatusIcon status={job.status} />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-800">
                      {job.job_type.replace(/_/g, " ")}
                    </p>
                    <p className="text-xs text-gray-400">
                      {job.items_processed} processed · {job.items_failed} failed ·{" "}
                      {job.triggered_by}
                    </p>
                  </div>
                  <div className="text-right shrink-0">
                    <span
                      className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                        STATUS_COLORS[job.status] ?? "bg-gray-100 text-gray-600"
                      }`}
                    >
                      {job.status}
                    </span>
                    <p className="text-xs text-gray-400 mt-1">
                      {new Date(job.created_at).toLocaleString()}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
