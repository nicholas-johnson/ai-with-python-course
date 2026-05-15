import { InlineMarkdown } from "./InlineMarkdown";

const accentColors = [
  "border-t-cyan-400",
  "border-t-purple-400",
  "border-t-amber-400",
  "border-t-green-400",
  "border-t-rose-400",
  "border-t-sky-400",
];

export function CardsSlide({ content }) {
  return (
    <div className="flex-1 flex flex-col justify-center items-center animate-fade-in p-8 w-full">
      <div className="max-w-6xl w-full mx-auto flex flex-col items-center gap-6">
        <h1 className="text-3xl md:text-4xl font-bold text-white text-center">
          {content.title}
        </h1>
        <div
          className={`grid gap-5 w-full ${
            content.cards.length === 2
              ? "grid-cols-1 md:grid-cols-2"
              : content.cards.length === 3
                ? "grid-cols-1 md:grid-cols-3"
                : "grid-cols-1 md:grid-cols-2 lg:grid-cols-4"
          }`}
        >
          {content.cards.map((card, i) => (
            <div
              key={i}
              className={`bg-slate-800/60 rounded-xl p-5 border border-slate-700 border-t-4 ${
                accentColors[i % accentColors.length]
              }`}
            >
              <h3 className="text-xl font-bold text-white mb-3">
                {card.heading}
              </h3>
              <ul className="space-y-2">
                {card.points.map((point, j) => (
                  <li key={j} className="text-sm text-gray-300 leading-relaxed">
                    <InlineMarkdown text={point} />
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
