import { CompetencyProgress } from '@/lib/types';

export default function ProgressGauge({ progress, compact = false }: { progress: CompetencyProgress; compact?: boolean }) {
  const r = compact ? 28 : 44;
  const stroke = compact ? 6 : 9;
  const c = 2 * Math.PI * r;
  const size = (r + stroke) * 2;
  return (
    <div className="flex items-center gap-4">
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} role="img" aria-label={`${progress.percent} % des compétences acquises`}>
        <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="#EAE0D2" strokeWidth={stroke} />
        <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="#5C3D2E" strokeWidth={stroke} strokeLinecap="round"
          strokeDasharray={c} strokeDashoffset={c * (1 - progress.percent / 100)} transform={`rotate(-90 ${size / 2} ${size / 2})`} />
        <text x="50%" y="50%" dominantBaseline="central" textAnchor="middle" className="fill-brown-900" fontFamily="Fraunces, serif" fontSize={compact ? 14 : 22} fontWeight={600}>
          {progress.percent}%
        </text>
      </svg>
      <div className="text-sm text-brown-800/80">
        <div><strong className="text-brown-900">{progress.acquired}</strong> acquises sur {progress.total}</div>
        <div>{progress.in_progress} en cours</div>
      </div>
    </div>
  );
}
