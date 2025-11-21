"use client"; 

import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import { ArrowLeft } from 'lucide-react';

export default function BackButton() {
  const searchParams = useSearchParams();
  const query = searchParams.get('q');
  
  const href = query ? `/search?q=${encodeURIComponent(query)}` : '/search';

  return (
    <Link
      href={href}
      className="flex items-center justify-center w-10 h-10 rounded-full hover:bg-neutral-200/40 transition-colors"
      title="Back to Search"
    >
      <ArrowLeft className="w-6 h-6 text-neutral-700" />
    </Link>
  );
}