import { redirect } from "next/navigation";
import Link from "next/link";
import { createClient } from "@/lib/supabase/server";

const CARDS = [
  {
    href: "/symptoms",
    icon: "🩺",
    iconBg: "bg-pursh-mint",
    title: "Check Symptoms",
    description: "Describe what you're feeling and get matched with the right specialist.",
  },
  {
    href: "/doctors",
    icon: "👨‍⚕️",
    iconBg: "bg-pursh-silver",
    title: "Browse Doctors",
    description: "View available clinicians and their specialties.",
  },
  {
    href: "/appointments",
    icon: "📅",
    iconBg: "bg-pursh-mint",
    title: "My Appointments",
    description: "View and manage your upcoming and past appointments.",
  },
  {
    href: "/profile",
    icon: "👤",
    iconBg: "bg-pursh-silver",
    title: "My Profile",
    description: "Update your health profile and preferences.",
  },
];

export default async function DashboardPage() {
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();

  if (!user) {
    redirect("/login");
  }

  return (
    <main className="max-w-5xl mx-auto px-4 py-14">
      {/* Header */}
      <div className="mb-10">
        <p className="text-pursh-muted text-sm mb-1">Good morning,</p>
        <h1 className="text-3xl font-bold text-pursh-charcoal">
          {user.email?.split("@")[0] ?? "Patient"}
        </h1>
        <div className="flex items-center gap-2 mt-2">
          <span className="text-xs text-pursh-muted">{user.email}</span>
          <span className="inline-block w-1 h-1 rounded-full bg-gray-300" />
          <span className="text-xs font-medium text-pursh-teal bg-pursh-mint px-2 py-0.5 rounded-full">
            Patient account
          </span>
        </div>
      </div>

      {/* Stats row */}
      <div className="grid grid-cols-3 gap-4 mb-10">
        {[
          { label: "Appointments", value: "0" },
          { label: "Messages", value: "0" },
          { label: "Prescriptions", value: "0" },
        ].map((s) => (
          <div key={s.label} className="bg-white rounded-2xl p-5 border border-gray-100 shadow-sm text-center">
            <p className="text-2xl font-bold text-pursh-charcoal">{s.value}</p>
            <p className="text-xs text-pursh-muted mt-1">{s.label}</p>
          </div>
        ))}
      </div>

      {/* Quick actions */}
      <h2 className="text-sm font-semibold text-pursh-muted uppercase tracking-wider mb-4">
        Quick actions
      </h2>
      <div className="grid md:grid-cols-2 gap-4">
        {CARDS.map((card) => (
          <Link
            key={card.href}
            href={card.href}
            className="bg-white rounded-2xl p-6 border border-gray-100 shadow-sm hover:shadow-md transition-shadow flex gap-4 items-start group"
          >
            <div className={`w-12 h-12 rounded-xl ${card.iconBg} flex items-center justify-center text-2xl flex-shrink-0 group-hover:scale-105 transition-transform`}>
              {card.icon}
            </div>
            <div>
              <h3 className="font-semibold text-pursh-charcoal text-base">{card.title}</h3>
              <p className="text-pursh-muted text-sm mt-1 leading-relaxed">{card.description}</p>
            </div>
          </Link>
        ))}
      </div>

      {/* Disclaimer */}
      <div className="mt-8 bg-pursh-mint border border-pursh-teal/20 rounded-2xl p-4 text-sm text-pursh-graphite">
        <strong>Reminder:</strong> This is a demonstration project. All health data shown is
        synthetic. Do not enter real medical information.
      </div>
    </main>
  );
}
