import { InlineMarkdown } from "./InlineMarkdown";

const THREE_COLORS = ["text-cyan-300", "text-purple-300", "text-green-300"];
const FOUR_COLORS = ["text-cyan-300", "text-amber-300", "text-purple-300", "text-green-300"];

export function ThreeWayComparison({ content }) {
  const { title, left, middle, right, columns } = content;
  const panels = columns ?? [left, middle, right];
  const colors = panels.length > 3 ? FOUR_COLORS : THREE_COLORS;

  return (
    <div className="flex-1 flex flex-col items-center justify-center p-8">
      <h2 className="text-4xl font-bold mb-8 text-slate-100">{title}</h2>

      <div
        className={`grid w-full ${
          panels.length > 3 ? "grid-cols-4 gap-4 max-w-7xl" : "grid-cols-3 gap-6 max-w-6xl"
        }`}
      >
        {panels.map((panel, i) => (
          <div key={panel.label} className="flex flex-col min-w-0">
            <div className="text-center mb-4">
              <h3 className={`font-bold ${panels.length > 3 ? "text-xl" : "text-2xl"} ${colors[i]}`}>
                {panel.label}
              </h3>
            </div>
            <div
              className={`flex-1 bg-slate-800 rounded-xl border border-slate-700 ${
                panels.length > 3 ? "p-4" : "p-6"
              }`}
            >
              {panel.items ? (
                <ul className="space-y-3">
                  {panel.items.map((item, itemIndex) => (
                    <li
                      key={itemIndex}
                      className="text-base text-gray-300 flex items-start gap-2"
                    >
                      <span className="text-secondary font-bold">→</span>
                      <span>
                        <InlineMarkdown text={item} />
                      </span>
                    </li>
                  ))}
                </ul>
              ) : (
                <pre className="text-sm text-slate-300 overflow-auto">
                  <code>{panel.code}</code>
                </pre>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
