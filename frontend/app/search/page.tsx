"use client"
import BackgroundParticles from "@/components/BackgroundParticles";
import SearchBar from "@/components/SearchBar";
import ResultList from "@/components/ResultList";
import { useState, useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
// import Image from "next/image";
import { ArrowLeft } from "lucide-react";

export default function SearchPage() {
    const [query, setQuery] = useState("")
    const [results, setResults] = useState<any[]>([])
    const [loading, setLoading] = useState(false)

    const searchParams = useSearchParams()
    const initialQuery = searchParams.get("q") || ""

    useEffect(() => {
    if (initialQuery) {
        setQuery(initialQuery)
        handleSearch(initialQuery)
    }
    }, [initialQuery])

    const router = useRouter()

    const handleSearch = async (customQuery?: string) => {
    const q = customQuery ?? query
    if (!q.trim()) return

    // Update the URL to show ?q=yoursearch
    router.push(`/search?q=${encodeURIComponent(q)}`, { scroll: false })

    console.log("Searching for:", q)
    setLoading(true)
    try {
        const res = await fetch(`/api/search?query=${encodeURIComponent(q)}`)
        const data = await res.json()
        setResults(data)
    } catch (error) {
        console.error("Search error:", error)
    }
    setLoading(false)
    }

  return (
    <main className="relative flex flex-col items-center justify-center min-h-screen text-center">
      <BackgroundParticles/>

      {/* --- Search Section --- */}
      <div className="flex justify-center w-full mt-8">
        <div className="flex items-center gap-4 max-w-2xl w-full px-4">

          {/* Back Button */}
          <Link
            href="/"
            className="flex items-center justify-center w-10 h-10 rounded-full hover:bg-neutral-200/40 transition-colors"
            title="Back to Home"
          >
            <ArrowLeft className="w-6 h-6 text-neutral-700" />
          </Link>

          {/* Search Bar */}
          <div className="flex-grow">
            <SearchBar onSearch={handleSearch} />
          </div>
        </div>
      </div>

      <div className="min-h-screen bg-transparent flex flex-col items-center p-8">
        {/* --- Result List Section --- */}
        <ResultList results={results} loading={loading} />
      </div>
    </main>
  )
}