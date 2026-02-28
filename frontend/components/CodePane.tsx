"use client";

import dynamic from "next/dynamic";
const MonacoEditor = dynamic(() => import("@monaco-editor/react"), { ssr: false });

type CodePaneProps = {
  value: string;
  onChange: (value: string) => void;
  onSave: () => void;
  saveState: "idle" | "saving" | "saved" | "error";
  title: string;
};

export function CodePane({ value, onChange, onSave, saveState, title }: CodePaneProps) {
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
        <button
          className="btn-primary icon-action-btn"
          onClick={onSave}
          disabled={saveState === "saving"}
          aria-label={saveState === "saving" ? "Saving strategy" : "Save strategy"}
          title={saveState === "saving" ? "Saving strategy" : "Save strategy"}
        >
          {saveState === "saving" ? (
            <span className="loading-dots" aria-hidden="true">
              <span />
              <span />
              <span />
            </span>
          ) : (
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" aria-hidden="true">
              <path
                d="M5 3H16L21 8V19C21 20.105 20.105 21 19 21H5C3.895 21 3 20.105 3 19V5C3 3.895 3.895 3 5 3Z"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
              <path d="M7 3V9H15V3" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
              <path
                d="M8 21V14H16V21"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
          )}
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
