"use client";

import {
  CandlestickData,
  CandlestickSeries,
  createChart,
  createSeriesMarkers,
  IChartApi,
  LineData,
  LineSeries,
  SeriesMarker,
  Time,
} from "lightweight-charts";
import { useEffect, useRef } from "react";

type PriceBar = {
  time: string;
  open: number;
  high: number;
  low: number;
  close: number;
};

type TradeMarker = {
  time: string;
  price: number;
  side: "buy" | "sell";
};

type TradeChartPaneProps = {
  bars: PriceBar[];
  markers: TradeMarker[];
  indicators?: Record<string, { time: string; value: number }[]>;
  indicatorColors?: Record<string, string>;
};

export function TradeChartPane({ bars, markers, indicators, indicatorColors }: TradeChartPaneProps) {
  const ref = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (!ref.current) return;

    const chart: IChartApi = createChart(ref.current, {
      height: 480,
      layout: { background: { color: "#0a0a0c" }, textColor: "#8A8F98" },
      grid: {
        vertLines: { color: "rgba(255,255,255,0.06)" },
        horzLines: { color: "rgba(255,255,255,0.06)" },
      },
      rightPriceScale: { borderColor: "rgba(255,255,255,0.12)" },
      timeScale: { borderColor: "rgba(255,255,255,0.12)" },
      crosshair: { mode: 1 },
    });

    const anyChart = chart as any;
    const candleSeries =
      typeof anyChart.addCandlestickSeries === "function"
        ? anyChart.addCandlestickSeries({
            upColor: "#2db887",
            downColor: "#d05c70",
            wickUpColor: "#2db887",
            wickDownColor: "#d05c70",
            borderVisible: false,
          })
        : chart.addSeries(CandlestickSeries, {
            upColor: "#2db887",
            downColor: "#d05c70",
            wickUpColor: "#2db887",
            wickDownColor: "#d05c70",
            borderVisible: false,
          });

    const candleData: CandlestickData[] = bars.map((b) => ({
      time: Math.floor(new Date(b.time).getTime() / 1000) as Time,
      open: b.open,
      high: b.high,
      low: b.low,
      close: b.close,
    }));
    candleSeries.setData(candleData);

    const sortedMarkers = [...markers].sort(
      (a, b) => new Date(a.time).getTime() - new Date(b.time).getTime()
    );

    const seriesMarkers: SeriesMarker<Time>[] = sortedMarkers.map((m) => ({
      time: Math.floor(new Date(m.time).getTime() / 1000) as Time,
      position: m.side === "buy" ? "belowBar" : "aboveBar",
      color: m.side === "buy" ? "#2db887" : "#d05c70",
      shape: m.side === "buy" ? "arrowUp" : "arrowDown",
    }));

    if (typeof (candleSeries as any).setMarkers === "function") {
      (candleSeries as any).setMarkers(seriesMarkers);
    } else {
      createSeriesMarkers(candleSeries as any, seriesMarkers as any);
    }

    const defaultIndicatorColors: Record<string, string> = {
      sma_fast: "#ffd166",
      sma_slow: "#60a5fa",
    };
    for (const [name, points] of Object.entries(indicators || {})) {
      if (!points?.length) continue;
      const lineColor =
        (indicatorColors && indicatorColors[name]) ||
        defaultIndicatorColors[name] ||
        "rgba(255,255,255,0.65)";
      const lineSeries =
        typeof (chart as any).addLineSeries === "function"
          ? (chart as any).addLineSeries({
              color: lineColor,
              lineWidth: 2,
              crosshairMarkerVisible: false,
              lastValueVisible: false,
              priceLineVisible: false,
            })
          : chart.addSeries(LineSeries, {
              color: lineColor,
              lineWidth: 2,
              crosshairMarkerVisible: false,
              lastValueVisible: false,
              priceLineVisible: false,
            });

      const lineData: LineData[] = points.map((p) => ({
        time: Math.floor(new Date(p.time).getTime() / 1000) as Time,
        value: p.value,
      }));
      lineSeries.setData(lineData);
    }

    // Draw connector lines between matching entry/exit marker pairs.
    let openEntry: TradeMarker | null = null;
    for (const marker of sortedMarkers) {
      if (marker.side === "buy") {
        openEntry = marker;
        continue;
      }
      if (!openEntry) continue;
      const isWin = marker.price >= openEntry.price;
      const tradeColor = isWin ? "rgba(45,184,135,0.85)" : "rgba(208,92,112,0.85)";

      const lineSeries =
        typeof (chart as any).addLineSeries === "function"
          ? (chart as any).addLineSeries({
              color: tradeColor,
              lineWidth: 1,
              crosshairMarkerVisible: false,
              lastValueVisible: false,
              priceLineVisible: false,
            })
          : chart.addSeries(LineSeries, {
              color: tradeColor,
              lineWidth: 1,
              crosshairMarkerVisible: false,
              lastValueVisible: false,
              priceLineVisible: false,
            });

      const lineData: LineData[] = [
        {
          time: Math.floor(new Date(openEntry.time).getTime() / 1000) as Time,
          value: openEntry.price,
        },
        {
          time: Math.floor(new Date(marker.time).getTime() / 1000) as Time,
          value: marker.price,
        },
      ];
      lineSeries.setData(lineData);
      openEntry = null;
    }

    chart.timeScale().fitContent();

    const resize = () => chart.applyOptions({ width: ref.current?.clientWidth || 0 });
    resize();
    window.addEventListener("resize", resize);

    return () => {
      window.removeEventListener("resize", resize);
      chart.remove();
    };
  }, [bars, markers, indicators, indicatorColors]);

  return <div ref={ref} className="chart-root" />;
}
