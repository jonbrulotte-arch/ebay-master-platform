"use client";

import { useState, useEffect } from "react";
import { Link2, Link2Off, CheckCircle, AlertCircle, RefreshCw } from "lucide-react";
import { apiClient } from "@/lib/api-client";

interface ConnectionStatus {
  connected: boolean;
  marketplace: string;
  expires_at?: string;
  scopes: string[];
}

interface Policy {
  fulfillmentPolicyId?: string;
  returnPolicyId?: string;
  paymentPolicyId?: string;
  name: string;
}

export default function SettingsPage() {
  const [status, setStatus] = useState<ConnectionStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [connecting, setConnecting] = useState(false);
  const [disconnecting, setDisconnecting] = useState(false);
  const [fulfillmentPolicies, setFulfillmentPolicies] = useState<Policy[]>([]);
  const [returnPolicies, setReturnPolicies] = useState<Policy[]>([]);
  const [paymentPolicies, setPaymentPolicies] = useState<Policy[]>([]);
  const [policiesLoading, setPoliciesLoading] = useState(false);
  const [policiesError, setPoliciesError] = useState("");

  useEffect(() => {
    fetchStatus();
  }, []);

  async function fetchStatus() {
    setLoading(true);
    try {
      const { data } = await apiClient.get<ConnectionStatus>("/ebay/status");
      setStatus(data);
    } catch {
      setStatus({ connected: false, marketplace: "EBAY_US", scopes: [] });
    } finally {
      setLoading(false);
    }
  }

  async function handleConnect() {
    setConnecting(true);
    try {
      const { data } = await apiClient.get<{ url: string }>("/ebay/connect");
      window.location.href = data.url;
    } catch {
      setConnecting(false);
    }
  }

  async function handleDisconnect() {
    if (!confirm("Disconnect your eBay account? This will stop all syncs.")) return;
    setDisconnecting(true);
    try {
      await apiClient.delete("/ebay/disconnect");
      await fetchStatus();
    } finally {
      setDisconnecting(false);
    }
  }

  async function loadPolicies() {
    setPoliciesLoading(true);
    setPoliciesError("");
    try {
      const [ff, rp, pp] = await Promise.all([
        apiClient.get("/ebay/policies/fulfillment"),
        apiClient.get("/ebay/policies/return"),
        apiClient.get("/ebay/policies/payment"),
      ]);
      setFulfillmentPolicies(ff.data?.fulfillmentPolicies ?? []);
      setReturnPolicies(rp.data?.returnPolicies ?? []);
      setPaymentPolicies(pp.data?.paymentPolicies ?? []);
    } catch {
      setPoliciesError("Failed to load policies. Make sure your eBay account is connected.");
    } finally {
      setPoliciesLoading(false);
    }
  }

  return (
    <div className="max-w-2xl">
      <h1 className="text-2xl font-bold mb-6">Settings</h1>

      {/* eBay Connection */}
      <section className="bg-white rounded-lg border p-6 mb-6">
        <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <img src="https://upload.wikimedia.org/wikipedia/commons/1/1b/EBay_logo.svg" alt="eBay" className="h-5" />
          eBay Account
        </h2>

        {loading ? (
          <div className="flex items-center gap-2 text-gray-400">
            <RefreshCw size={16} className="animate-spin" /> Checking status…
          </div>
        ) : status?.connected ? (
          <div>
            <div className="flex items-center gap-2 mb-4">
              <CheckCircle size={18} className="text-green-500" />
              <span className="font-medium text-green-700">Connected to eBay US</span>
            </div>
            {status.expires_at && (
              <p className="text-sm text-gray-500 mb-4">
                Token expires: {new Date(status.expires_at).toLocaleString()}
              </p>
            )}
            {status.scopes.length > 0 && (
              <details className="mb-4">
                <summary className="text-sm text-gray-500 cursor-pointer">
                  {status.scopes.length} active scopes
                </summary>
                <ul className="mt-2 space-y-1">
                  {status.scopes.map((s) => (
                    <li key={s} className="text-xs text-gray-400 font-mono">{s}</li>
                  ))}
                </ul>
              </details>
            )}
            <div className="flex gap-3">
              <button
                onClick={handleDisconnect}
                disabled={disconnecting}
                className="inline-flex items-center gap-2 px-4 py-2 border border-red-200 text-red-600 rounded-lg text-sm hover:bg-red-50 disabled:opacity-50"
              >
                <Link2Off size={16} />
                {disconnecting ? "Disconnecting…" : "Disconnect"}
              </button>
              <button
                onClick={handleConnect}
                disabled={connecting}
                className="inline-flex items-center gap-2 px-4 py-2 border rounded-lg text-sm hover:bg-gray-50 disabled:opacity-50"
              >
                <RefreshCw size={16} />
                Reconnect
              </button>
            </div>
          </div>
        ) : (
          <div>
            <div className="flex items-center gap-2 mb-4">
              <AlertCircle size={18} className="text-gray-400" />
              <span className="text-gray-600">Not connected</span>
            </div>
            <p className="text-sm text-gray-500 mb-4">
              Connect your eBay seller account to enable listing management, order sync, and repricing.
            </p>
            <button
              onClick={handleConnect}
              disabled={connecting}
              className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50"
            >
              <Link2 size={16} />
              {connecting ? "Redirecting to eBay…" : "Connect eBay Account"}
            </button>
          </div>
        )}
      </section>

      {/* Seller Policies */}
      {status?.connected && (
        <section className="bg-white rounded-lg border p-6 mb-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold">Seller Policies</h2>
            <button
              onClick={loadPolicies}
              disabled={policiesLoading}
              className="inline-flex items-center gap-2 px-3 py-1.5 border rounded-lg text-sm hover:bg-gray-50 disabled:opacity-50"
            >
              <RefreshCw size={14} className={policiesLoading ? "animate-spin" : ""} />
              Load Policies
            </button>
          </div>

          {policiesError && (
            <p className="text-sm text-red-500 mb-4">{policiesError}</p>
          )}

          {fulfillmentPolicies.length > 0 && (
            <PolicySection title="Fulfillment (Shipping)" policies={fulfillmentPolicies} nameKey="fulfillmentPolicyId" />
          )}
          {returnPolicies.length > 0 && (
            <PolicySection title="Return" policies={returnPolicies} nameKey="returnPolicyId" />
          )}
          {paymentPolicies.length > 0 && (
            <PolicySection title="Payment" policies={paymentPolicies} nameKey="paymentPolicyId" />
          )}

          {!policiesLoading && fulfillmentPolicies.length === 0 && returnPolicies.length === 0 && paymentPolicies.length === 0 && (
            <p className="text-sm text-gray-400">Click &quot;Load Policies&quot; to view your eBay seller policies.</p>
          )}
        </section>
      )}
    </div>
  );
}

function PolicySection({ title, policies, nameKey }: { title: string; policies: any[]; nameKey: string }) {
  return (
    <div className="mb-4">
      <h3 className="text-sm font-medium text-gray-700 mb-2">{title}</h3>
      <ul className="space-y-1">
        {policies.map((p, i) => (
          <li key={i} className="text-sm text-gray-600 flex items-center justify-between py-1.5 border-b last:border-0">
            <span>{p.name}</span>
            <span className="text-xs text-gray-400 font-mono">{p[nameKey]}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
