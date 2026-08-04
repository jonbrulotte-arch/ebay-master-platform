"use client";

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <html>
      <body className="bg-gray-50 text-gray-900 antialiased">
        <div className="flex flex-col items-center justify-center min-h-screen gap-4 text-center p-8">
          <h2 className="text-2xl font-semibold text-red-600">Something went wrong</h2>
          <p className="text-gray-500 text-sm max-w-md">
            {error.message || "An unexpected error occurred. Please try again."}
          </p>
          {error.digest && (
            <p className="text-xs text-gray-400">Error ID: {error.digest}</p>
          )}
          <button
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 text-sm"
            onClick={reset}
          >
            Try again
          </button>
        </div>
      </body>
    </html>
  );
}
