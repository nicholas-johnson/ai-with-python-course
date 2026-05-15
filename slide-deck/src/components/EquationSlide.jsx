export function EquationSlide({ content }) {
  return (
    <div className="flex-1 flex flex-col justify-center items-center animate-fade-in p-8 w-full">
      <div className="max-w-4xl w-full mx-auto flex flex-col items-center gap-6">
        {content.title && (
          <h1 className="text-3xl md:text-4xl font-bold text-white text-center">
            {content.title}
          </h1>
        )}
        <div
          className="text-white text-3xl md:text-4xl py-8"
          dangerouslySetInnerHTML={{ __html: content.mathml }}
        />
        {content.description && (
          <p className="text-lg text-gray-300 text-center max-w-2xl">
            {content.description}
          </p>
        )}
        {content.credit && (
          <p className="text-sm text-gray-400 text-center">{content.credit}</p>
        )}
      </div>
    </div>
  );
}
