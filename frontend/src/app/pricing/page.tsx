"use client";

import { useState } from "react";
import {
  useFeeCalculator,
  useFeeCategories,
  usePricingRules,
  useCreatePricingRule,
  useUpdatePricingRule,
  useDeletePricingRule,
  usePriceChangeLog,
  useUserSettings,
  type FeeCalculationResponse,
} from "@/hooks/usePricing";
import { Calculator, List, History, Pencil, Trash2, Plus, CheckCircle, XCircle } from "lucide-react";

const STORE_LEVELS = [
  { value: "none", label: "No Store" },
  { value: "starter", label: "Starter" },
  { value: "basic", label: "Basic" },
  { value: "premium", label: "Premium" },
  { value: "anchor", label: "Anchor" },
  { value: "enterprise", label: "Enterprise" },
];

function fmt(n: number) {
  return n.toLocaleString("en-US", { style: "currency", currency: "USD" });
}

function pct(n: number, decimals = 2) {
  return `${n.toFixed(decimals)}%`;
}

// ── Fee Calculator Tab ─────────────────────────────────────────────────────────

function FeeCalculatorTab() {
  const { data: settings } = useUserSettings();
  const { data: categories = [] } = useFeeCategories();
  const calc = useFeeCalculator();

  const [form, setForm] = useState({
    sold_price: "",
    item_cost: "",
    actual_shipping_cost: "",
    shipping_charge_to_buyer: "",
    seller_discount_pct: "",
    promoted_rate: "",
    sales_tax_rate: "",
    store_level: settings?.ebay_store_level ?? "basic",
    category_name: settings?.default_fee_category ?? "All Other Categories",
    is_top_rated_seller: settings?.is_top_rated_seller ?? false,
  });

  const [result, setResult] = useState<FeeCalculationResponse | null>(null);

  function set(field: string, value: string | boolean) {
    setForm((f) => ({ ...f, [field]: value }));
  }

  async function handleCalculate() {
    const payload = {
      sold_price: parseFloat(form.sold_price) || 0,
      item_cost: parseFloat(form.item_cost) || 0,
      actual_shipping_cost: parseFloat(form.actual_shipping_cost) || 0,
      shipping_charge_to_buyer: parseFloat(form.shipping_charge_to_buyer) || 0,
      seller_discount_pct: parseFloat(form.seller_discount_pct) || 0,
      promoted_rate: parseFloat(form.promoted_rate) || 0,
      sales_tax_rate: parseFloat(form.sales_tax_rate) || 0,
      store_level: form.store_level,
      category_name: form.category_name,
      is_top_rated_seller: form.is_top_rated_seller,
    };
    const data = await calc.mutateAsync(payload);
    setResult(data);
  }

  const profitColor = result
    ? result.net_profit >= 0
      ? "text-green-600"
      : "text-red-600"
    : "";

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* Inputs */}
      <div className="bg-white rounded-lg border p-6">
        <h2 className="font-semibold text-gray-800 mb-4">Sale Details</h2>
        <div className="space-y-3">
          <Field label="Sold Price ($)" value={form.sold_price} onChange={(v) => set("sold_price", v)} placeholder="29.99" />
          <Field label="Item Cost ($)" value={form.item_cost} onChange={(v) => set("item_cost", v)} placeholder="5.00" />
          <Field label="Actual Shipping Cost ($)" value={form.actual_shipping_cost} onChange={(v) => set("actual_shipping_cost", v)} placeholder="4.99" />
          <Field label="Shipping Charged to Buyer ($)" value={form.shipping_charge_to_buyer} onChange={(v) => set("shipping_charge_to_buyer", v)} placeholder="0.00" />
          <Field label="Seller Discount (%)" value={form.seller_discount_pct} onChange={(v) => set("seller_discount_pct", v)} placeholder="0" />
          <Field label="Promoted Listing Rate (%)" value={form.promoted_rate} onChange={(v) => set("promoted_rate", v)} placeholder="0" />
          <Field label="Sales Tax Rate (%)" value={form.sales_tax_rate} onChange={(v) => set("sales_tax_rate", v)} placeholder="0" />

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Store Level</label>
            <select
              value={form.store_level}
              onChange={(e) => set("store_level", e.target.value)}
              className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {STORE_LEVELS.map((s) => (
                <option key={s.value} value={s.value}>{s.label}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Category</label>
            <select
              value={form.category_name}
              onChange={(e) => set("category_name", e.target.value)}
              className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {categories.map((c) => (
                <option key={c} value={c}>{c}</option>
              ))}
            </select>
          </div>

          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={form.is_top_rated_seller}
              onChange={(e) => set("is_top_rated_seller", e.target.checked)}
              className="w-4 h-4 rounded border-gray-300"
            />
            <span className="text-sm font-medium text-gray-700">Top Rated Seller (10% FVF discount)</span>
          </label>
        </div>

        <button
          onClick={handleCalculate}
          disabled={calc.isPending || !form.sold_price}
          className="mt-5 w-full py-2.5 bg-blue-600 text-white rounded-lg font-medium text-sm hover:bg-blue-700 disabled:opacity-50 transition-colors"
        >
          {calc.isPending ? "Calculating…" : "Calculate"}
        </button>
      </div>

      {/* Results */}
      <div className="bg-white rounded-lg border p-6">
        <h2 className="font-semibold text-gray-800 mb-4">Results</h2>
        {result ? (
          <div className="space-y-3">
            {/* Primary KPIs */}
            <div className="grid grid-cols-3 gap-3 mb-4">
              <KpiCard label="Net Profit" value={fmt(result.net_profit)} color={profitColor} />
              <KpiCard label="Margin" value={pct(result.profit_margin_pct)} color={profitColor} />
              <KpiCard label="ROI" value={pct(result.roi_pct)} color={profitColor} />
            </div>

            <Divider />
            <Row label="Sold Price" value={fmt(result.sold_price)} />
            {result.seller_discount_amount > 0 && (
              <Row label="Seller Discount" value={`− ${fmt(result.seller_discount_amount)}`} muted />
            )}
            <Row label="Effective Price" value={fmt(result.effective_sold_price)} />
            {result.shipping_charge_to_buyer > 0 && (
              <Row label="Shipping to Buyer" value={`+ ${fmt(result.shipping_charge_to_buyer)}`} />
            )}
            <Row label="Pre-Tax Total" value={fmt(result.pre_tax_total)} bold />
            {result.sales_tax_amount > 0 && (
              <Row label="Sales Tax (remitted)" value={fmt(result.sales_tax_amount)} muted />
            )}
            <Row label="Total Sale (FVF basis)" value={fmt(result.total_sale)} />

            <Divider />
            <Row label="Final Value Fee" value={`− ${fmt(result.final_value_fee)}`} red />
            {result.promoted_fee > 0 && (
              <Row label="Promoted Listing Fee" value={`− ${fmt(result.promoted_fee)}`} red />
            )}
            <Row label="Total eBay Fees" value={`− ${fmt(result.total_fees)}`} red bold />

            <Divider />
            <Row label="Payout (pre-tax − fees)" value={fmt(result.payout)} bold />
            <Row label="Item Cost" value={`− ${fmt(result.item_cost)}`} red />
            {result.actual_shipping_cost > 0 && (
              <Row label="Shipping Cost (supplier)" value={`− ${fmt(result.actual_shipping_cost)}`} red />
            )}

            <Divider />
            <Row label="Net Profit" value={fmt(result.net_profit)} bold color={profitColor} />
          </div>
        ) : (
          <div className="h-48 flex items-center justify-center text-gray-400 text-sm">
            Enter values and click Calculate
          </div>
        )}
      </div>
    </div>
  );
}

function Field({
  label,
  value,
  onChange,
  placeholder,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
}) {
  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-1">{label}</label>
      <input
        type="number"
        step="0.01"
        min="0"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
      />
    </div>
  );
}

function KpiCard({ label, value, color }: { label: string; value: string; color?: string }) {
  return (
    <div className="bg-gray-50 rounded-lg p-3 text-center">
      <p className="text-xs text-gray-500 mb-1">{label}</p>
      <p className={`text-lg font-bold ${color ?? "text-gray-900"}`}>{value}</p>
    </div>
  );
}

function Divider() {
  return <hr className="border-gray-100" />;
}

function Row({
  label,
  value,
  muted,
  bold,
  red,
  color,
}: {
  label: string;
  value: string;
  muted?: boolean;
  bold?: boolean;
  red?: boolean;
  color?: string;
}) {
  const textColor = color ?? (red ? "text-red-600" : muted ? "text-gray-400" : "text-gray-700");
  return (
    <div className="flex justify-between text-sm">
      <span className={muted ? "text-gray-400" : "text-gray-600"}>{label}</span>
      <span className={`${textColor} ${bold ? "font-semibold" : ""}`}>{value}</span>
    </div>
  );
}

// ── Pricing Rules Tab ──────────────────────────────────────────────────────────

function PricingRulesTab() {
  const { data: rules = [], isLoading } = usePricingRules();
  const createRule = useCreatePricingRule();
  const updateRule = useUpdatePricingRule();
  const deleteRule = useDeletePricingRule();

  const [showForm, setShowForm] = useState(false);
  const [editId, setEditId] = useState<string | null>(null);
  const [form, setForm] = useState({
    name: "",
    min_margin_pct: "",
    target_margin_pct: "",
    min_price: "",
    max_price: "",
    priority: "0",
  });

  function openCreate() {
    setEditId(null);
    setForm({ name: "", min_margin_pct: "", target_margin_pct: "", min_price: "", max_price: "", priority: "0" });
    setShowForm(true);
  }

  function openEdit(rule: (typeof rules)[0]) {
    setEditId(rule.id);
    setForm({
      name: rule.name,
      min_margin_pct: rule.min_margin_pct?.toString() ?? "",
      target_margin_pct: rule.target_margin_pct?.toString() ?? "",
      min_price: rule.min_price?.toString() ?? "",
      max_price: rule.max_price?.toString() ?? "",
      priority: rule.priority.toString(),
    });
    setShowForm(true);
  }

  async function handleSave() {
    const payload = {
      name: form.name,
      rule_type: "MIN_MARGIN",
      reprice_strategy: "TARGET_MARGIN",
      min_margin_pct: form.min_margin_pct ? parseFloat(form.min_margin_pct) : null,
      target_margin_pct: form.target_margin_pct ? parseFloat(form.target_margin_pct) : null,
      min_price: form.min_price ? parseFloat(form.min_price) : null,
      max_price: form.max_price ? parseFloat(form.max_price) : null,
      priority: parseInt(form.priority) || 0,
    };
    if (editId) {
      await updateRule.mutateAsync({ id: editId, updates: payload });
    } else {
      await createRule.mutateAsync(payload);
    }
    setShowForm(false);
  }

  async function handleDelete(id: string) {
    if (!confirm("Delete this pricing rule?")) return;
    await deleteRule.mutateAsync(id);
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <p className="text-sm text-gray-500">
          Rules are evaluated every hour. The highest-priority active rule for each product is applied.
        </p>
        <button
          onClick={openCreate}
          className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700"
        >
          <Plus size={16} /> New Rule
        </button>
      </div>

      {showForm && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
          <h3 className="font-medium text-gray-800 mb-3">{editId ? "Edit Rule" : "New Rule"}</h3>
          <div className="grid grid-cols-2 gap-3">
            <div className="col-span-2">
              <label className="block text-xs font-medium text-gray-600 mb-1">Rule Name</label>
              <input
                value={form.name}
                onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
                className="w-full border rounded-lg px-3 py-2 text-sm"
                placeholder="e.g. Electronics Min Margin"
              />
            </div>
            <RuleField label="Min Margin %" value={form.min_margin_pct} onChange={(v) => setForm((f) => ({ ...f, min_margin_pct: v }))} placeholder="20" />
            <RuleField label="Target Margin %" value={form.target_margin_pct} onChange={(v) => setForm((f) => ({ ...f, target_margin_pct: v }))} placeholder="30" />
            <RuleField label="Price Floor ($)" value={form.min_price} onChange={(v) => setForm((f) => ({ ...f, min_price: v }))} placeholder="Optional" />
            <RuleField label="Price Ceiling ($)" value={form.max_price} onChange={(v) => setForm((f) => ({ ...f, max_price: v }))} placeholder="Optional" />
            <RuleField label="Priority" value={form.priority} onChange={(v) => setForm((f) => ({ ...f, priority: v }))} placeholder="0" />
          </div>
          <div className="flex gap-2 mt-3">
            <button
              onClick={handleSave}
              disabled={createRule.isPending || updateRule.isPending || !form.name}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50"
            >
              Save Rule
            </button>
            <button onClick={() => setShowForm(false)} className="px-4 py-2 border rounded-lg text-sm hover:bg-gray-50">
              Cancel
            </button>
          </div>
        </div>
      )}

      {isLoading ? (
        <div className="text-gray-400 text-sm p-4">Loading rules…</div>
      ) : rules.length === 0 ? (
        <div className="text-gray-400 text-sm bg-white rounded-lg border p-8 text-center">
          No pricing rules yet. Create one to enable auto-repricing.
        </div>
      ) : (
        <div className="bg-white rounded-lg border overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b">
              <tr>
                <th className="px-4 py-3 text-left font-medium text-gray-600">Name</th>
                <th className="px-4 py-3 text-right font-medium text-gray-600">Min Margin</th>
                <th className="px-4 py-3 text-right font-medium text-gray-600">Target Margin</th>
                <th className="px-4 py-3 text-right font-medium text-gray-600">Floor</th>
                <th className="px-4 py-3 text-right font-medium text-gray-600">Ceiling</th>
                <th className="px-4 py-3 text-center font-medium text-gray-600">Active</th>
                <th className="px-4 py-3 text-right font-medium text-gray-600">Priority</th>
                <th className="px-4 py-3"></th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {rules.map((rule) => (
                <tr key={rule.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 font-medium text-gray-800">{rule.name}</td>
                  <td className="px-4 py-3 text-right text-gray-600">
                    {rule.min_margin_pct != null ? pct(rule.min_margin_pct) : "—"}
                  </td>
                  <td className="px-4 py-3 text-right text-gray-600">
                    {rule.target_margin_pct != null ? pct(rule.target_margin_pct) : "—"}
                  </td>
                  <td className="px-4 py-3 text-right text-gray-600">
                    {rule.min_price != null ? fmt(rule.min_price) : "—"}
                  </td>
                  <td className="px-4 py-3 text-right text-gray-600">
                    {rule.max_price != null ? fmt(rule.max_price) : "—"}
                  </td>
                  <td className="px-4 py-3 text-center">
                    {rule.is_active ? (
                      <CheckCircle size={16} className="text-green-500 inline" />
                    ) : (
                      <XCircle size={16} className="text-gray-300 inline" />
                    )}
                  </td>
                  <td className="px-4 py-3 text-right text-gray-500">{rule.priority}</td>
                  <td className="px-4 py-3 text-right">
                    <div className="flex items-center justify-end gap-2">
                      <button onClick={() => openEdit(rule)} className="text-gray-400 hover:text-blue-600">
                        <Pencil size={15} />
                      </button>
                      <button onClick={() => handleDelete(rule.id)} className="text-gray-400 hover:text-red-600">
                        <Trash2 size={15} />
                      </button>
                    </div>
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

function RuleField({
  label,
  value,
  onChange,
  placeholder,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
}) {
  return (
    <div>
      <label className="block text-xs font-medium text-gray-600 mb-1">{label}</label>
      <input
        type="number"
        step="0.01"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="w-full border rounded-lg px-3 py-2 text-sm"
      />
    </div>
  );
}

// ── Price Change Log Tab ───────────────────────────────────────────────────────

function PriceChangeLogTab() {
  const [page, setPage] = useState(1);
  const { data, isLoading } = usePriceChangeLog(page);

  const logs = data?.items ?? [];
  const totalPages = data?.total_pages ?? 1;

  return (
    <div>
      {isLoading ? (
        <div className="text-gray-400 text-sm p-4">Loading…</div>
      ) : logs.length === 0 ? (
        <div className="text-gray-400 text-sm bg-white rounded-lg border p-8 text-center">
          No price changes recorded yet.
        </div>
      ) : (
        <>
          <div className="bg-white rounded-lg border overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 border-b">
                <tr>
                  <th className="px-4 py-3 text-left font-medium text-gray-600">Date</th>
                  <th className="px-4 py-3 text-right font-medium text-gray-600">Old Price</th>
                  <th className="px-4 py-3 text-right font-medium text-gray-600">New Price</th>
                  <th className="px-4 py-3 text-left font-medium text-gray-600">Reason</th>
                  <th className="px-4 py-3 text-left font-medium text-gray-600">Detail</th>
                  <th className="px-4 py-3 text-center font-medium text-gray-600">eBay</th>
                  <th className="px-4 py-3 text-left font-medium text-gray-600">Triggered By</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {logs.map((log) => (
                  <tr key={log.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 text-gray-500 whitespace-nowrap">
                      {new Date(log.created_at).toLocaleString()}
                    </td>
                    <td className="px-4 py-3 text-right text-gray-600">{fmt(log.old_price)}</td>
                    <td className="px-4 py-3 text-right font-medium text-gray-800">{fmt(log.new_price)}</td>
                    <td className="px-4 py-3 text-gray-600">{log.reason}</td>
                    <td className="px-4 py-3 text-gray-400 text-xs">{log.reason_detail ?? "—"}</td>
                    <td className="px-4 py-3 text-center">
                      {log.applied_to_ebay ? (
                        <CheckCircle size={15} className="text-green-500 inline" title="Applied to eBay" />
                      ) : (
                        <XCircle size={15} className="text-red-400 inline" title={log.ebay_update_error ?? "Not applied"} />
                      )}
                    </td>
                    <td className="px-4 py-3 text-gray-500 text-xs">{log.triggered_by}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {totalPages > 1 && (
            <div className="flex items-center justify-between mt-4 text-sm text-gray-500">
              <span>Page {page} of {totalPages}</span>
              <div className="flex gap-2">
                <button
                  disabled={page === 1}
                  onClick={() => setPage((p) => p - 1)}
                  className="px-3 py-1.5 border rounded-lg hover:bg-gray-50 disabled:opacity-40"
                >
                  Previous
                </button>
                <button
                  disabled={page === totalPages}
                  onClick={() => setPage((p) => p + 1)}
                  className="px-3 py-1.5 border rounded-lg hover:bg-gray-50 disabled:opacity-40"
                >
                  Next
                </button>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}

// ── Page ───────────────────────────────────────────────────────────────────────

const TABS = [
  { id: "calculator", label: "Fee Calculator", icon: Calculator },
  { id: "rules", label: "Pricing Rules", icon: List },
  { id: "log", label: "Price Change Log", icon: History },
] as const;

type TabId = (typeof TABS)[number]["id"];

export default function PricingPage() {
  const [activeTab, setActiveTab] = useState<TabId>("calculator");

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Pricing & Profitability</h1>

      <div className="flex gap-1 border-b mb-6">
        {TABS.map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            onClick={() => setActiveTab(id)}
            className={`inline-flex items-center gap-2 px-4 py-2.5 text-sm font-medium border-b-2 transition-colors ${
              activeTab === id
                ? "border-blue-600 text-blue-600"
                : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
            }`}
          >
            <Icon size={16} />
            {label}
          </button>
        ))}
      </div>

      {activeTab === "calculator" && <FeeCalculatorTab />}
      {activeTab === "rules" && <PricingRulesTab />}
      {activeTab === "log" && <PriceChangeLogTab />}
    </div>
  );
}
