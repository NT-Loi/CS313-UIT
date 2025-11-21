"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { useState } from "react";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";
import BackgroundParticles from "@/components/BackgroundParticles";
import SearchBar from "@/components/SearchBar";
import { PaperChart } from "./paper-chart";
import { ChartConfig } from "@/components/ui/chart";
import { Paper } from "@/lib/types";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { AttributionChart } from "./attribution-chart";
import {
  ResizableHandle,
  ResizablePanel,
  ResizablePanelGroup,
} from "@/components/ui/resizable";

interface PaperViewProps {
  paper: Paper | null;
}

export function PaperClientView({ paper }: PaperViewProps) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const query = searchParams.get("q") || "";
  const [pdfLoading, setPdfLoading] = useState(true);

  const handleSearch = (newQuery: string) => {
    router.push(`/search?q=${encodeURIComponent(newQuery)}`);
  };

  const dataKey = "Lượt trích dẫn";

  const sampleData = [
    { name: "2019", [dataKey]: 10 },
    { name: "2020", [dataKey]: 25 },
    { name: "2021", [dataKey]: 40 },
    { name: "2022", [dataKey]: 35 },
    { name: "2023", [dataKey]: 60 },
    { name: "2024", [dataKey]: 85 },
  ];

  const citationsByYear = paper?.citations_by_year;
  const processedChartData = citationsByYear
    ? Object.entries(citationsByYear).map(([year, count]) => ({
        name: year,
        [dataKey]: count,
      }))
    : [];

  const chartDataToShow =
    processedChartData.length > 0 ? processedChartData : sampleData;

  const chartConfig = {
    [dataKey]: {
      label: dataKey,
      color: "#8884d8",
    },
  } satisfies ChartConfig;

  return (
    <main className="relative flex flex-col items-center h-screen overflow-hidden">
      <BackgroundParticles />

      <header className="flex w-full justify-center p-4 z-10 flex-shrink-0 bg-white/10 backdrop-blur-sm border-b border-white/20">
        <div className="flex w-full max-w-5xl items-center gap-4">
          <Link
            href={query ? `/search?q=${encodeURIComponent(query)}` : "/search"}
            className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full hover:bg-neutral-200/40 transition-colors"
            title="Back to Search"
          >
            <ArrowLeft className="h-6 w-6 text-neutral-700" />
          </Link>

          <div className="flex-grow">
            <SearchBar
              defaultValue={query}
              onSearch={handleSearch}
              loading={false}
              className="bg-white/80 border-neutral-300 placeholder-neutral-500 focus-visible:ring-blue-500"
            />
          </div>

          <div className="h-10 w-10 shrink-0" />
        </div>
      </header>

      <div className="flex-1 w-full px-6 pb-6 overflow-hidden z-10">
        <ResizablePanelGroup direction="horizontal" className="h-full w-full">
          <ResizablePanel defaultSize={60}>
            <section className="h-full w-full overflow-hidden rounded-lg bg-white/10 backdrop-blur-sm shadow-xl border-white/20 relative">
              {pdfLoading && (
                <div className="absolute inset-0 z-10 flex items-center justify-center bg-black/40 backdrop-blur-sm">
                  <div className="text-center">
                    <div className="mx-auto mb-4 h-16 w-16 animate-spin rounded-full border-4 border-[#90e0ef] border-t-transparent" />
                    <p className="text-lg font-medium text-[#caf0f8]">Đang tải tài liệu...</p>
                  </div>
                </div>
              )}
              <iframe
                src={paper?.pdf_url ? `${paper.pdf_url}#toolbar=0&navpanes=0` : undefined}
                className="h-full w-full rounded-lg border-0"
                title={`PDF Viewer for ${paper?.title}`}
                onLoad={() => setPdfLoading(false)}
                onError={() => setPdfLoading(false)}
              />
            </section>
          </ResizablePanel>

          <ResizableHandle
            withHandle
            className="w-2 bg-transparent hover:bg-white/20 data-[resize-handle-active]:bg-white/30 transition-all"
          />

          <ResizablePanel defaultSize={40}>
            <aside className="h-full w-full flex flex-col rounded-lg p-6">
              <h3 className="mb-4 text-lg font-semibold">Phân tích xu hướng trích dẫn</h3>

              <Tabs defaultValue="chart" className="flex h-full flex-col flex-grow">
                <TabsList className="grid grid-cols-2 rounded-md bg-white/10 p-1">
                  <TabsTrigger
                    value="chart"
                    className="w-full data-[state=active]:bg-white/20 data-[state=active]:text-[#90e0ef] data-[state=active]:font-semibold text-neutral-300"
                  >
                    Biểu đồ
                  </TabsTrigger>
                  <TabsTrigger
                    value="attribution"
                    className="w-full data-[state=active]:bg-white/20 data-[state=active]:text-[#90e0ef] data-[state=active]:font-semibold text-neutral-300"
                  >
                    Future Attribution
                  </TabsTrigger>
                </TabsList>

                <TabsContent value="chart" className="mt-4 h-full flex-grow">
                  <PaperChart
                    analysisData={chartDataToShow}
                    chartConfig={chartConfig}
                    dataKey={dataKey}
                  />
                </TabsContent>

                <TabsContent value="attribution" className="mt-4 h-full flex-grow">
                  <AttributionChart />
                </TabsContent>
              </Tabs>
            </aside>
          </ResizablePanel>
        </ResizablePanelGroup>
      </div>
    </main>
  );
}