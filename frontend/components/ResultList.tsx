"use client";

import { Card, CardContent } from "@/components/ui/card";
import Link from "next/link";
import Image from "next/image";
import { useState } from "react";
import { FileText } from "lucide-react";
import { useSearchParams } from "next/navigation";

interface Paper {
  id: string;
  title: string;
  abstract: string;
  authors?: string[];
  pdf_url?: string;
}

interface ResultListProps {
  results: Paper[];
  loading?: boolean;
}

export default function ResultList({ results, loading = false }: ResultListProps) {
  const searchParams = useSearchParams();
  const currentQuery = searchParams.get("q") || "";

  const getThumbnailUrl = (paperId: string) =>
    `https://cdn-thumbnails.huggingface.co/social-thumbnails/papers/${paperId}.png`;

  if (loading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 w-full max-w-6xl">
        {Array.from({ length: 6 }).map((_, i) => (
          <Card
            key={i}
            className="border-white/20 overflow-hidden animate-pulse bg-white/10 backdrop-blur-sm"
          >
            <CardContent className="p-0">
              <div className="w-full h-48 bg-neutral-200/20" />
              <div className="p-4">
                <div className="h-5 bg-neutral-300/30 rounded mb-3 w-5/6" />
                <div className="h-4 bg-neutral-300/20 rounded mb-2 w-4/5" />
                <div className="h-4 bg-neutral-300/20 rounded mb-2 w-3/4" />
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  if (results.length === 0) {
    return (
      <p className="text-neutral-400 mt-8">
        No results found. Try searching for another paper.
      </p>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 w-full max-w-6xl">
      {results.map((paper) => (
        <PaperCard
          key={paper.id}
          paper={paper}
          getThumbnailUrl={getThumbnailUrl}
          currentQuery={currentQuery}
        />
      ))}
    </div>
  );
}

function PaperCard({
  paper,
  getThumbnailUrl,
  currentQuery,
}: {
  paper: Paper;
  getThumbnailUrl: (id: string) => string;
  currentQuery: string;
}) {
  const [imageError, setImageError] = useState(false);

  return (
    <Card className="transition-shadow overflow-hidden bg-white/10 backdrop-blur-sm shadow-xl border-white/20 text-white">
      <CardContent className="p-0">
        {/* Paper Preview Image */}
        <div className="relative w-full h-48 bg-gradient-to-br from-blue-50 to-indigo-50">
          {!imageError ? (
            <Image
              src={getThumbnailUrl(paper.id)}
              alt={paper.title}
              fill
              className="object-cover"
              onError={() => setImageError(true)}
            />
          ) : (
            <div className="flex flex-col items-center justify-center h-full text-neutral-400">
              <FileText className="w-16 h-16 mb-2" />
              <span className="text-sm">No preview available</span>
            </div>
          )}
        </div>

        {/* Paper Details */}
        <div className="p-4">
          <h2 className="text-lg font-semibold mb-2 line-clamp-2">{paper.title}</h2>
          <p className="text-sm text-neutral-300 mb-4 line-clamp-3">{paper.abstract}</p>

          <Link
            href={`/paper/${paper.id}?q=${encodeURIComponent(currentQuery)}`}
            className="text-blue-400 hover:underline text-sm font-medium"
          >
            View details →
          </Link>
        </div>
      </CardContent>
    </Card>
  );
}
