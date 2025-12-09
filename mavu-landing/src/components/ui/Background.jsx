export default function Background() {
  return (
    <div className="fixed inset-0 -z-10 overflow-hidden">
      {/* Grid pattern */}
      <div className="absolute inset-0 bg-grid opacity-50" />

      {/* Gradient blobs */}
      <div className="absolute top-0 -left-40 w-96 h-96 bg-violet-600/30 rounded-full blur-3xl animate-blob" />
      <div className="absolute top-1/3 -right-40 w-96 h-96 bg-pink-600/20 rounded-full blur-3xl animate-blob animation-delay-2000" />
      <div className="absolute bottom-0 left-1/3 w-96 h-96 bg-emerald-600/10 rounded-full blur-3xl animate-blob animation-delay-4000" />

      {/* Floating shapes */}
      <div className="absolute top-20 right-20 w-3 h-3 bg-violet-400/60 rounded-full animate-float" />
      <div className="absolute top-40 left-20 w-2 h-2 bg-pink-400/60 rounded-full animate-float-reverse" />
      <div className="absolute bottom-40 right-40 w-4 h-4 bg-emerald-400/40 rounded-full animate-float" />

      {/* Stars */}
      {[...Array(20)].map((_, i) => (
        <div
          key={i}
          className="absolute w-1 h-1 bg-white/30 rounded-full animate-twinkle"
          style={{
            top: `${Math.random() * 100}%`,
            left: `${Math.random() * 100}%`,
            animationDelay: `${Math.random() * 3}s`,
          }}
        />
      ))}

      {/* Orbiting element */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[300px] h-[300px] animate-orbit pointer-events-none opacity-20">
        <div className="absolute top-0 left-1/2 w-2 h-2 bg-violet-400 rounded-full" />
      </div>

      {/* Noise overlay */}
      <div className="noise" />
    </div>
  );
}
