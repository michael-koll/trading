"use client";

import { CodePane } from "@/components/CodePane";

type CodingViewProps = {
  title: string;
  code: string;
  onChange: (value: string) => void;
  onSave: () => void;
  saveState: "idle" | "saving" | "saved" | "error";
};

export function CodingView({ title, code, onChange, onSave, saveState }: CodingViewProps) {
  return <CodePane value={code} onChange={onChange} onSave={onSave} saveState={saveState} title={title} />;
}
