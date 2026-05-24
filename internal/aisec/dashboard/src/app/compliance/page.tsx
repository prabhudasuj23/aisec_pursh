import Navbar from "@/components/Navbar";

// ── OWASP Top 10 (2021) — scanner coverage ────────────────────────────────────
const OWASP = [
  { id: "A01:2021", name: "Broken Access Control",      scanners: ["semgrep", "zap", "prowler", "iam-access-analyzer"] },
  { id: "A02:2021", name: "Cryptographic Failures",     scanners: ["semgrep", "trivy-sca", "checkov", "tfsec", "prowler"] },
  { id: "A03:2021", name: "Injection",                  scanners: ["semgrep", "zap"] },
  { id: "A04:2021", name: "Insecure Design",            scanners: ["semgrep", "zap"] },
  { id: "A05:2021", name: "Security Misconfiguration",  scanners: ["checkov", "tfsec", "semgrep", "prowler", "scoutsuite"] },
  { id: "A06:2021", name: "Vulnerable Components",      scanners: ["trivy-sca", "grype", "syft", "detect-secrets"] },
  { id: "A07:2021", name: "Auth Failures",              scanners: ["semgrep", "gitleaks", "detect-secrets", "iam-access-analyzer"] },
  { id: "A08:2021", name: "Integrity Failures",         scanners: ["grype", "syft", "checkov"] },
  { id: "A09:2021", name: "Security Logging Failures",  scanners: ["semgrep", "prowler", "guardduty"] },
  { id: "A10:2021", name: "SSRF",                       scanners: ["semgrep", "zap"] },
];

// ── OWASP LLM Top 10 (2025) — AI scanner coverage ────────────────────────────
const OWASP_LLM = [
  { id: "LLM01", name: "Prompt Injection",          scanners: ["promptfoo", "garak"],             pursh: "Symptom field injection tests" },
  { id: "LLM02", name: "Insecure Output Handling",  scanners: ["promptfoo"],                      pursh: "Output rendered as plain text, never HTML" },
  { id: "LLM04", name: "Model DoS",                 scanners: ["promptfoo"],                      pursh: "Token caps, rate limits, timeout enforced" },
  { id: "LLM05", name: "Supply Chain",              scanners: ["syft", "grype"],                  pursh: "SBOM tracks LLM SDK + pinned versions" },
  { id: "LLM06", name: "Sensitive Info Disclosure", scanners: ["promptfoo", "garak"],             pursh: "PHI redaction layer before every LLM call" },
  { id: "LLM08", name: "Excessive Agency",          scanners: ["promptfoo"],                      pursh: "LLM has zero write access to DB or actions" },
  { id: "LLM09", name: "Overreliance",              scanners: ["promptfoo"],                      pursh: '"Not medical advice" disclaimer on every page' },
  { id: "LLM10", name: "Model Theft",               scanners: ["iam-access-analyzer", "prowler"], pursh: "API keys in Secrets Manager; CloudTrail on access" },
];

// ── HIPAA Security Rule ────────────────────────────────────────────────────────
const HIPAA = [
  { section: "§164.312(a)(1)", name: "Access Control",         scanners: ["iam-access-analyzer", "prowler"], controls: ["Supabase RLS", "FastAPI RBAC"] },
  { section: "§164.312(a)(2)(i)",  name: "Unique User ID",     scanners: ["semgrep"],                        controls: ["Supabase Auth UUIDs", "no shared accounts"] },
  { section: "§164.312(a)(2)(iii)", name: "Auto Logoff",       scanners: ["semgrep", "zap"],                 controls: ["Session timeout 15 min", "refresh-token rotation"] },
  { section: "§164.312(a)(2)(iv)", name: "Encryption",         scanners: ["checkov", "tfsec", "prowler"],    controls: ["AES-256 at rest", "KMS CMK"] },
  { section: "§164.312(b)",        name: "Audit Controls",     scanners: ["semgrep", "guardduty"],           controls: ["audit_log table", "structured logging"] },
  { section: "§164.312(c)(1)",     name: "Integrity",          scanners: ["grype", "syft"],                  controls: ["file checksums", "signatures"] },
  { section: "§164.312(d)",        name: "Authentication",     scanners: ["semgrep", "zap"],                 controls: ["MFA", "OIDC tokens"] },
  { section: "§164.312(e)(1)",     name: "Transmission Security", scanners: ["zap", "checkov"],             controls: ["TLS 1.3", "HSTS"] },
];

// ── GDPR Article 32 ───────────────────────────────────────────────────────────
const GDPR = [
  { article: "Art32(1)(a)", name: "Pseudonymization & Encryption", scanners: ["checkov", "tfsec", "prowler"], controls: ["AES-256", "KMS CMK"] },
  { article: "Art32(1)(b)", name: "Confidentiality & Integrity",   scanners: ["zap", "semgrep", "guardduty"], controls: ["TLS", "audit logs", "RLS"] },
  { article: "Art32(1)(c)", name: "Availability & Resilience",     scanners: ["checkov", "prowler"],          controls: ["RDS PITR", "S3 versioning"] },
  { article: "Art32(1)(d)", name: "Regular Testing & Evaluation",  scanners: ["semgrep", "zap", "trivy-sca", "promptfoo"], controls: ["Monthly tabletops", "DAST scans"] },
];

// ── PCI-DSS v4.0 ──────────────────────────────────────────────────────────────
const PCI = [
  { req: "Req 2",    name: "Secure Configurations",         scanners: ["checkov", "tfsec", "prowler"],              controls: ["CIS hardening", "Lynis audit"] },
  { req: "Req 3",    name: "Protect Stored Account Data",   scanners: ["checkov", "macie"],                         controls: ["AES-256", "KMS CMK", "no raw PANs stored"] },
  { req: "Req 4",    name: "Protect Data in Transit",       scanners: ["zap", "checkov"],                           controls: ["TLS 1.3", "HSTS"] },
  { req: "Req 6.3.3", name: "Patch Vulnerable Components", scanners: ["trivy-sca", "grype", "syft"],               controls: ["Dependency-Track policy", "CVE gating"] },
  { req: "Req 6.4",  name: "Web App Protection (WAF)",      scanners: ["zap", "semgrep"],                           controls: ["ModSecurity + OWASP CRS", "ZAP DAST gate"] },
  { req: "Req 7",    name: "Restrict Access by Need",       scanners: ["iam-access-analyzer", "prowler"],           controls: ["Supabase RLS", "ECS task roles"] },
  { req: "Req 8",    name: "Identify & Authenticate Users", scanners: ["semgrep", "zap"],                           controls: ["MFA required", "OIDC short-TTL tokens"] },
  { req: "Req 10",   name: "Log & Monitor All Access",      scanners: ["guardduty", "prowler"],                     controls: ["audit_log table", "CloudTrail", "Wazuh"] },
  { req: "Req 11.3", name: "Vulnerability Scanning",        scanners: ["trivy-sca", "grype", "semgrep", "zap"],     controls: ["DefectDojo SLA tracking", "quarterly OpenVAS"] },
  { req: "Req 11.4", name: "Penetration Testing",           scanners: ["zap", "semgrep"],                           controls: ["ZAP DAST", "Nuclei", "manual Kali testing"] },
  { req: "Req 12.10", name: "Incident Response Plan",       scanners: ["guardduty"],                                controls: ["15 IR runbooks", "monthly tabletops"] },
];

// ── NIST CSF 2.0 ──────────────────────────────────────────────────────────────
const NIST = [
  { fn: "GV", id: "GV.SC-01", name: "Supply Chain Risk",      scanners: ["syft", "grype", "trivy-sca"],            controls: ["SBOM per build", "Dependency-Track policy"] },
  { fn: "ID", id: "ID.AM-02", name: "Software Inventory",     scanners: ["syft", "trivy-sca"],                     controls: ["CycloneDX SBOMs in S3"] },
  { fn: "ID", id: "ID.RA-01", name: "Vulnerabilities Identified", scanners: ["semgrep", "trivy-sca", "grype", "zap"], controls: ["DefectDojo aggregation"] },
  { fn: "PR", id: "PR.AA-05", name: "Least Privilege",        scanners: ["iam-access-analyzer", "prowler"],        controls: ["ECS task roles", "Supabase RLS"] },
  { fn: "PR", id: "PR.DS-10", name: "Sensitive Data",         scanners: ["gitleaks", "detect-secrets", "macie"],   controls: ["Gitleaks pre-commit", "Macie S3 scan"] },
  { fn: "PR", id: "PR.PS-01", name: "Secure Config",          scanners: ["checkov", "tfsec", "prowler", "scoutsuite"], controls: ["Terraform IaC gates", "CIS benchmarks"] },
  { fn: "PR", id: "PR.PS-04", name: "Secure Development",     scanners: ["semgrep", "zap", "gitleaks"],            controls: ["SAST + DAST on every PR"] },
  { fn: "DE", id: "DE.CM-01", name: "Network Monitoring",     scanners: ["guardduty"],                             controls: ["GuardDuty VPC flow", "Suricata (homelab)"] },
  { fn: "DE", id: "DE.AE-02", name: "Adverse Events Detected", scanners: ["guardduty", "semgrep", "zap"],         controls: ["Wazuh alerts", "Sigma rules"] },
  { fn: "RS", id: "RS.MA-01", name: "Response Plan Executed", scanners: ["guardduty"],                             controls: ["NIST 800-61 runbooks", "TheHive cases"] },
];

// ── SOC 2 Trust Services Criteria ─────────────────────────────────────────────
const SOC2 = [
  { cc: "CC6.1", name: "Logical Access Restrictions",   scanners: ["iam-access-analyzer", "prowler"],         controls: ["Supabase RLS", "OIDC RBAC"] },
  { cc: "CC6.6", name: "External Access Restricted",    scanners: ["checkov", "tfsec", "prowler"],            controls: ["VPC private subnets", "ALB-only ingress"] },
  { cc: "CC6.8", name: "Malware Prevention",            scanners: ["trivy-image", "gitleaks", "detect-secrets"], controls: ["Trivy image gate", "Gitleaks CI"] },
  { cc: "CC7.1", name: "Config Changes Detected",       scanners: ["checkov", "tfsec"],                       controls: ["Wazuh FIM", "AWS Config drift"] },
  { cc: "CC7.2", name: "Anomalous Behavior Detected",   scanners: ["guardduty", "semgrep"],                   controls: ["GuardDuty", "Suricata rules", "Falco"] },
  { cc: "CC7.5", name: "Vulnerabilities Remediated",    scanners: ["trivy-sca", "grype", "semgrep", "zap"],   controls: ["DefectDojo SLA", "MTTR metrics"] },
  { cc: "CC8.1", name: "Change Management",             scanners: ["semgrep", "checkov"],                     controls: ["Branch protection", "signed commits", "PR checklist"] },
  { cc: "A1.2",  name: "Availability Controls",         scanners: ["prowler", "checkov"],                     controls: ["RDS Multi-AZ", "S3 versioning", "ECS autoscaling"] },
];

// ── shared badge component helpers ────────────────────────────────────────────
function ScannerBadge({ id }: { id: string }) {
  return (
    <span className="text-xs bg-gray-800 text-gray-300 px-2 py-0.5 rounded font-mono border border-gray-700/50">
      {id}
    </span>
  );
}

function ControlBadge({ label, color }: { label: string; color: string }) {
  return (
    <span className={`text-xs px-2 py-0.5 rounded border ${color}`}>
      {label}
    </span>
  );
}

function SectionHeader({ title, subtitle, count }: { title: string; subtitle: string; count?: string }) {
  return (
    <div className="flex items-baseline justify-between mb-4">
      <div>
        <h2 className="text-white font-black text-lg">{title}</h2>
        <p className="text-gray-500 text-xs mt-0.5">{subtitle}</p>
      </div>
      {count && <span className="text-xs text-gray-500 font-mono">{count}</span>}
    </div>
  );
}

export default function CompliancePage() {
  return (
    <div className="min-h-screen bg-gray-950 text-white">
      <Navbar />
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-12">

        {/* Page header */}
        <div>
          <h1 className="text-3xl font-black text-white mb-2">Compliance Mapping</h1>
          <p className="text-gray-400 text-sm">
            Scanner coverage mapped to OWASP Top 10, OWASP LLM Top 10, HIPAA Security Rule,
            GDPR Art. 32, PCI-DSS v4.0, NIST CSF 2.0, and SOC 2 Trust Services Criteria.
          </p>
          <div className="flex gap-2 mt-3 flex-wrap">
            {["OWASP Top 10","OWASP LLM","HIPAA","GDPR","PCI-DSS v4","NIST CSF 2.0","SOC 2"].map(f => (
              <span key={f} className="text-xs bg-gray-800 text-gray-400 px-2 py-1 rounded border border-gray-700">{f}</span>
            ))}
          </div>
        </div>

        {/* ── OWASP Top 10 (2021) ── */}
        <section>
          <SectionHeader
            title="OWASP Top 10 (2021)"
            subtitle="All 10 categories — scanner IDs show which tools detect each risk class"
            count={`${OWASP.length} categories`}
          />
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-800">
                  <th className="text-left py-2 px-3 text-gray-400 font-semibold w-28">Category</th>
                  <th className="text-left py-2 px-3 text-gray-400 font-semibold">Risk</th>
                  <th className="text-left py-2 px-3 text-gray-400 font-semibold">Scanner Coverage</th>
                </tr>
              </thead>
              <tbody>
                {OWASP.map(o => (
                  <tr key={o.id} className="border-b border-gray-800/50 hover:bg-gray-900/50">
                    <td className="py-2 px-3 font-mono text-purple-400 font-bold text-xs">{o.id}</td>
                    <td className="py-2 px-3 text-white">{o.name}</td>
                    <td className="py-2 px-3">
                      <div className="flex gap-1 flex-wrap">
                        {o.scanners.map(s => <ScannerBadge key={s} id={s} />)}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        {/* ── OWASP LLM Top 10 (2025) ── */}
        <section>
          <SectionHeader
            title="OWASP LLM Top 10 (2025)"
            subtitle="Pursh AI flows (doctor-matching, visit summarization, symptom checker) tested by promptfoo + Garak"
            count={`${OWASP_LLM.length} categories`}
          />
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-800">
                  <th className="text-left py-2 px-3 text-gray-400 font-semibold w-20">ID</th>
                  <th className="text-left py-2 px-3 text-gray-400 font-semibold">Risk</th>
                  <th className="text-left py-2 px-3 text-gray-400 font-semibold">Scanner</th>
                  <th className="text-left py-2 px-3 text-gray-400 font-semibold">Pursh Control</th>
                </tr>
              </thead>
              <tbody>
                {OWASP_LLM.map(o => (
                  <tr key={o.id} className="border-b border-gray-800/50 hover:bg-gray-900/50">
                    <td className="py-2 px-3 font-mono text-pink-400 font-bold text-xs">{o.id}</td>
                    <td className="py-2 px-3 text-white">{o.name}</td>
                    <td className="py-2 px-3">
                      <div className="flex gap-1 flex-wrap">
                        {o.scanners.map(s => <ScannerBadge key={s} id={s} />)}
                      </div>
                    </td>
                    <td className="py-2 px-3 text-gray-400 text-xs">{o.pursh}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        {/* ── HIPAA Security Rule ── */}
        <section>
          <SectionHeader
            title="HIPAA Security Rule"
            subtitle="Synthetic data only — controls are real, PHI is not. Demonstrates §164.312 implementation."
            count={`${HIPAA.length} sections`}
          />
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-800">
                  <th className="text-left py-2 px-3 text-gray-400 font-semibold w-44">Section</th>
                  <th className="text-left py-2 px-3 text-gray-400 font-semibold">Requirement</th>
                  <th className="text-left py-2 px-3 text-gray-400 font-semibold">Scanners</th>
                  <th className="text-left py-2 px-3 text-gray-400 font-semibold">Pursh Controls</th>
                </tr>
              </thead>
              <tbody>
                {HIPAA.map(h => (
                  <tr key={h.section} className="border-b border-gray-800/50 hover:bg-gray-900/50">
                    <td className="py-2 px-3 font-mono text-blue-400 font-bold text-xs">{h.section}</td>
                    <td className="py-2 px-3 text-white">{h.name}</td>
                    <td className="py-2 px-3">
                      <div className="flex gap-1 flex-wrap">
                        {h.scanners.map(s => <ScannerBadge key={s} id={s} />)}
                      </div>
                    </td>
                    <td className="py-2 px-3">
                      <div className="flex gap-1 flex-wrap">
                        {h.controls.map(c => <ControlBadge key={c} label={c} color="bg-blue-900/20 text-blue-300 border-blue-700/30" />)}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        {/* ── GDPR Article 32 ── */}
        <section>
          <SectionHeader
            title="GDPR Article 32"
            subtitle="Appropriate technical measures — mapping demonstrates risk-based approach, not a compliance claim."
            count={`${GDPR.length} sub-clauses`}
          />
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-800">
                  <th className="text-left py-2 px-3 text-gray-400 font-semibold w-28">Sub-clause</th>
                  <th className="text-left py-2 px-3 text-gray-400 font-semibold">Requirement</th>
                  <th className="text-left py-2 px-3 text-gray-400 font-semibold">Scanners</th>
                  <th className="text-left py-2 px-3 text-gray-400 font-semibold">Pursh Controls</th>
                </tr>
              </thead>
              <tbody>
                {GDPR.map(g => (
                  <tr key={g.article} className="border-b border-gray-800/50 hover:bg-gray-900/50">
                    <td className="py-2 px-3 font-mono text-green-400 font-bold text-xs">{g.article}</td>
                    <td className="py-2 px-3 text-white">{g.name}</td>
                    <td className="py-2 px-3">
                      <div className="flex gap-1 flex-wrap">
                        {g.scanners.map(s => <ScannerBadge key={s} id={s} />)}
                      </div>
                    </td>
                    <td className="py-2 px-3">
                      <div className="flex gap-1 flex-wrap">
                        {g.controls.map(c => <ControlBadge key={c} label={c} color="bg-green-900/20 text-green-300 border-green-700/30" />)}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        {/* ── PCI-DSS v4.0 ── */}
        <section>
          <SectionHeader
            title="PCI-DSS v4.0"
            subtitle="Synthetic card data only — demonstrates the controls a payment-handling telehealth app requires."
            count={`${PCI.length} requirements`}
          />
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-800">
                  <th className="text-left py-2 px-3 text-gray-400 font-semibold w-24">Req</th>
                  <th className="text-left py-2 px-3 text-gray-400 font-semibold">Requirement</th>
                  <th className="text-left py-2 px-3 text-gray-400 font-semibold">Scanners</th>
                  <th className="text-left py-2 px-3 text-gray-400 font-semibold">Pursh Controls</th>
                </tr>
              </thead>
              <tbody>
                {PCI.map(p => (
                  <tr key={p.req} className="border-b border-gray-800/50 hover:bg-gray-900/50">
                    <td className="py-2 px-3 font-mono text-orange-400 font-bold text-xs">{p.req}</td>
                    <td className="py-2 px-3 text-white">{p.name}</td>
                    <td className="py-2 px-3">
                      <div className="flex gap-1 flex-wrap">
                        {p.scanners.map(s => <ScannerBadge key={s} id={s} />)}
                      </div>
                    </td>
                    <td className="py-2 px-3">
                      <div className="flex gap-1 flex-wrap">
                        {p.controls.map(c => <ControlBadge key={c} label={c} color="bg-orange-900/20 text-orange-300 border-orange-700/30" />)}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        {/* ── NIST CSF 2.0 ── */}
        <section>
          <SectionHeader
            title="NIST CSF 2.0"
            subtitle="Six Functions: Govern · Identify · Protect · Detect · Respond · Recover"
            count={`${NIST.length} subcategories`}
          />
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-800">
                  <th className="text-left py-2 px-3 text-gray-400 font-semibold w-8">Fn</th>
                  <th className="text-left py-2 px-3 text-gray-400 font-semibold w-28">ID</th>
                  <th className="text-left py-2 px-3 text-gray-400 font-semibold">Subcategory</th>
                  <th className="text-left py-2 px-3 text-gray-400 font-semibold">Scanners</th>
                  <th className="text-left py-2 px-3 text-gray-400 font-semibold">Implementation</th>
                </tr>
              </thead>
              <tbody>
                {NIST.map(n => (
                  <tr key={n.id} className="border-b border-gray-800/50 hover:bg-gray-900/50">
                    <td className="py-2 px-3 font-mono text-sky-400 font-bold text-xs">{n.fn}</td>
                    <td className="py-2 px-3 font-mono text-sky-300 text-xs">{n.id}</td>
                    <td className="py-2 px-3 text-white">{n.name}</td>
                    <td className="py-2 px-3">
                      <div className="flex gap-1 flex-wrap">
                        {n.scanners.map(s => <ScannerBadge key={s} id={s} />)}
                      </div>
                    </td>
                    <td className="py-2 px-3">
                      <div className="flex gap-1 flex-wrap">
                        {n.controls.map(c => <ControlBadge key={c} label={c} color="bg-sky-900/20 text-sky-300 border-sky-700/30" />)}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        {/* ── SOC 2 Trust Services Criteria ── */}
        <section>
          <SectionHeader
            title="SOC 2 Trust Services Criteria"
            subtitle="Security (CC) and Availability (A) criteria — evidence of consistent operation over time."
            count={`${SOC2.length} criteria`}
          />
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-800">
                  <th className="text-left py-2 px-3 text-gray-400 font-semibold w-16">CC</th>
                  <th className="text-left py-2 px-3 text-gray-400 font-semibold">Criteria</th>
                  <th className="text-left py-2 px-3 text-gray-400 font-semibold">Scanners</th>
                  <th className="text-left py-2 px-3 text-gray-400 font-semibold">Evidence</th>
                </tr>
              </thead>
              <tbody>
                {SOC2.map(s => (
                  <tr key={s.cc} className="border-b border-gray-800/50 hover:bg-gray-900/50">
                    <td className="py-2 px-3 font-mono text-violet-400 font-bold text-xs">{s.cc}</td>
                    <td className="py-2 px-3 text-white">{s.name}</td>
                    <td className="py-2 px-3">
                      <div className="flex gap-1 flex-wrap">
                        {s.scanners.map(sc => <ScannerBadge key={sc} id={sc} />)}
                      </div>
                    </td>
                    <td className="py-2 px-3">
                      <div className="flex gap-1 flex-wrap">
                        {s.controls.map(c => <ControlBadge key={c} label={c} color="bg-violet-900/20 text-violet-300 border-violet-700/30" />)}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

      </main>
    </div>
  );
}
