import { redirect } from "next/navigation";
import Link from "next/link";
import { createClient } from "@/lib/supabase/server";

export default async function DashboardPage() {
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();

  if (!user) {
    redirect("/login");
  }

  return (
    <main className="max-w-4xl mx-auto px-4 py-12">
      <div className="mb-8">
        <h1 className="text-3xl font-bold">Welcome back</h1>
        <p className="text-pursh-muted mt-1">
          {user.email} · <span className="text-pursh-green">Patient account</span>
        </p>
      </div>

      <div className="grid md:grid-cols-2 gap-6">
        <DashboardCard
          href="/symptoms"
          icon="🩺"
          title="Check Symptoms"
          description="Describe what you're feeling and get matched with the right specialist."
        />
        <DashboardCard
          href="/doctors"
          icon="👨‍⚕️"
          title="Browse Doctors"
          description="View available clinicians and their specialties."
        />
        <DashboardCard
          href="/appointments"
          icon="📅"
          title="My Appointments"
          description="View and manage your upcoming and past appointments."
        />
        <DashboardCard
          href="/profile"
          icon="👤"
          title="My Profile"
          description="Update your health profile and preferences."
        />
      </div>

      <div className="mt-8 bg-amber-50 border border-amber-200 rounded-xl p-4 text-sm text-amber-800">
        <strong>Reminder:</strong> This is a demonstration project. All health data shown is
        synthetic. Do not enter real medical information.
      </div>
    </main>
  );
}

function DashboardCard({
  href,
  icon,
  title,
  description,
}: {
  href: string;
  icon: string;
  title: string;
  description: string;
}) {
  return (
    <Link
      href={href}
      className="bg-white rounded-2xl p-6 border border-gray-100 shadow-sm hover:shadow-md transition-shadow flex gap-4 items-start"
    >
      <span className="text-3xl">{icon}</span>
      <div>
        <h2 className="font-semibold text-lg">{title}</h2>
        <p className="text-pursh-muted text-sm mt-1">{description}</p>
      </div>
    </Link>
  );
}
