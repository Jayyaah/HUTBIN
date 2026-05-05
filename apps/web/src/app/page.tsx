import Link from 'next/link'

export default function HomePage() {
  return (
    <div className="flex flex-col items-center justify-center py-20 text-center">
      <h1 className="text-5xl font-black tracking-tight">
        HUT<span className="text-brand-500">BIN</span>
      </h1>
      <p className="mt-4 text-lg text-gray-400 max-w-md">
        Community-driven NHL 26 HUT player database — stats, cards, and live prices.
      </p>
      <div className="mt-8 flex gap-4">
        <Link href="/cards" className="rounded-lg bg-brand-600 px-6 py-3 font-semibold hover:bg-brand-500 transition-colors">
          Browse Cards
        </Link>
        <Link href="/players" className="rounded-lg border border-white/20 px-6 py-3 font-semibold hover:border-white/40 transition-colors">
          Players
        </Link>
      </div>
    </div>
  )
}
