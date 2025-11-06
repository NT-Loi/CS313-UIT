"use client";

import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Search } from "lucide-react";
import { useState } from "react";

interface SearchBarProps {
  defaultValue?: string;
  onSearch: (query: string) => void;
  loading?: boolean;
}

export default function SearchBar({ defaultValue = "", onSearch, loading = false }: SearchBarProps) {
  const [query, setQuery] = useState(defaultValue);

  const handleSearch = () => {
    if (query.trim()) onSearch(query);
  };

  return (
    <div className="flex w-full max-w-2xl gap-2">
      <Input
        placeholder="Search for a paper..."
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        onKeyDown={(e) => e.key === "Enter" && handleSearch()}
        className="shadow-sm !text-lg py-6 px-4"
      />
      <Button onClick={handleSearch} 
              disabled={loading} 
              className="bg-gradient-to-r from-[#03045e] to-[#0077b6] 
             hover:from-[#0077b6] hover:to-[#00b4d8]
             text-white text-lg py-6 px-6 rounded-xl shadow-lg transition-all duration-300">
        {loading ? "Searching..." : (<><Search className="mr-2 h-5 w-5" />Search</>)}
      </Button>
    </div>
  );
}