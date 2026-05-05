import Link from 'next/link'

export function Navbar() {
  return (
    <nav className="border-b border-white/10 bg-dark-900">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3">
        <Link href="/" className="text-xl font-black tracking-tight text-white">
          HUT<span className="text-brand-500">BIN</span>
        </Link>
        <div className="flex items-center gap-6 text-sm font-medium text-gray-400">
          <Link href="/cards" className="hover:text-white transition-colors">Cards</Link>
          <Link href="/players" className="hover:text-white transition-colors">Players</Link>
          <Link href="/login" className="rounded-md bg-brand-600 px-4 py-1.5 text-white hover:bg-brand-500 transition-colors">
            Sign In
          </Link>
        </div>
      </div>
    </nav>
  )
}
