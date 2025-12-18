"use client";

import Link from "next/link";
import { useSearchParams, useRouter } from "next/navigation";

interface Author {
  name: string;
  citations_all?: number;
  citations_recent?: number;
  h_index_all?: number;
  h_index_recent?: number;
  i10_index_all?: number;
  i10_index_recent?: number;
}

interface Paper {
  id: string;
  title: string;
  abstract: string;
  authors?: Author[];
}

interface ResultListProps {
  results: Paper[];
  loading?: boolean;
  pageSize?: number;
}

export default function ResultList({
  results,
  loading = false,
  pageSize = 10,
}: ResultListProps) {
  const searchParams = useSearchParams();
  const router = useRouter();

  const query = searchParams.get("q") || "";
  const page = Number(searchParams.get("page") || 1);

  const totalPages = Math.ceil(results.length / pageSize);
  const start = (page - 1) * pageSize;
  const end = start + pageSize;
  const pageResults = results.slice(start, end);

  const goToPage = (p: number) => {
    const params = new URLSearchParams(searchParams.toString());
    params.set("page", String(p));
    router.push(`?${params.toString()}`);
  };

  /* ---------- Loading ---------- */
  if (loading) {
    return (
      <div className="space-y-4 mt-6 w-full max-w-4xl">
        {Array.from({ length: pageSize }).map((_, i) => (
          <div
            key={i}
            className="bg-white/95 backdrop-blur-sm border border-neutral-200 rounded-lg p-6 shadow-md animate-pulse"
          >
            <div className="h-6 bg-neutral-300/50 rounded w-3/4 mb-3" />
            <div className="h-4 bg-neutral-300/30 rounded w-1/2 mb-4" />
            <div className="h-4 bg-neutral-300/30 rounded w-full mb-2" />
            <div className="h-4 bg-neutral-300/30 rounded w-5/6" />
          </div>
        ))}
      </div>
    );
  }

  /* ---------- Empty ---------- */
  if (results.length === 0) {
    return (
      <div className="bg-white/95 backdrop-blur-sm border border-neutral-200 rounded-lg p-8 shadow-md mt-8 max-w-4xl">
        <p className="text-neutral-600">
          No results found. Try a different query.
        </p>
      </div>
    );
  }

  return (
    <div className="w-full mt-6 max-w-4xl">
      {/* Result count */}
      <p className="text-sm text-neutral-700 mb-4 px-1">
        About {results.length} results
      </p>

      {/* Result list */}
      <ul className="space-y-4">
        {pageResults.map((paper) => (
          <li
            key={paper.id}
            className="bg-white/95 backdrop-blur-sm border border-neutral-200 rounded-lg p-6 shadow-md hover:shadow-lg hover:border-neutral-300 transition-all"
          >
            <Link
              href={`/paper/${paper.id}?q=${encodeURIComponent(query)}`}
              className="text-blue-600 text-lg font-semibold hover:underline block"
            >
              {paper.title}
            </Link>

            {paper.authors && paper.authors.length > 0 && (
              <p className="text-sm text-neutral-600 mt-2">
                {paper.authors.map(author => author.name).join(", ")}
              </p>
            )}

            <p className="text-sm text-neutral-700 mt-3 line-clamp-3 leading-relaxed">
              {paper.abstract}
            </p>

            <Link
              href={`/paper/${paper.id}?q=${encodeURIComponent(query)}`}
              className="text-sm text-blue-600 hover:underline inline-block mt-3 font-medium"
            >
              View details →
            </Link>
          </li>
        ))}
      </ul>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-center gap-2 mt-8 flex-wrap bg-white/95 backdrop-blur-sm border border-neutral-200 rounded-lg p-4 shadow-md">
          <button
            disabled={page === 1}
            onClick={() => goToPage(page - 1)}
            className="px-4 py-2 text-sm rounded-md border border-neutral-300 bg-white hover:bg-neutral-50 disabled:opacity-40 disabled:cursor-not-allowed transition-colors font-medium"
          >
            Previous
          </button>

          {Array.from({ length: totalPages }).map((_, i) => {
            const p = i + 1;
            return (
              <button
                key={p}
                onClick={() => goToPage(p)}
                className={`px-4 py-2 text-sm rounded-md border font-medium transition-colors ${
                  p === page
                    ? "bg-blue-600 text-white border-blue-600 shadow-sm"
                    : "border-neutral-300 bg-white text-neutral-700 hover:bg-neutral-50"
                }`}
              >
                {p}
              </button>
            );
          })}

          <button
            disabled={page === totalPages}
            onClick={() => goToPage(page + 1)}
            className="px-4 py-2 text-sm rounded-md border border-neutral-300 bg-white hover:bg-neutral-50 disabled:opacity-40 disabled:cursor-not-allowed transition-colors font-medium"
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
}