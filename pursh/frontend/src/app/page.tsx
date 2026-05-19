import Link from "next/link";

const CONDITIONS = [
  { name: "Hair Loss", icon: "💇", slug: "hair-loss" },
  { name: "Skin Care", icon: "✨", slug: "skin-care" },
  { name: "Mental Health", icon: "🧠", slug: "mental-health" },
  { name: "Sexual Health", icon: "❤️", slug: "sexual-health" },
  { name: "General Wellness", icon: "🌿", slug: "general-wellness" },
  { name: "Weight Management", icon: "⚖️", slug: "weight-management" },
];

export default function HomePage() {
  return (
    <main>
      {/* Hero */}
      <section className="bg-white py-20 px-4 text-center">
        <h1 className="text-5xl font-bold text-pursh-charcoal mb-4">
          Healthcare, simplified.
        </h1>
        <p className="text-xl text-pursh-muted mb-8 max-w-xl mx-auto">
          Connect with licensed clinicians online. Get personalized treatment
          plans delivered to your door.
        </p>
        <div className="flex gap-4 justify-center flex-wrap">
          <Link
            href="/symptoms"
            className="bg-pursh-green text-white px-8 py-3 rounded-full font-semibold hover:bg-pursh-green-light transition-colors"
          >
            Check Symptoms
          </Link>
          <Link
            href="/doctors"
            className="border-2 border-pursh-green text-pursh-green px-8 py-3 rounded-full font-semibold hover:bg-pursh-green hover:text-white transition-colors"
          >
            Browse Doctors
          </Link>
        </div>
      </section>

      {/* Conditions grid */}
      <section className="py-16 px-4 max-w-5xl mx-auto">
        <h2 className="text-3xl font-bold text-center mb-10">
          Conditions we treat
        </h2>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-6">
          {CONDITIONS.map((c) => (
            <Link
              key={c.slug}
              href={`/symptoms?category=${c.slug}`}
              className="bg-white rounded-2xl p-6 shadow-sm hover:shadow-md transition-shadow text-center border border-gray-100"
            >
              <div className="text-4xl mb-3">{c.icon}</div>
              <h3 className="font-semibold text-pursh-charcoal">{c.name}</h3>
            </Link>
          ))}
        </div>
      </section>

      {/* How it works */}
      <section className="bg-white py-16 px-4">
        <div className="max-w-4xl mx-auto">
          <h2 className="text-3xl font-bold text-center mb-12">
            How Pursh works
          </h2>
          <div className="grid md:grid-cols-3 gap-8 text-center">
            {[
              { step: "1", title: "Describe symptoms", desc: "Tell us what you're experiencing through our secure intake form." },
              { step: "2", title: "Match with a clinician", desc: "Our system routes you to the right specialist for your needs." },
              { step: "3", title: "Get a treatment plan", desc: "Receive personalized guidance, prescriptions, and follow-up care." },
            ].map((item) => (
              <div key={item.step}>
                <div className="w-12 h-12 rounded-full bg-pursh-green text-white flex items-center justify-center text-xl font-bold mx-auto mb-4">
                  {item.step}
                </div>
                <h3 className="font-semibold text-lg mb-2">{item.title}</h3>
                <p className="text-pursh-muted text-sm">{item.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Security badge — shows AISec scans this app */}
      <section className="py-8 px-4 text-center bg-gray-50">
        <p className="text-sm text-gray-500">
          🔒 This app is continuously scanned by{" "}
          <a href="https://aisec.aivistix.com" className="underline text-pursh-green">
            AISec
          </a>{" "}
          · SAST · DAST · SCA · Secrets · IaC · AI Security
        </p>
      </section>
    </main>
  );
}
