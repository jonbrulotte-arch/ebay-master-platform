export default function DashboardPage() {
  return (
    <div>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <KPICard title="Today's Revenue" value="$0.00" change="" />
        <KPICard title="Orders Today" value="0" change="" />
        <KPICard title="Active Listings" value="0" change="" />
        <KPICard title="Avg Margin" value="0%" change="" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-lg border p-6">
          <h3 className="text-sm font-medium text-gray-500 mb-4">
            Recent Orders
          </h3>
          <p className="text-gray-400 text-sm">
            No orders yet. Connect your eBay account to start syncing.
          </p>
        </div>
        <div className="bg-white rounded-lg border p-6">
          <h3 className="text-sm font-medium text-gray-500 mb-4">
            Alerts
          </h3>
          <p className="text-gray-400 text-sm">No alerts.</p>
        </div>
      </div>
    </div>
  );
}

function KPICard({
  title,
  value,
  change,
}: {
  title: string;
  value: string;
  change: string;
}) {
  return (
    <div className="bg-white rounded-lg border p-4">
      <p className="text-sm text-gray-500">{title}</p>
      <p className="text-2xl font-bold mt-1">{value}</p>
      {change && (
        <p className="text-xs text-gray-400 mt-1">{change}</p>
      )}
    </div>
  );
}
