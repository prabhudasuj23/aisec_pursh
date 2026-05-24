"use client";

import { Suspense, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { Doctor, DoctorsApiResponse } from "@/lib/types/doctor";
import { PURSH_SPECIALTIES, normalizeSpecialty } from "@/lib/specialty-map";

const AVATAR_COMBOS = [
  "bg-pursh-teal text-white",
  "bg-pursh-graphite text-white",
  "bg-pursh-aqua text-pursh-charcoal",
  "bg-pursh-mint text-pursh-charcoal",
];

function avatarClass(id: string): string {
  let hash = 0;
  for (let i = 0; i < id.length; i++) hash = (hash * 31 + id.charCodeAt(i)) | 0;
  return AVATAR_COMBOS[Math.abs(hash) % AVATAR_COMBOS.length];
}

function SkeletonCard() {
  return (
    <div className="bg-white rounded-2xl border border-pursh-graphite/10 p-5 animate-pulse">
      <div className="flex items-center gap-4 mb-4">
        <div className="w-12 h-12 rounded-full bg-pursh-silver" />
        <div className="flex-1 space-y-2">
          <div className="h-4 bg-pursh-silver rounded w-3/4" />
          <div className="h-3 bg-pursh-silver rounded w-1/2" />
        </div>
      </div>
      <div className="space-y-2">
        <div className="h-3 bg-pursh-silver rounded" />
        <div className="h-3 bg-pursh-silver rounded w-5/6" />
        <div className="h-3 bg-pursh-silver rounded w-4/6" />
      </div>
      <div className="mt-4 flex gap-2">
        <div className="flex-1 h-9 bg-pursh-silver rounded-full" />
        <div className="h-9 w-20 bg-pursh-silver rounded-full" />
      </div>
    </div>
  );
}

function DoctorCard({ doctor }: { doctor: Doctor }) {
  const [showModal, setShowModal] = useState(false);

  return (
    <>
      <div className="bg-white rounded-2xl border border-pursh-graphite/10 p-5 flex flex-col gap-4 hover:shadow-md transition-shadow">
        <div className="flex items-center gap-4">
          <div
            className={`w-12 h-12 rounded-full flex items-center justify-center text-sm font-black shrink-0 ${avatarClass(doctor.id)}`}
          >
            {doctor.initials}
          </div>
          <div className="min-w-0">
            <p className="font-bold text-pursh-charcoal truncate">{doctor.name}</p>
            <span className="inline-block mt-0.5 text-xs font-semibold bg-pursh-mint text-pursh-teal px-2 py-0.5 rounded-full">
              {doctor.specialty}
            </span>
          </div>
        </div>

        <div className="text-sm text-pursh-slate space-y-1">
          {doctor.hospital && (
            <p className="flex gap-2">
              <span>🏥</span>
              <span className="truncate">{doctor.hospital}</span>
            </p>
          )}
          {(doctor.city || doctor.state) && (
            <p className="flex gap-2">
              <span>📍</span>
              <span>{[doctor.city, doctor.state].filter(Boolean).join(", ")}</span>
            </p>
          )}
          {doctor.qualification && (
            <p className="flex gap-2">
              <span>🎓</span>
              <span>{doctor.qualification}</span>
            </p>
          )}
          {doctor.nmcRegNo && (
            <p className="flex gap-2">
              <span>🪪</span>
              <span className="font-mono text-xs">{doctor.nmcRegNo}</span>
            </p>
          )}
        </div>

        <div className="flex gap-2 mt-auto">
          <button
            onClick={() => setShowModal(true)}
            className="flex-1 bg-pursh-teal text-white text-sm font-bold py-2 rounded-full hover:bg-pursh-teal-deep transition-colors"
          >
            Book appointment
          </button>
          <a
            href="https://www.nmc.org.in/information-desk/indian-medical-register/"
            target="_blank"
            rel="noopener noreferrer"
            className="px-4 text-sm font-bold text-pursh-teal border border-pursh-teal py-2 rounded-full hover:bg-pursh-mint transition-colors"
          >
            Verify ↗
          </a>
        </div>
      </div>

      {showModal && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4"
          onClick={() => setShowModal(false)}
        >
          <div
            className="bg-white rounded-2xl p-8 max-w-sm w-full shadow-xl"
            onClick={(e) => e.stopPropagation()}
          >
            <p className="text-2xl mb-2">🗓️</p>
            <h3 className="text-xl font-black text-pursh-charcoal mb-2">Coming soon</h3>
            <p className="text-pursh-slate text-sm mb-6">
              Online booking is on the way. In the meantime, use the Symptom Checker to
              find the right care for your needs.
            </p>
            <div className="flex gap-3">
              <a
                href="/symptoms"
                className="flex-1 text-center bg-pursh-teal text-white py-2.5 rounded-full text-sm font-bold hover:bg-pursh-teal-deep transition-colors"
              >
                Symptom Checker
              </a>
              <button
                onClick={() => setShowModal(false)}
                className="flex-1 border border-pursh-graphite/20 text-pursh-charcoal py-2.5 rounded-full text-sm font-bold hover:border-pursh-teal hover:text-pursh-teal transition-colors"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}

function DoctorsContent() {
  const searchParams = useSearchParams();
  const rawSpecialty = searchParams.get("specialty") ?? "";
  const [activeFilter, setActiveFilter] = useState<string>(
    rawSpecialty ? normalizeSpecialty(rawSpecialty) : "General Practice"
  );
  const [doctors, setDoctors] = useState<Doctor[]>([]);
  const [source, setSource] = useState<"nmc" | "static" | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    fetch(`/api/doctors?specialty=${encodeURIComponent(activeFilter)}`)
      .then((r) => {
        if (!r.ok) throw new Error("Failed to load doctors");
        return r.json() as Promise<DoctorsApiResponse>;
      })
      .then((data) => {
        if (!cancelled) {
          setDoctors(data.doctors);
          setSource(data.source);
        }
      })
      .catch(() => { if (!cancelled) setError("Could not load doctors. Please try again."); })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [activeFilter]);

  return (
    <main className="min-h-screen bg-pursh-silver">
      <div className="bg-pursh-charcoal text-white py-14 px-4">
        <div className="mx-auto max-w-4xl text-center">
          <h1 className="text-4xl sm:text-5xl font-black tracking-tight mb-4">
            Find your doctor
          </h1>
          <p className="text-pursh-aqua text-lg">
            NMC-registered clinicians across India
          </p>
        </div>
      </div>

      <div className="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8 py-10">
        <div className="flex flex-wrap gap-2 mb-3">
          {PURSH_SPECIALTIES.map((s) => (
            <button
              key={s}
              onClick={() => setActiveFilter(s)}
              className={`px-4 py-1.5 rounded-full text-sm font-semibold transition-colors ${
                activeFilter === s
                  ? "bg-pursh-teal text-white"
                  : "bg-white text-pursh-slate border border-pursh-graphite/15 hover:border-pursh-teal hover:text-pursh-teal"
              }`}
            >
              {s}
            </button>
          ))}
        </div>

        {source && !loading && (
          <p className="text-xs text-pursh-muted mb-6">
            {source === "nmc"
              ? "Data sourced from the National Medical Commission (NMC) Indian Medical Register."
              : "Showing curated NMC-registered clinicians. Live data temporarily unavailable."}
          </p>
        )}

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-xl p-4 mb-6 flex items-center justify-between">
            <span className="text-red-700 text-sm">{error}</span>
            <button
              onClick={() => setActiveFilter(activeFilter + " ")}
              className="text-sm font-bold text-red-700 underline ml-4"
            >
              Retry
            </button>
          </div>
        )}

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
          {loading
            ? Array.from({ length: 6 }).map((_, i) => <SkeletonCard key={i} />)
            : doctors.length > 0
            ? doctors.map((d) => <DoctorCard key={d.id} doctor={d} />)
            : !error && (
                <div className="col-span-full text-center py-16 text-pursh-muted">
                  No doctors found for this specialty.
                </div>
              )}
        </div>
      </div>
    </main>
  );
}

export default function DoctorsPage() {
  return (
    <Suspense
      fallback={
        <main className="min-h-screen bg-pursh-silver">
          <div className="bg-pursh-charcoal text-white py-14 px-4">
            <div className="mx-auto max-w-4xl text-center">
              <h1 className="text-4xl sm:text-5xl font-black tracking-tight mb-4">
                Find your doctor
              </h1>
              <p className="text-pursh-aqua text-lg">NMC-registered clinicians across India</p>
            </div>
          </div>
          <div className="mx-auto max-w-6xl px-4 py-10">
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
              {Array.from({ length: 6 }).map((_, i) => (
                <div key={i} className="bg-white rounded-2xl border border-pursh-graphite/10 p-5 animate-pulse">
                  <div className="flex items-center gap-4 mb-4">
                    <div className="w-12 h-12 rounded-full bg-pursh-silver" />
                    <div className="flex-1 space-y-2">
                      <div className="h-4 bg-pursh-silver rounded w-3/4" />
                      <div className="h-3 bg-pursh-silver rounded w-1/2" />
                    </div>
                  </div>
                  <div className="space-y-2">
                    <div className="h-3 bg-pursh-silver rounded" />
                    <div className="h-3 bg-pursh-silver rounded w-5/6" />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </main>
      }
    >
      <DoctorsContent />
    </Suspense>
  );
}
