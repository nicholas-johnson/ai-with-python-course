import { useEffect } from "react";
import { House } from "lucide-react";
import {
  BrowserRouter,
  Routes,
  Route,
  useParams,
  useNavigate,
  Navigate,
} from "react-router";
import {
  TitleSlide,
  StandardSlide,
  ComparisonSlide,
  CodeSlide,
  RulesSlide,
  WelcomeSlide,
  ModulesSlide,
  ThreeWayComparison,
  ImageSlide,
  EquationSlide,
  CardsSlide,
  DescriptionSlide,
} from "./components";

// Keep in sync with scripts/export-slides-pdf.mjs (SLIDE_WIDTH / SLIDE_HEIGHT).
const PRINT_WIDTH = 1920;
const PRINT_HEIGHT = 1080;

const PRINT_CSS = `
  @page { size: ${PRINT_WIDTH}px ${PRINT_HEIGHT}px; margin: 0; }
  html, body, #root {
    margin: 0;
    padding: 0;
    background: #0f172a;
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
  }
  .print-slide {
    width: ${PRINT_WIDTH}px;
    height: ${PRINT_HEIGHT}px;
    display: flex;
    flex-direction: column;
    background: #0f172a;
    color: #fff;
    overflow: hidden;
    break-after: page;
    break-inside: avoid;
    page-break-after: always;
    page-break-inside: avoid;
  }
  .print-slide:last-child {
    break-after: auto;
    page-break-after: auto;
  }
  .print-slide .animate-fade-in,
  .print-slide .animate-float {
    animation: none !important;
    opacity: 1 !important;
    transform: none !important;
  }
  .print-slide [class*="60vh"] {
    max-height: ${Math.round(PRINT_HEIGHT * 0.6)}px !important;
  }
`;

function SlideBody({ slide }) {
  if (slide.type === "custom" && slide.component) {
    const Component = slide.component;
    return <Component />;
  }

  switch (slide.type) {
    case "title":
      return <TitleSlide content={slide.content} />;
    case "comparison":
      return <ComparisonSlide content={slide.content} />;
    case "three-way":
      return <ThreeWayComparison content={slide.content} />;
    case "code":
      return <CodeSlide content={slide.content} />;
    case "rules":
      return <RulesSlide content={slide.content} />;
    case "welcome":
      return <WelcomeSlide content={slide.content} />;
    case "modules":
      return <ModulesSlide content={slide.content} />;
    case "image":
      return <ImageSlide content={slide.content} />;
    case "equation":
      return <EquationSlide content={slide.content} />;
    case "cards":
      return <CardsSlide content={slide.content} />;
    case "description":
      return <DescriptionSlide content={slide.content} />;
    default:
      return <StandardSlide content={slide.content} />;
  }
}

function SlideFooter({ children }) {
  return (
    <div className="flex justify-between items-center gap-8 p-4 bg-slate-950 border-t border-slate-800">
      {children}
    </div>
  );
}

function PrintDeck({ slides }) {
  return (
    <div id="print-deck" data-slide-count={slides.length}>
      <style>{PRINT_CSS}</style>
      {slides.map((slide, index) => (
        <section
          key={index}
          className="print-slide"
          aria-label={`Slide ${index + 1}`}
        >
          <SlideBody slide={slide} />
          <SlideFooter>
            <div className="w-10" aria-hidden="true" />
            <span className="text-lg text-gray-400 font-semibold min-w-[80px] text-center">
              {index + 1} / {slides.length}
            </span>
            <div className="w-10" aria-hidden="true" />
          </SlideFooter>
        </section>
      ))}
    </div>
  );
}

function SlideViewer({ slides }) {
  const { slideNumber } = useParams();
  const navigate = useNavigate();

  // Convert to 0-based index, default to slide 1
  const currentSlide = Math.max(
    0,
    Math.min(parseInt(slideNumber || "1", 10) - 1, slides.length - 1),
  );

  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === "ArrowRight" || e.key === " " || e.key === "Enter") {
        e.preventDefault();
        if (currentSlide < slides.length - 1) {
          navigate(`/${currentSlide + 2}`);
        }
      } else if (e.key === "ArrowLeft" || e.key === "Backspace") {
        e.preventDefault();
        if (currentSlide > 0) {
          navigate(`/${currentSlide}`);
        }
      } else if (e.key === "Home") {
        navigate("/1");
      } else if (e.key === "End") {
        navigate(`/${slides.length}`);
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [currentSlide, navigate, slides.length]);

  const slide = slides[currentSlide];

  return (
    <div className="w-screen h-screen flex flex-col bg-slate-900 text-white overflow-hidden">
      <SlideBody slide={slide} />

      <SlideFooter>
        <button
          onClick={() => navigate("/1")}
          className="p-2 text-slate-400 hover:text-slate-200 transition-colors rounded-lg"
          aria-label="Go to first slide"
        >
          <House className="w-5 h-5" />
        </button>
        <div className="flex items-center gap-8">
          <button
            onClick={() => navigate(`/${currentSlide}`)}
            disabled={currentSlide === 0}
            className="px-6 py-2 font-semibold rounded-lg bg-primary text-white transition-all hover:scale-105 disabled:opacity-30 disabled:cursor-not-allowed disabled:hover:scale-100"
          >
            ← Prev
          </button>
          <span className="text-lg text-gray-400 font-semibold min-w-[80px] text-center">
            {currentSlide + 1} / {slides.length}
          </span>
          <button
            onClick={() => navigate(`/${currentSlide + 2}`)}
            disabled={currentSlide === slides.length - 1}
            className="px-6 py-2 font-semibold rounded-lg bg-primary text-white transition-all hover:scale-105 disabled:opacity-30 disabled:cursor-not-allowed disabled:hover:scale-100"
          >
            Next →
          </button>
        </div>
        <div className="w-10" aria-hidden="true" />
      </SlideFooter>
    </div>
  );
}

export function SlideDeck({ slides }) {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/print" element={<PrintDeck slides={slides} />} />
        <Route path="/:slideNumber" element={<SlideViewer slides={slides} />} />
        <Route path="/" element={<Navigate to="/1" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
