type Card = { title: string; image: string };

export default function DestinationStrip({ items }: { items: Card[] }) {
  return (
    <div className="mx-auto mt-10 max-w-6xl px-6">
      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        {items.map((c) => (
          <div
            key={c.title}
            className="relative h-24 overflow-hidden rounded-md md:h-28"
          >
            <img
              src={c.image}
              alt={c.title}
              className="h-full w-full object-cover"
              loading="lazy"
            />
            <div className="absolute inset-0 bg-black/35" />
            <div className="absolute bottom-3 left-3 text-sm font-semibold text-white">
              {c.title}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
