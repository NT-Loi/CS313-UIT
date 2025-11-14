"use client";
import { Card, CardContent } from "@/components/ui/card";
import Link from "next/link";
import Image from "next/image";
import { useState } from "react";
import { FileText } from "lucide-react";

interface Paper {
  id: string;
  title: string;
  abstract: string;
}

interface ResultListProps {
  results: Paper[];
  loading?: boolean;
}

export default function ResultList({ results, loading = false }: ResultListProps) {
  // Generate thumbnail URL from paper ID
  const getThumbnailUrl = (paperId: string) => {
    return `https://cdn-thumbnails.huggingface.co/social-thumbnails/papers/${paperId}.png`;
  };

  // Show loading placeholder
  if (loading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 w-full max-w-6xl">
        {Array.from({ length: 6 }).map((_, i) => (
          <Card
            key={i}
            className="border-neutral-200 overflow-hidden animate-pulse bg-white/10 backdrop-blur-sm"
          >
            <CardContent className="p-0">
              {/* Placeholder for image */}
              <div className="w-full h-48 bg-neutral-200/50" />

              {/* Placeholder text sections */}
              <div className="p-4">
                <div className="h-5 bg-neutral-300/70 rounded mb-3 w-5/6" />
                <div className="h-4 bg-neutral-300/60 rounded mb-2 w-4/5" />
                <div className="h-4 bg-neutral-300/60 rounded mb-2 w-3/4" />
                <div className="h-4 bg-neutral-300/60 rounded mb-4 w-2/3" />
                <div className="h-4 bg-neutral-300/70 rounded w-24" />
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  // Show "no results" message
  if (results.length === 0) {
    return (
      <p className="text-neutral-500 mt-8">
        No results found. Try searching for another paper.
      </p>
    );
  }

  // Show results grid
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 w-full max-w-6xl">
      {results.map((paper) => (
        <PaperCard key={paper.id} paper={paper} getThumbnailUrl={getThumbnailUrl} />
      ))}
    </div>
  );
}

// Separate component to handle individual paper card state
function PaperCard({ paper, getThumbnailUrl }: { paper: Paper; getThumbnailUrl: (id: string) => string }) {
  const [imageError, setImageError] = useState(false);

  return (
    <Card className="hover:shadow-lg transition-shadow border-neutral-200 overflow-hidden">
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
          <p className="text-sm text-neutral-600 mb-4 line-clamp-3">{paper.abstract}</p>
          <Link
            href={`/paper/${paper.id}`}
            className="text-blue-600 hover:underline text-sm font-medium"
          >
            View details →
          </Link>
        </div>
      </CardContent>
    </Card>
  );
}