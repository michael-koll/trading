"use client";

import { createChart, IChartApi, LineData, LineSeries } from "lightweight-charts";
import { useEffect, useRef } from "react";

type Point = { time: string; value: number };

type ChartPaneProps = {
  points: Point[];
};

export function ChartPane({ points }: ChartPaneProps) {
  const ref = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (!ref.current) return;
    const chart: IChartApi = createChart(ref.current, {
      height: 260,
      layout: { background: { color: "#0a0a0c" }, textColor: "#8A8F98" },
      grid: {
        vertLines: { color: "rgba(255,255,255,0.06)" },
        horzLines: { color: "rgba(255,255,255,0.06)" },
      },
      rightPriceScale: { borderColor: "rgba(255,255,255,0.12)" },
      timeScale: { borderColor: "rgba(255,255,255,0.12)" },
    });

    const anyChart = chart as any;
    const series =
      typeof anyChart.addLineSeries === "function"
        ? anyChart.addLineSeries({ color: "#5E6AD2", lineWidth: 2 })
        : chart.addSeries(LineSeries, { color: "#5E6AD2", lineWidth: 2 });
    const data: LineData[] = points.map((p) => ({
      time: Math.floor(new Date(p.time).getTime() / 1000) as LineData["time"],
      value: p.value,
    }));
    series.setData(data);
    chart.timeScale().fitContent();

    const resize = () => chart.applyOptions({ width: ref.current?.clientWidth || 0 });
    resize();
    window.addEventListener("resize", resize);

    return () => {
      window.removeEventListener("resize", resize);
      chart.remove();
    };
  }, [points]);

  return <div ref={ref} className="chart-root" />;
}
