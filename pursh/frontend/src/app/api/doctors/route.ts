import { NextRequest, NextResponse } from "next/server";
import fs from "fs";
import path from "path";
import { Doctor, DoctorsApiResponse } from "@/lib/types/doctor";
import { SPECIALTY_TO_NMC, normalizeSpecialty } from "@/lib/specialty-map";

function initials(name: string): string {
  return name
    .replace(/^Dr\.\s*/i, "")
    .split(" ")
    .filter(Boolean)
    .slice(0, 2)
    .map((w) => w[0].toUpperCase())
    .join("");
}

function nmcRecordToDoctor(r: Record<string, string>, specialty: string): Doctor {
  const fullName = `Dr. ${r.doctorName ?? r.name ?? "Unknown"}`;
  return {
    id: `nmc-${r.registrationNo ?? r.regNo ?? Math.random()}`,
    name: fullName,
    initials: initials(fullName),
    specialty: normalizeSpecialty(specialty),
    nmcSpecialty: r.specialization ?? r.broadSpeciality ?? specialty,
    nmcRegNo: r.registrationNo ?? r.regNo ?? "",
    qualification: r.qualification ?? r.degree ?? "MBBS",
    hospital: r.hospitalName ?? r.college ?? "",
    city: r.city ?? r.district ?? "",
    state: r.stateMedicalCouncil ?? r.state ?? "",
    source: "nmc",
  };
}

function loadStaticDoctors(): Doctor[] {
  const filePath = path.join(process.cwd(), "public", "data", "doctors.json");
  const raw = fs.readFileSync(filePath, "utf-8");
  return JSON.parse(raw) as Doctor[];
}

function filterStatic(
  doctors: Doctor[],
  specialty: string,
  city?: string,
  q?: string
): Doctor[] {
  const normalised = normalizeSpecialty(specialty);
  return doctors.filter((d) => {
    if (d.specialty !== normalised) return false;
    if (city && !d.city.toLowerCase().includes(city.toLowerCase())) return false;
    if (q) {
      const search = q.toLowerCase();
      if (
        !d.name.toLowerCase().includes(search) &&
        !d.hospital.toLowerCase().includes(search)
      )
        return false;
    }
    return true;
  });
}

export async function GET(req: NextRequest): Promise<NextResponse<DoctorsApiResponse>> {
  const { searchParams } = req.nextUrl;
  const specialty = searchParams.get("specialty") ?? "General Practice";
  const city = searchParams.get("city") ?? undefined;
  const q = searchParams.get("q") ?? undefined;

  const nmcKeywords = SPECIALTY_TO_NMC[normalizeSpecialty(specialty)] ?? [
    "GENERAL MEDICINE",
  ];
  const firstKeyword = nmcKeywords[0];

  try {
    const body = new URLSearchParams({
      page: "1",
      size: "20",
      specialization: firstKeyword,
      name: q ?? "",
      smcId: "",
      registrationNo: "",
      typeOfDoctor: "",
      gender: "",
      country: "",
      state: "",
      district: city ?? "",
      collegeName: "",
      universityName: "",
      qualification: "",
      year: "",
    });

    const res = await fetch(
      "https://www.nmc.org.in/MCIRest/open/getDataFromService?service=searchDoctor",
      {
        method: "POST",
        headers: {
          "Content-Type": "application/x-www-form-urlencoded",
          "User-Agent": "Mozilla/5.0 (compatible; Pursh-demo/1.0)",
          Accept: "application/json",
        },
        body: body.toString(),
        signal: AbortSignal.timeout(5000),
      }
    );

    if (res.ok) {
      const data = await res.json();
      const records: Record<string, string>[] = Array.isArray(data)
        ? data
        : data?.data ?? data?.result ?? [];

      if (records.length > 0) {
        const doctors = records.map((r) => nmcRecordToDoctor(r, firstKeyword));
        return NextResponse.json(
          { doctors, total: doctors.length, source: "nmc" },
          {
            headers: {
              "Cache-Control": "public, s-maxage=300, stale-while-revalidate=600",
            },
          }
        );
      }
    }
  } catch {
    // NMC unreachable — fall through to static
  }

  const all = loadStaticDoctors();
  const doctors = filterStatic(all, specialty, city, q);
  return NextResponse.json(
    { doctors, total: doctors.length, source: "static" },
    {
      headers: {
        "Cache-Control": "public, s-maxage=300, stale-while-revalidate=600",
      },
    }
  );
}
