"use client";

import {
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
} from "@/components/ui/chart";
import { XAxis, YAxis, CartesianGrid, LineChart, Line } from "recharts";
import { ChartConfig } from "@/components/ui/chart";

// ---- KIỂU DỮ LIỆU ----
interface PaperChartProps {
  analysisData: any[];
  chartConfig: ChartConfig;
  dataKey: string | null;
}

// ---- DỮ LIỆU MẪU (luôn hiển thị nếu không có data) ----
const sampleData = [
  { name: "2019", "Lượt trích dẫn": 10 },
  { name: "2020", "Lượt trích dẫn": 25 },
  { name: "2021", "Lượt trích dẫn": 40 },
  { name: "2022", "Lượt trích dẫn": 35 },
  { name: "2023", "Lượt trích dẫn": 60 },
  { name: "2024", "Lượt trích dẫn": 85 },
];

// ---- COMPONENT CHÍNH ----
export function PaperChart({
  analysisData,
  chartConfig,
  dataKey,
}: PaperChartProps) {
  // Nếu không có dữ liệu, vẫn hiển thị biểu đồ mẫu
  const chartData =
    dataKey && analysisData && analysisData.length > 0
      ? analysisData
      : sampleData;

  return (
    <ChartContainer
      config={chartConfig}
      className="w-full h-full flex-grow"
    >
      <LineChart
        data={chartData}
        margin={{ top: 10, right: 20, left: 10, bottom: 5 }}
      >
        <CartesianGrid vertical={false} strokeDasharray="3 3" opacity={0.3} />
        <XAxis
          dataKey="name"
          tickLine={false}
          axisLine={false}
          tick={{ fill: "#666", fontSize: 12 }}
        />
        <YAxis
          tickLine={false}
          axisLine={false}
          tick={{ fill: "#666", fontSize: 12 }}
          width={40}
        />
        <ChartTooltip
          cursor={{ stroke: "#03045e", strokeWidth: 1, strokeDasharray: "4 4" }}
          content={<ChartTooltipContent />}
        />
        <Line
          type="monotone"
          dataKey={dataKey || "Lượt trích dẫn"}
          stroke={chartConfig[dataKey || "Lượt trích dẫn"]?.color || "#03045e"}
          strokeWidth={2}
          dot={{ r: 4, fill: "#03045e" }}
          activeDot={{ r: 6, strokeWidth: 0 }}
        />
        <Line
          type="monotone"
          dataKey="Dự báo"
          stroke={chartConfig["Dự báo"]?.color || "#00b4d8"}
          strokeWidth={2}
          strokeDasharray="5 5"
          dot={{ r: 4, fill: "#00b4d8" }}
          activeDot={{ r: 6, strokeWidth: 0 }}
        />
      </LineChart>
    </ChartContainer>
  );
}