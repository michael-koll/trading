"use client";

import { CodePane } from "@/components/CodePane";

type CodingViewProps = {
  title: string;
  code: string;
  onChange: (value: string) => void;
  onSave: () => void;
};

export function CodingView({ title, code, onChange, onSave }: CodingViewProps) {
  return <CodePane value={code} onChange={onChange} onSave={onSave} title={title} />;
}
