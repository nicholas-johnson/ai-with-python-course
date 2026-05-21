import { SlideIcon } from "./SlideIcon";
import { InlineMarkdown } from "./InlineMarkdown";

export function DescriptionSlide({ content }) {
  return (
    <div className="flex-1 flex flex-col justify-center items-center animate-fade-in p-8 w-full">
      <div className="max-w-3xl w-full mx-auto text-center">
        {content.icon && (
          <div className="mb-6 flex justify-center text-white">
            <SlideIcon name={content.icon} size={48} />
          </div>
        )}
        <h1 className="text-4xl md:text-5xl font-bold text-white mb-8">
          {content.title}
        </h1>
        <p className="text-xl md:text-2xl text-gray-200 leading-relaxed">
          <InlineMarkdown text={content.description} />
        </p>
        {content.credit && (
          <p className="text-sm text-gray-400 text-center max-w-2xl mx-auto mt-6">
            {content.credit}
          </p>
        )}
      </div>
    </div>
  );
}
