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

const attributionData = [
  { feature: "0.325 = ShellWeight", value: 1.42 },
  { feature: "1.103 = WholeWeight", value: 0.97 },
  { feature: "0.301 = VisceraWeight", value: -0.79 },
  { feature: "0.421 = ShuckedWeight", value: -0.38 },
  { feature: "0.16 = Height", value: 0.19 },
  { feature: "False = Sex_I", value: 0.06 },
  { feature: "0.605 = Length", value: -0.05 },
  { feature: "True = Sex_M", value: 0.02 },
  { feature: "0.455 = Diameter", value: 0.0 },
];

const COLOR_POSITIVE = "#00b4d8";
const COLOR_NEGATIVE = "#03045e";

const chartConfig = {
  value: {
    label: "Contribution",
  },
};

const CustomBarLabel = (props: any) => {
  const { x, y, width, height, value } = props;
  const isNegative = value < 0;
  const formattedValue = (value > 0 ? "+" : "") + value.toFixed(2);
  const labelX = isNegative ? x - 5 : x + width + 5;
  const textAnchor = isNegative ? "end" : "start";

  return (
    <text
      x={labelX}
      y={y + height / 2}
      dy={4}
      fill="#caf0f8"
      textAnchor={textAnchor}
      fontSize={12}
      fontWeight="bold"
    >
      {formattedValue}
    </text>
  );
};

export function AttributionChart() {
  return (
    <ChartContainer config={chartConfig} className="h-full w-full">
      <BarChart
        layout="vertical"
        data={attributionData}
        margin={{ top: 5, right: 50, left: 30, bottom: 5 }}
      >
        <CartesianGrid strokeDasharray="3 3" stroke="#caf0f8" strokeOpacity={0.2} />

        <XAxis type="number" domain={[-1.5, 1.5]} stroke="#caf0f8" fontSize={12} />

        <YAxis
          type="category"
          dataKey="feature"
          stroke="#caf0f8"
          fontSize={12}
          tickLine={false}
          axisLine={false}
          width={150}
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

        <Bar dataKey="value" radius={4}>
          {attributionData.map((entry, index) => (
            <Cell
              key={`cell-${index}`}
              fill={entry.value >= 0 ? COLOR_POSITIVE : COLOR_NEGATIVE}
            />
          ))}
          <LabelList dataKey="value" content={<CustomBarLabel />} />
        </Bar>
      </BarChart>
    </ChartContainer>
  );
}