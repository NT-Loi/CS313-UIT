"use client";
import BackgroundParticles from "@/components/BackgroundParticles";
import SearchBar from "@/components/SearchBar";
import { useRouter } from "next/navigation";
import Image from "next/image";

export default function HomePage() {
  const router = useRouter();

  const handleSearch = (query: string) => {
    router.push(`/search?q=${encodeURIComponent(query)}`);
  };

  return (
    <main className="relative flex flex-col items-center justify-center min-h-screen text-center">
      <BackgroundParticles />

      {/* Logo */}
      <div className="absolute" style={{ top: 'calc(50% - 160px)', left: '50%', transform: 'translateX(-50%)' }}>
        <Image src="/logo-slogan.svg" alt="App Logo" width={500} height={2000} />
      </div>

      {/* Search Bar */}
      <div className="flex justify-center w-full">
        <SearchBar onSearch={handleSearch} />
      </div>
    </main>
  );
}