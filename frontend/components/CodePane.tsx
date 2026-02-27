"use client";

import dynamic from "next/dynamic";
const MonacoEditor = dynamic(() => import("@monaco-editor/react"), { ssr: false });

type CodePaneProps = {
  value: string;
  onChange: (value: string) => void;
  onSave: () => void;
  title: string;
};

export function CodePane({ value, onChange, onSave, title }: CodePaneProps) {
  const handleBeforeMount = (monaco: typeof import("monaco-editor")) => {
    monaco.editor.defineTheme("glass-dark", {
      base: "vs-dark",
      inherit: true,
      rules: [],
      colors: {
        "editor.background": "#00000000",
        "editorGutter.background": "#00000000",
        "minimap.background": "#00000000",
        "editorLineNumber.foreground": "#6f7480",
        "editorLineNumber.activeForeground": "#a6adbb",
        "scrollbar.shadow": "#00000000",
        "scrollbarSlider.background": "#5e6ad273",
        "scrollbarSlider.hoverBackground": "#6872d997",
        "scrollbarSlider.activeBackground": "#6872d9bf",
      },
    });
  };

  return (
    <section className="card code-pane">
      <div className="panel-head">
        <div>
          <div className="section-label">EDITOR</div>
          <h3>{title}</h3>
        </div>
        <button className="btn-primary" onClick={onSave}>
          Save Strategy
        </button>
      </div>
      <div className="editor-wrap">
        <MonacoEditor
          height="100%"
          defaultLanguage="python"
          value={value}
          beforeMount={handleBeforeMount}
          onChange={(next) => onChange(next || "")}
          theme="glass-dark"
          options={{
            minimap: { enabled: false },
            fontSize: 13,
            fontLigatures: true,
            smoothScrolling: true,
            overviewRulerBorder: false,
            scrollbar: {
              verticalScrollbarSize: 8,
              horizontalScrollbarSize: 8,
            },
          }}
        />
      </div>
    </section>
  );
}
