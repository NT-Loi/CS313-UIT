// app/paper/[id]/attribution-chart.tsx
"use client";

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  LabelList,
  Cell,
} from "recharts";
import {
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
} from "@/components/ui/chart";

import { useEffect, useState } from "react";

const COLOR_POSITIVE = "#00b4d8";
const COLOR_NEGATIVE = "#03045e";

const chartConfig = {
  weight: {
    label: "Contribution",
  },
};

const CustomBarLabel = (props: any) => {
  const { x, y, width, height, value } = props;
  const isNegative = value < 0;
  const formattedValue = (value > 0 ? "+" : "") + value.toFixed(3);
  const labelX = isNegative ? x - 5 : x + width + 5;
  const textAnchor = isNegative ? "end" : "start";

  return (
    <text
      x={labelX}
      y={y + height / 2}
      dy={4}
      fill="#caf0f8"
      textAnchor={textAnchor}
      fontSize={10}
      fontWeight="bold"
    >
      {formattedValue}
    </text>
  );
};

interface AttributionChartProps {
  paperId: string;
}

export function AttributionChart({ paperId }: AttributionChartProps) {
  const [data, setData] = useState<{ feature: string; weight: number }[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchAttribution = async () => {
      setLoading(true);
      try {
        const response = await fetch(`http://localhost:8000/attribution/${paperId}`);
        if (!response.ok) throw new Error("Failed to fetch attribution");
        const result = await response.json();
        setData(result.attribution);
      } catch (error) {
        console.error("Error fetching attribution:", error);
      } finally {
        setLoading(false);
      }
    };

    if (paperId) {
      fetchAttribution();
    }
  }, [paperId]);

  if (loading) {
    return (
      <div className="flex h-full w-full items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-[#90e0ef] border-t-transparent" />
      </div>
    );
  }

  if (data.length === 0) {
    return (
      <div className="flex h-full w-full items-center justify-center text-[#caf0f8]/60">
        Không có dữ liệu giải thích.
      </div>
    );
  }

  // Calculate max absolute weight for domain
  const maxAbs = Math.max(...data.map(d => Math.abs(d.weight)), 0.1);
  const domain: [number, number] = [-maxAbs * 1.5, maxAbs * 1.5];

  return (
    <ChartContainer config={chartConfig} className="h-full w-full">
      <BarChart
        layout="vertical"
        data={data}
        margin={{ top: 5, right: 60, left: 10, bottom: 5 }}
      >
        <CartesianGrid strokeDasharray="3 3" stroke="#caf0f8" strokeOpacity={0.2} />

        <XAxis type="number" domain={domain} hide />

        <YAxis
          type="category"
          dataKey="feature"
          stroke="#caf0f8"
          fontSize={11}
          tickLine={false}
          axisLine={false}
          width={130}
        />

        <ChartTooltip
          cursor={{ fill: "rgba(255, 255, 255, 0.1)" }}
          content={
            <ChartTooltipContent
              className="bg-[#0077b6]/95 backdrop-blur-xl border-[#90e0ef]/50 text-[#caf0f8] shadow-2xl rounded-2xl"
              labelClassName="text-[#caf0f8] font-bold"
            />
          }
        />

        <Bar dataKey="weight" radius={4}>
          {data.map((entry, index) => (
            <Cell
              key={`cell-${index}`}
              fill={entry.weight >= 0 ? COLOR_POSITIVE : COLOR_NEGATIVE}
            />
          ))}
          <LabelList dataKey="weight" content={<CustomBarLabel />} />
        </Bar>
      </BarChart>
    </ChartContainer>
  );
}