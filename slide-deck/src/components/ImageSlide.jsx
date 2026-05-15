export function ImageSlide({ content }) {
  return (
    <div className="flex-1 flex flex-col justify-center items-center animate-fade-in p-8 w-full">
      <div className="max-w-4xl w-full mx-auto flex flex-col items-center gap-6">
        {content.title && (
          <h1 className="text-3xl md:text-4xl font-bold text-white text-center">
            {content.title}
          </h1>
        )}
        <img
          src={content.src}
          alt={content.alt || content.title || ""}
          className="max-h-[60vh] max-w-full rounded-lg shadow-lg"
        />
        {content.credit && (
          <p className="text-sm text-gray-400 text-center">{content.credit}</p>
        )}
      </div>
    </div>
  );
}
