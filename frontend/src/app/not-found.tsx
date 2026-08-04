import Link from "next/link";

export default function NotFound() {
  return (
    <div className="flex flex-col items-center justify-center min-h-screen gap-4 text-center">
      <h1 className="text-5xl font-bold text-gray-300">404</h1>
      <h2 className="text-xl font-semibold text-gray-700">Page not found</h2>
      <p className="text-gray-500 text-sm">The page you&apos;re looking for doesn&apos;t exist.</p>
      <Link
        href="/dashboard"
        className="mt-2 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 text-sm"
      >
        Go to Dashboard
      </Link>
    </div>
  );
}
