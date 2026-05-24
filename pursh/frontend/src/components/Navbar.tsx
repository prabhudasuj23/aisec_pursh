import Link from "next/link";

export default function Navbar() {
  return (
    <nav className="sticky top-0 z-50 border-b border-pursh-graphite/10 bg-white/90 backdrop-blur">
      <div className="mx-auto flex h-14 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">

        {/* Logo */}
        <Link href="/" className="flex items-center gap-2.5" aria-label="Pursh home">
          <span className="flex h-8 w-8 items-center justify-center rounded-2xl bg-gradient-to-br from-pursh-teal to-pursh-graphite text-sm font-black text-white shadow-sm">
            P
          </span>
          <span className="text-xl font-black tracking-tight text-pursh-charcoal">Pursh</span>
        </Link>

        {/* Center nav — public pages only */}
        <div className="hidden items-center gap-7 text-sm font-semibold md:flex">
          <Link href="/symptoms" className="text-pursh-slate transition-colors hover:text-pursh-teal">
            Symptom Checker
          </Link>
          <Link href="/doctors" className="text-pursh-slate transition-colors hover:text-pursh-teal">
            Doctors
          </Link>
        </div>

        {/* Auth */}
        <div className="flex items-center gap-3">
          <Link
            href="/login"
            className="hidden text-sm font-semibold text-pursh-charcoal transition-colors hover:text-pursh-teal md:block"
          >
            Sign in
          </Link>
          <Link
            href="/signup"
            className="inline-flex h-9 items-center rounded-full bg-pursh-teal px-5 text-sm font-bold text-white shadow-sm transition-colors hover:bg-pursh-teal-deep"
          >
            Get started
          </Link>
        </div>

      </div>
    </nav>
  );
}
