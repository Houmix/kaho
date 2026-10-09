import Link from 'next/link';
import { ExamStats, fmtDuration } from '@/lib/lms';

/** Jauge de préparation (moyenne des 5 derniers examens blancs). */
export function ReadinessGauge({ value, count, threshold = 88, compact = false }: { value: number | null; count: number; threshold?: number; compact?: boolean }) {
  const pct = value ?? 0;
  const r = 44, c = Math.PI * r; // demi-cercle
  const ready = value !== null && value >= threshold;
  const label = value === null ? 'Pas encore d’examen blanc' : ready ? 'Prêt pour l’examen du code' : value >= threshold - 10 ? 'Presque prêt — encore un effort' : 'Entraînement à poursuivre';
  return (
    <div className={`flex ${compact ? 'items-center gap-4' : 'flex-col items-center'}`}>
      <svg viewBox="0 0 100 58" className={compact ? 'w-28' : 'w-48'} aria-label={`Préparation ${value ?? 0} %`}>
        <path d="M6 52 A44 44 0 0 1 94 52" fill="none" stroke="#EAE0D2" strokeWidth="10" strokeLinecap="round" />
        <path d="M6 52 A44 44 0 0 1 94 52" fill="none" stroke={ready ? '#5C3D2E' : '#C8A97E'} strokeWidth="10" strokeLinecap="round" strokeDasharray={`${(pct / 100) * c} ${c}`} />
        <text x="50" y="50" textAnchor="middle" fontSize="20" fontWeight="600" fill="#2B1D14">{value === null ? '—' : `${value} %`}</text>
      </svg>
      <div className={compact ? '' : 'text-center'}>
        <p className="font-semibold">{label}</p>
        <p className="text-xs text-brown-800/60">{count ? `Moyenne des ${count} dernier(s) examen(s) blanc(s) · objectif ${threshold} %` : 'Passez un examen blanc pour mesurer votre niveau'}</p>
      </div>
    </div>
  );
}

/** Courbe d'évolution des scores aux examens blancs. */
export function ScoreChart({ points, threshold = 88 }: { points: ExamStats['evolution']; threshold?: number }) {
  if (points.length === 0) return <p className="text-sm text-brown-800/60">Aucun examen blanc terminé.</p>;
  const w = 320, h = 120, px = 24, py = 10;
  const x = (i: number) => px + (points.length === 1 ? (w - 2 * px) / 2 : (i * (w - 2 * px)) / (points.length - 1));
  const y = (s: number) => h - py - (s / 100) * (h - 2 * py);
  const d = points.map((p, i) => `${i ? 'L' : 'M'}${x(i)} ${y(p.score)}`).join(' ');
  return (
    <svg viewBox={`0 0 ${w} ${h}`} className="w-full" aria-label="Évolution des scores">
      {[0, 50, 100].map((v) => <g key={v}><line x1={px} x2={w - px} y1={y(v)} y2={y(v)} stroke="#EAE0D2" /><text x={4} y={y(v) + 4} fontSize="9" fill="#8B5E3C">{v}</text></g>)}
      <line x1={px} x2={w - px} y1={y(threshold)} y2={y(threshold)} stroke="#C8A97E" strokeDasharray="4 3" />
      <path d={d} fill="none" stroke="#5C3D2E" strokeWidth="2" />
      {points.map((p, i) => <circle key={i} cx={x(i)} cy={y(p.score)} r="3.5" fill={p.passed ? '#5C3D2E' : '#C8A97E'}><title>{p.date ?? ''} · {p.exam} · {p.score} %</title></circle>)}
    </svg>
  );
}

/** Histogramme des performances thème par thème. */
export function TopicBars({ topics, threshold = 88 }: { topics: ExamStats['by_topic']; threshold?: number }) {
  if (topics.length === 0) return <p className="text-sm text-brown-800/60">Les thèmes apparaîtront après votre premier examen blanc.</p>;
  return (
    <ul className="space-y-1.5 text-sm">
      {topics.map((t) => (
        <li key={t.code || t.topic} className="flex items-center gap-2">
          <span className="w-40 truncate" title={t.topic}>{t.topic}</span>
          <div className="flex-1 h-2 bg-cream-200 rounded-full overflow-hidden"><div className={`h-full ${(t.percent ?? 0) >= threshold ? 'bg-brown-700' : (t.percent ?? 0) >= 60 ? 'bg-caramel' : 'bg-red-300'}`} style={{ width: `${t.percent ?? 0}%` }} /></div>
          <span className="w-14 text-right text-brown-800/70">{t.percent === null ? '—' : `${t.percent} %`}</span>
          {t.code && t.percent !== null && t.percent < threshold && <Link href={`/code/revision?topic=${t.code}`} className="text-xs text-brown-700 hover:underline whitespace-nowrap">réviser</Link>}
        </li>
      ))}
    </ul>
  );
}

export function StatTiles({ s }: { s: ExamStats }) {
  return (
    <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-sm">
      {[['Examens blancs', `${s.attempts}`, `${s.passed} réussi(s)`], ['Moyenne', s.average === null ? '—' : `${s.average} %`, `meilleur : ${s.best ?? '—'} %`], ['Séries de quiz', `${s.quiz_attempts}`, `${s.lessons_done} leçon(s) terminée(s)`], ['Temps passé', fmtDuration(s.time_seconds), 'sur la plateforme']].map(([l, v, sub]) => (
        <div key={l} className="rounded-xl bg-cream-100 px-3 py-2"><p className="text-xs text-brown-800/70">{l}</p><p className="text-xl font-display">{v}</p><p className="text-[11px] text-brown-800/60">{sub}</p></div>
      ))}
    </div>
  );
}
