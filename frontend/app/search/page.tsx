"use client"
import BackgroundParticles from "@/components/BackgroundParticles";
import SearchBar from "@/components/SearchBar";
import ResultList from "@/components/ResultList";
import { useState, useEffect, useRef } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";

export default function SearchPage() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  const router = useRouter();
  const searchParams = useSearchParams();
  const initialQuery = searchParams.get("q") || "";

  // tránh gọi fetch 2 lần khi vừa load từ url (chỉ fetch nếu không có dữ liệu cached)
  const firstLoad = useRef(true);

  // Khi component mount / khi initialQuery thay đổi:
  useEffect(() => {
    if (!initialQuery) return;

    setQuery(initialQuery);

    // Nếu có data cached cho query trong sessionStorage -> restore và không fetch
    try {
      const cached = sessionStorage.getItem(`search:${initialQuery}`);
      if (cached) {
        setResults(JSON.parse(cached));
        setLoading(false);
        firstLoad.current = false; // đã restore lần đầu
        return;
      }
    } catch (e) {
      // ignore sessionStorage errors
    }

    // Nếu chưa có cache và là lần đầu load URL thì fetch
    if (firstLoad.current) {
      firstLoad.current = false;
      handleSearch(initialQuery);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [initialQuery]);

  // Hàm search: fetch API, cập nhật state và lưu vào sessionStorage
  const handleSearch = async (customQuery?: string) => {
    const q = (customQuery ?? query ?? "").trim();
    if (!q) return;

    // Cập nhật URL để có ?q=...
    router.push(`/search?q=${encodeURIComponent(q)}`, { scroll: false });

    setQuery(q);
    setLoading(true);
    try {
      const res = await fetch(`/api/search?query=${encodeURIComponent(q)}`);
      const data = await res.json();
      setResults(data);

      // Lưu vào sessionStorage để restore khi user back
      try {
        sessionStorage.setItem(`search:${q}`, JSON.stringify(data));
        sessionStorage.setItem("lastSearchQuery", q);
      } catch (e) {
        // ignore storage errors (private mode etc.)
      }
    } catch (error) {
      console.error("Search error:", error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="relative flex flex-col items-center justify-center min-h-screen text-center">
      <BackgroundParticles />

      <div className="flex justify-center w-full mt-8">
        <div className="flex items-center gap-4 max-w-2xl w-full px-4">
          <Link
            href="/"
            className="flex items-center justify-center w-10 h-10 rounded-full hover:bg-neutral-200/40 transition-colors"
            title="Back to Home"
          >
            <ArrowLeft className="w-6 h-6 text-neutral-700" />
          </Link>

          <div className="flex-grow">
            {/* pass defaultValue để input hiển thị query hiện tại */}
            <SearchBar onSearch={handleSearch} defaultValue={initialQuery} loading={loading} />
          </div>
        </div>
      </div>

      <div className="min-h-screen bg-transparent flex flex-col items-center p-8">
        <ResultList results={results} loading={loading} />
      </div>
    </main>
  );
}
