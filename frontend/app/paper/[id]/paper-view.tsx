"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";
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

  const [futureCitations, setFutureCitations] = useState<Record<string, number>>({});

  const citationsByYear = paper?.citations_by_year;
  const processedChartData = citationsByYear
    ? Object.entries(citationsByYear).map(([year, count]) => ({
      name: year,
      [dataKey]: count,
    }))
    : [];

  const futureChartData = Object.entries(futureCitations).map(([key, count]) => {
    const year = key.replace("citations_", "");
    return {
      name: year,
      "Dự báo": count,
    };
  });

  const chartDataToShow =
    processedChartData.length > 0 || futureChartData.length > 0
      ? [...processedChartData]
      : sampleData;

  if (chartDataToShow !== sampleData) {
    futureChartData.forEach((futureItem) => {
      chartDataToShow.push({
        name: futureItem.name,
        "Dự báo": futureItem["Dự báo"],
      } as any);
    });

    if (processedChartData.length > 0 && futureChartData.length > 0) {
      const lastHistory = chartDataToShow[processedChartData.length - 1];
      (lastHistory as any)["Dự báo"] = (lastHistory as any)[dataKey];
    }
  }

  const chartConfig = {
    [dataKey]: {
      label: dataKey,
      color: "#03045e",
    },
    "Dự báo": {
      label: "Dự báo",
      color: "#00b4d8",
    },
  } satisfies ChartConfig;


  useEffect(() => {
    if (paper) {
      const fetchFutureCitations = async () => {
        try {
          const response = await fetch(`http://localhost:8000/predict/${paper.id}`);
          console.log(response);
          if (!response.ok) {
            throw new Error("Failed to fetch future citations");
          }
          const data = await response.json();
          setFutureCitations(data.prediction);
        } catch (error) {
          console.error("Error fetching future citations:", error);
        }
      };
      fetchFutureCitations();
    }
  }, [paper]);

  return (
    <main className="relative flex flex-col items-center h-screen overflow-hidden">
      <BackgroundParticles />

      <header className="flex w-full justify-center p-4 z-10 flex-shrink-0 bg-white/10 backdrop-blur-sm border-b border-white/20">
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
                    Feature Attribution
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
                  {paper && <AttributionChart paperId={paper.id} />}
                </TabsContent>
              </Tabs>
            </aside>
          </ResizablePanel>
        </ResizablePanelGroup>
      </div>
    </main>
  );
}