import Link from "next/link";

const DOCTORS = [
  { id: "doctor-uuid-001", name: "Dr. Alex Chen", specialty: "General Practice", availability: "Mon–Fri 9am–5pm", emoji: "👨‍⚕️" },
  { id: "doctor-uuid-002", name: "Dr. Jordan Patel", specialty: "Dermatology", availability: "Tue–Thu 10am–4pm", emoji: "🧴" },
  { id: "doctor-uuid-003", name: "Dr. Morgan Lee", specialty: "Mental Health", availability: "Mon–Wed 8am–6pm", emoji: "🧠" },
  { id: "doctor-uuid-004", name: "Dr. Sam Rivera", specialty: "Hair Loss", availability: "Wed–Fri 9am–3pm", emoji: "💇" },
  { id: "doctor-uuid-005", name: "Dr. Taylor Kim", specialty: "Sexual Health", availability: "Mon–Thu 10am–6pm", emoji: "❤️" },
];

export default function DoctorsPage() {
  return (
    <main className="max-w-4xl mx-auto px-4 py-12">
      <h1 className="text-3xl font-bold mb-2">Our Clinicians</h1>
      <p className="text-pursh-muted mb-8">
        Synthetic profiles for security testing. Not real physicians.
      </p>

      <div className="grid md:grid-cols-2 gap-6">
        {DOCTORS.map((doc) => (
          <div key={doc.id} className="bg-white rounded-2xl p-6 border border-gray-100 shadow-sm">
            <div className="flex items-center gap-4 mb-4">
              <div className="w-14 h-14 rounded-full bg-pursh-cream flex items-center justify-center text-2xl">
                {doc.emoji}
              </div>
              <div>
                <h2 className="font-semibold text-lg">{doc.name} (Synthetic)</h2>
                <p className="text-pursh-green text-sm font-medium">{doc.specialty}</p>
              </div>
            </div>
            <p className="text-sm text-pursh-muted mb-4">🕐 {doc.availability}</p>
            <Link
              href={`/symptoms?doctor=${doc.id}`}
              className="block text-center bg-pursh-green text-white py-2 rounded-lg text-sm font-semibold hover:bg-pursh-green-light transition-colors"
            >
              Book appointment
            </Link>
          </div>
        ))}
      </div>
    </main>
  );
}
