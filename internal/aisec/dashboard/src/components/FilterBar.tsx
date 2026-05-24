"use client";

interface Props {
  search: string;
  severity: string;
  scanner: string;
  status: string;
  scanners: string[];
  onSearch: (v: string) => void;
  onSeverity: (v: string) => void;
  onScanner: (v: string) => void;
  onStatus: (v: string) => void;
}

export default function FilterBar({ search, severity, scanner, status, scanners, onSearch, onSeverity, onScanner, onStatus }: Props) {
  const sel = "bg-gray-800 border border-gray-700 rounded-lg px-3 py-1.5 text-sm text-white focus:outline-none focus:border-teal-500";
  return (
    <div className="flex flex-wrap gap-3 items-center">
      <input
        type="search"
        placeholder="Search findings…"
        value={search}
        onChange={e => onSearch(e.target.value)}
        className="flex-1 min-w-48 bg-gray-800 border border-gray-700 rounded-lg px-3 py-1.5 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-teal-500"
      />
      <select value={severity} onChange={e => onSeverity(e.target.value)} className={sel}>
        <option value="">All severities</option>
        {["CRITICAL","HIGH","MEDIUM","LOW","INFO"].map(s => <option key={s}>{s}</option>)}
      </select>
      <select value={scanner} onChange={e => onScanner(e.target.value)} className={sel}>
        <option value="">All scanners</option>
        {scanners.map(s => <option key={s}>{s}</option>)}
      </select>
      <select value={status} onChange={e => onStatus(e.target.value)} className={sel}>
        <option value="">All statuses</option>
        {["open","triaged","accepted_risk","fixed","false_positive"].map(s => <option key={s}>{s}</option>)}
      </select>
    </div>
  );
}
