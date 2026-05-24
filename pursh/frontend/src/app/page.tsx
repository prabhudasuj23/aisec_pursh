import Link from "next/link";

const CARE_AREAS = [
  {
    name: "Primary care",
    detail: "Digital-first intake, secure triage, and clinician matching.",
    accent: "from-pursh-teal to-pursh-aqua",
    active: true,
    href: "/symptoms",
  },
  {
    name: "Skin and hair",
    detail: "Private questionnaires for routine dermatology needs.",
    accent: "from-pursh-graphite to-pursh-teal",
    active: true,
    href: "/symptoms?category=skin-hair",
  },
  {
    name: "Weight care",
    detail: "Eligibility checks, goal tracking, and follow-up reminders.",
    accent: "from-pursh-aqua to-pursh-silver",
    active: false,
    href: "#",
  },
  {
    name: "Wellness labs",
    detail: "Structured lab review flows with privacy-first records.",
    accent: "from-pursh-charcoal to-pursh-graphite",
    active: false,
    href: "#",
  },
];

const CLINICIANS = [
  { name: "Dr. Aarav Mehta",  specialty: "Primary care",      initials: "AM" },
  { name: "Dr. Diya Raman",   specialty: "Dermatology",       initials: "DR" },
  { name: "Dr. Neel Iyer",    specialty: "Wellness",          initials: "NI" },
  { name: "Dr. Sana Kapoor",  specialty: "Care programs",     initials: "SK" },
  { name: "Dr. Rohan Shah",   specialty: "Preventive health", initials: "RS" },
];

const IMAGE_URLS = {
  hero: "https://images.unsplash.com/photo-1537368910025-700350fe46c7?auto=format&fit=crop&w=1100&q=80",
  care: "https://images.unsplash.com/photo-1576091160550-2173dba999ef?auto=format&fit=crop&w=1200&q=80",
  labs: "https://images.unsplash.com/photo-1581093458791-9d15482442f6?auto=format&fit=crop&w=1200&q=80",
};

const TRUST_BADGES = [
  "Board-certified",
  "48 hr response",
  "Private & secure",
  "No insurance needed",
];

export default function HomePage() {
  return (
    <main className="bg-pursh-silver text-pursh-charcoal">

      {/* ── 1. HERO ─────────────────────────────────────────────────── */}
      <section className="px-4 pb-10 pt-6 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-7xl">
          <div className="grid min-h-[660px] gap-5 lg:grid-cols-[1.05fr_0.95fr]">

            {/* Left — hero card */}
            <div className="relative overflow-hidden rounded-[2rem] bg-pursh-ink p-6 text-white shadow-xl sm:p-8 lg:p-10">
              <img
                src={IMAGE_URLS.hero}
                alt="Clinician ready for a virtual care consultation"
                className="absolute inset-0 h-full w-full object-cover opacity-40"
              />
              <div className="absolute inset-0 bg-gradient-to-br from-pursh-ink via-pursh-graphite/80 to-pursh-teal/70" />

              <div className="relative z-10 flex min-h-[600px] flex-col justify-between">
                <div className="max-w-2xl">
                  <p className="mb-5 inline-flex rounded-full border border-white/20 bg-white/10 px-4 py-2 text-xs font-semibold uppercase tracking-[0.18em] text-white backdrop-blur">
                    Now in early access
                  </p>
                  <h1 className="max-w-2xl text-5xl font-black leading-[0.95] tracking-tight sm:text-6xl lg:text-7xl">
                    Healthcare journeys designed for trust.
                  </h1>
                  <p className="mt-6 max-w-xl text-base leading-7 text-white/80 sm:text-lg">
                    Connect with board-certified clinicians online. Get
                    personalized care plans delivered quickly, privately, and
                    affordably.
                  </p>
                </div>

                <div>
                  <div className="mb-6 flex flex-col gap-3 sm:flex-row">
                    <Link
                      href="/symptoms"
                      className="inline-flex h-12 items-center justify-center rounded-full bg-white px-7 text-sm font-bold text-pursh-charcoal shadow-lg transition hover:bg-pursh-mint"
                    >
                      Start assessment
                    </Link>
                    <Link
                      href="/doctors"
                      className="inline-flex h-12 items-center justify-center rounded-full border border-white/40 px-7 text-sm font-bold text-white transition hover:bg-white/10"
                    >
                      Browse clinicians
                    </Link>
                  </div>
                  <div className="grid gap-2 text-xs font-semibold uppercase tracking-[0.15em] text-white/75 sm:grid-cols-4">
                    {TRUST_BADGES.map((item) => (
                      <span key={item} className="rounded-2xl bg-white/10 px-3 py-3 text-center backdrop-blur">
                        {item}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            </div>

            {/* Right — feature cards */}
            <div className="grid gap-5">
              <div className="rounded-[2rem] bg-white p-6 shadow-lg ring-1 ring-pursh-graphite/10">
                <div className="rounded-[1.5rem] bg-gradient-to-r from-pursh-teal via-pursh-aqua to-pursh-graphite p-[1px]">
                  <div className="rounded-[1.45rem] bg-white/95 p-6">
                    <p className="text-xs font-bold uppercase tracking-[0.2em] text-pursh-teal">
                      Digital care platform
                    </p>
                    <h2 className="mt-4 text-4xl font-black leading-tight text-pursh-ink sm:text-5xl">
                      Clean, secure, and distinctly Pursh.
                    </h2>
                    <p className="mt-4 max-w-md text-sm leading-6 text-pursh-slate">
                      A seamless patient experience — from your first symptom
                      check to an ongoing clinician relationship.
                    </p>
                  </div>
                </div>
                <div className="mt-5 grid grid-cols-2 gap-3">
                  <div className="rounded-[1.25rem] bg-pursh-mint p-4">
                    <p className="text-2xl font-black text-pursh-teal">500+</p>
                    <p className="mt-1 text-xs font-semibold uppercase tracking-[0.12em] text-pursh-graphite">
                      Licensed clinicians
                    </p>
                  </div>
                  <div className="rounded-[1.25rem] bg-pursh-charcoal p-4 text-white">
                    <p className="text-2xl font-black">24/7</p>
                    <p className="mt-1 text-xs font-semibold uppercase tracking-[0.12em] text-white/70">
                      Secure platform
                    </p>
                  </div>
                </div>
              </div>

              <div className="grid gap-5 sm:grid-cols-2">
                {CARE_AREAS.slice(0, 2).map((item) => (
                  <Link
                    key={item.name}
                    href={item.href}
                    className="group relative min-h-56 overflow-hidden rounded-[1.75rem] bg-white p-5 shadow-sm ring-1 ring-pursh-graphite/10 transition hover:-translate-y-0.5 hover:shadow-xl"
                  >
                    <div className={`mb-8 h-20 rounded-[1.35rem] bg-gradient-to-br ${item.accent}`} />
                    <p className="text-xs font-bold uppercase tracking-[0.18em] text-pursh-teal">
                      Available now
                    </p>
                    <h3 className="mt-2 text-2xl font-black text-pursh-ink">{item.name}</h3>
                    <p className="mt-3 text-sm leading-6 text-pursh-slate">{item.detail}</p>
                  </Link>
                ))}
              </div>
            </div>

          </div>
        </div>
      </section>

      {/* ── 2. CARE AREAS GRID ──────────────────────────────────────── */}
      <section className="bg-pursh-ink px-4 py-20 text-white sm:px-6 lg:px-8">
        <div className="mx-auto max-w-7xl">
          <div className="grid gap-10 lg:grid-cols-[0.8fr_1.2fr] lg:items-end">
            <div>
              <p className="text-xs font-bold uppercase tracking-[0.25em] text-pursh-aqua">
                Care categories
              </p>
              <h2 className="mt-4 text-4xl font-black leading-tight sm:text-5xl">
                The right care, for the right moment.
              </h2>
            </div>
            <p className="max-w-2xl text-base leading-7 text-white/70 lg:ml-auto">
              From routine primary care to specialist consultations — Pursh
              connects you with the right clinician quickly and privately,
              without a waiting room.
            </p>
          </div>

          <div className="mt-12 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
            {CARE_AREAS.map((item) => (
              <div key={item.name} className="relative">
                {item.active ? (
                  <Link
                    href={item.href}
                    className="group block rounded-[1.6rem] border border-white/10 bg-white/[0.07] p-4 transition hover:-translate-y-1 hover:bg-white/[0.12]"
                  >
                    <div className={`h-32 rounded-[1.25rem] bg-gradient-to-br ${item.accent}`} />
                    <h3 className="mt-5 text-xl font-black">{item.name}</h3>
                    <p className="mt-3 text-sm leading-6 text-white/70">{item.detail}</p>
                    <span className="mt-5 inline-flex text-sm font-bold text-pursh-aqua">
                      Start care →
                    </span>
                  </Link>
                ) : (
                  <div className="relative rounded-[1.6rem] border border-white/10 bg-white/[0.04] p-4 opacity-70 select-none cursor-default">
                    <div className={`h-32 rounded-[1.25rem] bg-gradient-to-br ${item.accent} opacity-40`} />
                    <h3 className="mt-5 text-xl font-black text-white/60">{item.name}</h3>
                    <p className="mt-3 text-sm leading-6 text-white/40">{item.detail}</p>
                    <span className="mt-5 inline-flex rounded-full border border-white/20 bg-white/10 px-3 py-1 text-xs font-bold uppercase tracking-widest text-white/50">
                      Coming soon
                    </span>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── 3. FEATURE SPLIT ────────────────────────────────────────── */}
      <section className="bg-white px-4 py-8 sm:px-6 lg:px-8">
        <div className="mx-auto grid max-w-7xl overflow-hidden rounded-[2rem] bg-pursh-mint shadow-lg ring-1 ring-pursh-graphite/10 lg:grid-cols-2">
          <div className="p-8 sm:p-10 lg:p-14">
            <p className="text-xs font-bold uppercase tracking-[0.25em] text-pursh-teal">
              Clinician-led workflows
            </p>
            <h2 className="mt-4 text-4xl font-black leading-tight text-pursh-ink sm:text-5xl">
              Better care journeys with clearer data.
            </h2>
            <p className="mt-5 text-base leading-7 text-pursh-slate">
              A premium care surface for symptom intake, treatment planning,
              and secure follow-up — all inside one account.
            </p>
            <div className="mt-10 grid gap-4 sm:grid-cols-2">
              {[
                { label: "Care records",    body: "Structured visit history with clinician notes." },
                { label: "Follow-up plans", body: "Personalised treatment guidance after every consult." },
              ].map((item) => (
                <div key={item.label} className="rounded-[1.25rem] bg-white/80 p-5 shadow-sm">
                  <p className="text-lg font-black text-pursh-ink">{item.label}</p>
                  <p className="mt-2 text-sm leading-6 text-pursh-slate">{item.body}</p>
                </div>
              ))}
            </div>
            <Link
              href="/symptoms"
              className="mt-8 inline-flex h-11 items-center rounded-full bg-pursh-teal px-7 text-sm font-bold text-white shadow-sm transition hover:bg-pursh-teal-deep"
            >
              Start your assessment
            </Link>
          </div>
          <div className="relative min-h-[400px] overflow-hidden lg:min-h-[520px]">
            <img
              src={IMAGE_URLS.care}
              alt="Clinician reviewing a digital care plan"
              className="absolute inset-0 h-full w-full object-cover"
            />
            <div className="absolute inset-0 bg-gradient-to-t from-pursh-ink/45 to-transparent" />
          </div>
        </div>
      </section>

      {/* ── 4. CLINICIANS ───────────────────────────────────────────── */}
      <section className="bg-white px-4 py-20 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-7xl">
          <div className="mx-auto max-w-2xl text-center">
            <p className="text-xs font-bold uppercase tracking-[0.25em] text-pursh-teal">
              Our care team
            </p>
            <h2 className="mt-4 text-4xl font-black leading-tight text-pursh-ink sm:text-5xl">
              Professional care, clearly presented.
            </h2>
            <p className="mt-5 text-sm leading-7 text-pursh-muted">
              Board-certified clinicians across primary care, dermatology,
              mental health, and preventive medicine.
            </p>
          </div>

          <div className="mt-12 grid gap-4 sm:grid-cols-3 lg:grid-cols-5">
            {CLINICIANS.map((doc, index) => (
              <div key={doc.name} className="rounded-[1.5rem] border border-pursh-graphite/10 bg-pursh-silver p-4">
                <div className={`flex h-24 items-center justify-center rounded-[1.15rem] text-2xl font-black ${
                  index % 2 === 0 ? "bg-pursh-mint text-pursh-teal" : "bg-pursh-charcoal text-white"
                }`}>
                  {doc.initials}
                </div>
                <h3 className="mt-4 text-sm font-black text-pursh-ink">{doc.name}</h3>
                <p className="mt-1 text-xs text-pursh-muted">{doc.specialty}</p>
              </div>
            ))}
          </div>

          <div className="mt-8 text-center">
            <Link href="/doctors" className="inline-flex h-10 items-center rounded-full border border-pursh-graphite/20 px-6 text-sm font-bold text-pursh-charcoal transition hover:border-pursh-teal hover:text-pursh-teal">
              View all clinicians
            </Link>
          </div>
        </div>
      </section>

      {/* ── 5. BOTTOM CTA ───────────────────────────────────────────── */}
      <section className="bg-gradient-to-r from-pursh-teal via-pursh-aqua to-pursh-graphite px-4 py-20 sm:px-6 lg:px-8">
        <div className="mx-auto grid max-w-7xl gap-5 lg:grid-cols-[0.9fr_1.1fr]">
          <div className="rounded-[2rem] bg-pursh-ink p-8 text-white shadow-xl sm:p-10">
            <p className="text-xs font-bold uppercase tracking-[0.25em] text-pursh-aqua">
              Get started today
            </p>
            <h2 className="mt-4 text-4xl font-black leading-tight">
              Total care.<br />Totally different.
            </h2>
            <p className="mt-4 text-sm leading-7 text-white/70">
              Create your free account in under a minute. No insurance,
              no waiting rooms, no hassle.
            </p>
            <div className="mt-8 flex flex-col gap-3 sm:flex-row">
              <Link
                href="/signup"
                className="inline-flex h-12 items-center justify-center rounded-full bg-white px-7 text-sm font-black text-pursh-ink transition hover:bg-pursh-mint"
              >
                Create free account
              </Link>
              <Link
                href="/symptoms"
                className="inline-flex h-12 items-center justify-center rounded-full border border-white/30 px-7 text-sm font-bold text-white transition hover:bg-white/10"
              >
                Try symptom check
              </Link>
            </div>
          </div>

          <div className="relative min-h-[360px] overflow-hidden rounded-[2rem] shadow-xl lg:min-h-[460px]">
            <img
              src={IMAGE_URLS.labs}
              alt="Secure healthcare analytics"
              className="absolute inset-0 h-full w-full object-cover"
            />
            <div className="absolute inset-0 bg-gradient-to-r from-pursh-ink/60 via-pursh-ink/10 to-transparent" />
          </div>
        </div>
      </section>

    </main>
  );
}
