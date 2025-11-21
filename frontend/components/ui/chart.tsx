"use client";

import * as React from "react";
import * as RechartsPrimitive from "recharts";
import { cn } from "@/lib/utils";

const THEMES = { light: "", dark: ".dark" } as const;

export type ChartConfig = {
  [k in string]: {
    label?: React.ReactNode;
    icon?: React.ComponentType<{ className?: string }>;
  } & (
    | { color?: string; theme?: never }
    | { color?: never; theme: Record<keyof typeof THEMES, string> }
  );
};

type ChartContextProps = { config: ChartConfig };
const ChartContext = React.createContext<ChartContextProps | null>(null);

const useChart = () => {
  const context = React.useContext(ChartContext);
  if (!context) throw new Error("useChart must be used within a <ChartContainer />");
  return context;
};

const ChartStyle = ({ id, config }: { id: string; config: ChartConfig }) => {
  const colorConfig = Object.entries(config).filter(
    ([, config]) => config.theme || config.color
  );

  if (!colorConfig.length) return null;

  return (
    <style
      dangerouslySetInnerHTML={{
        __html: Object.entries(THEMES)
          .map(
            ([theme, prefix]) => `
${prefix} [data-chart=${id}] {
${colorConfig
  .map(([key, itemConfig]) => {
    const color =
      itemConfig.theme?.[theme as keyof typeof itemConfig.theme] ||
      itemConfig.color;
    return color ? `  --color-${key}: ${color};` : "";
  })
  .filter(Boolean)
  .join("\n")}
}`
          )
          .join("\n")
          .trim(),
      }}
    />
  );
};

type ChartContainerProps = React.ComponentProps<"div"> & {
  config: ChartConfig;
  children: React.ReactElement;
};

const ChartContainer = ({
  id,
  className,
  children,
  config,
  ...props
}: ChartContainerProps) => {
  const uniqueId = React.useId();
  const chartId = `chart-${id || uniqueId.replace(/:/g, "")}`;

  return (
    <ChartContext.Provider value={{ config }}>
      <div
        data-chart={chartId}
        className={cn(
          "flex aspect-video justify-center text-xs [&_.recharts-cartesian-axis-tick_text]:fill-muted-foreground [&_.recharts-cartesian-grid_line]:stroke-border/50 [&_.recharts-curve.recharts-tooltip-cursor]:stroke-border [&_.recharts-rectangle.recharts-tooltip-cursor]:fill-muted [&_.recharts-reference-line_line]:stroke-border [&_.recharts-sector]:outline-none",
          className
        )}
        {...props}
      >
        <ChartStyle id={chartId} config={config} />
        <RechartsPrimitive.ResponsiveContainer>
          {children}
        </RechartsPrimitive.ResponsiveContainer>
      </div>
    </ChartContext.Provider>
  );
};

const ChartTooltip = RechartsPrimitive.Tooltip;

type ChartTooltipContentProps = React.HTMLAttributes<HTMLDivElement> & {
  hideLabel?: boolean;
  hideIndicator?: boolean;
  indicator?: "dot" | "line" | "dashed";
  nameKey?: string;
  labelKey?: string;
  labelClassName?: string;
  labelFormatter?: (value: any, payload: any[]) => React.ReactNode;
  formatter?: (
    value: any,
    name: any,
    item: any,
    index: number,
    payload: any
  ) => React.ReactNode;
};

const ChartTooltipContent = ({
  active,
  payload,
  className,
  indicator = "dot",
  hideLabel = false,
  hideIndicator = false,
  label,
  labelFormatter,
  labelClassName,
  formatter,
  nameKey,
}: ChartTooltipContentProps & {
  active?: boolean;
  payload?: any[];
  label?: string | number;
}) => {
  const { config } = useChart();

  const tooltipLabel = React.useMemo(() => {
    if (hideLabel || !payload?.length) return null;

    const value = label;

    if (labelFormatter) {
      return (
        <div className={cn("font-medium", labelClassName)}>
          {labelFormatter(value, payload)}
        </div>
      );
    }

    if (value === undefined || value === null) return null;

    return <div className={cn("font-medium", labelClassName)}>{value}</div>;
  }, [label, labelFormatter, payload, hideLabel, labelClassName]);

  if (!active || !payload?.length) return null;

  const nestLabel = payload.length === 1 && indicator !== "dot";

  return (
    <div
      className={cn(
        "grid min-w-[8rem] gap-1.5 rounded-lg border bg-background px-2.5 py-1.5 text-xs shadow-xl",
        className
      )}
    >
      {!nestLabel && tooltipLabel}
      <div className="grid gap-1.5">
        {payload.map((item, index) => {
          const key = `${nameKey || item.name || item.dataKey || "value"}`;
          const itemConfig = config[key];
          const color = item.color || item.payload?.fill || "currentColor";

          return (
            <div
              key={index}
              className={cn("flex items-center gap-2", indicator === "dot" && "items-center")}
            >
              {!hideIndicator && (
                <div
                  className={cn(
                    "shrink-0 rounded-[2px] border-[--color-border] bg-[--color-bg]",
                    {
                      "h-2.5 w-2.5": indicator === "dot",
                      "w-1": indicator === "line",
                      "w-0 border-[1.5px] border-dashed bg-transparent": indicator === "dashed",
                    }
                  )}
                  style={{
                    "--color-bg": color,
                    "--color-border": color,
                  } as React.CSSProperties}
                />
              )}
              {formatter ? (
                formatter(item.value, item.name, item, index, item.payload)
              ) : (
                <div className="flex flex-1 justify-between leading-none">
                  <span className="text-muted-foreground">
                    {itemConfig?.label || item.name}
                  </span>
                  <span className="font-mono font-medium tabular-nums text-foreground">
                    {item.value?.toLocaleString()}
                  </span>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};

const ChartLegend = RechartsPrimitive.Legend;

type ChartLegendContentProps = React.ComponentProps<"div"> & {
  hideIcon?: boolean;
  payload?: any[];
  verticalAlign?: "top" | "bottom";
  nameKey?: string;
};

const ChartLegendContent = ({
  className,
  hideIcon = false,
  payload,
  verticalAlign = "bottom",
}: ChartLegendContentProps) => {
  const { config } = useChart();

  if (!payload?.length) return null;

  return (
    <div
      className={cn(
        "flex items-center justify-center gap-4",
        verticalAlign === "top" ? "pb-3" : "pt-3",
        className
      )}
    >
      {payload.map((item) => {
        const key = item.value as string;
        const itemConfig = config[key];

        return (
          <div
            key={key}
            className="flex items-center gap-1.5 text-muted-foreground"
          >
            {itemConfig?.icon && !hideIcon ? (
              <itemConfig.icon />
            ) : (
              <div
                className="h-2 w-2 shrink-0 rounded-[2px]"
                style={{ backgroundColor: item.color }}
              />
            )}
            <span className="text-xs">{itemConfig?.label || item.value}</span>
          </div>
        );
      })}
    </div>
  );
};

export {
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
  ChartLegend,
  ChartLegendContent,
  ChartStyle,
};