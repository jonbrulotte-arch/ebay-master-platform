"use client";

export default function ProductsPage() {
  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold">Products</h1>
          <p className="text-sm text-gray-500 mt-1">
            Manage your product catalog
          </p>
        </div>
        <button className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700">
          Add Product
        </button>
      </div>

      <div className="bg-white rounded-lg border">
        <div className="p-4 border-b flex gap-4">
          <input
            type="text"
            placeholder="Search products..."
            className="flex-1 border rounded-lg px-3 py-2 text-sm"
          />
          <select className="border rounded-lg px-3 py-2 text-sm">
            <option value="">All Conditions</option>
            <option value="NEW">New</option>
            <option value="USED">Used</option>
          </select>
          <select className="border rounded-lg px-3 py-2 text-sm">
            <option value="">All Status</option>
            <option value="true">Active</option>
            <option value="false">Inactive</option>
          </select>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b text-left text-xs text-gray-500 uppercase">
                <th className="px-4 py-3">SKU</th>
                <th className="px-4 py-3">Title</th>
                <th className="px-4 py-3">Brand</th>
                <th className="px-4 py-3">Condition</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3">Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td colSpan={6} className="px-4 py-8 text-center text-gray-400 text-sm">
                  No products yet. Click &quot;Add Product&quot; to get started.
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
