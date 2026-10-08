import { useEffect, useState } from 'react';
import api from '@/lib/api';
import { BACKOFFICE, useRequireAuth } from '@/hooks/useRequireAuth';
import AppShell from '@/components/AppShell';
import { PerformanceRow } from '@/lib/types';

export default function Performance() {
  const ready = useRequireAuth(BACKOFFICE);
  const [rows, setRows] = useState<PerformanceRow[] | null>(null);

  useEffect(() => { if (ready) api.get('/instructors/performance/').then((r) => setRows(r.data)); }, [ready]);

  if (!rows) return <AppShell title="Performance"><p className="text-brown-500">Chargement…</p></AppShell>;

  return (
    <AppShell title="Performance des moniteurs">
      <h1 className="text-3xl mb-2">Performance des moniteurs</h1>
      <p className="text-brown-800/70 mb-6">Avis des élèves après chaque leçon, volume d'activité et incidents.</p>

      <div className="card p-0 overflow-x-auto mb-8">
        <table className="w-full text-sm">
          <thead className="bg-cream-100 text-brown-800/70">
            <tr>
              <th className="text-left py-3 px-4 font-medium">Moniteur</th>
              <th className="text-left py-3 px-4 font-medium">Note</th>
              <th className="text-right py-3 px-4 font-medium">Avis</th>
              <th className="text-right py-3 px-4 font-medium">Leçons</th>
              <th className="text-right py-3 px-4 font-medium">Heures</th>
              <th className="text-right py-3 px-4 font-medium">Élèves</th>
              <th className="text-right py-3 px-4 font-medium">Absences</th>
              <th className="text-right py-3 px-4 font-medium">Annul. tardives</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.id} className="border-t border-cream-200">
                <td className="py-3 px-4 font-medium">{r.name}{!r.is_bookable && <span className="badge bg-cream-200 text-brown-800 ml-2">non réservable</span>}</td>
                <td className="py-3 px-4">{r.rating_average !== null ? <span><span className="text-caramel">{'★'.repeat(Math.round(r.rating_average))}</span> {r.rating_average.toFixed(1)}</span> : <span className="text-brown-800/40">—</span>}</td>
                <td className="py-3 px-4 text-right">{r.rating_count}</td>
                <td className="py-3 px-4 text-right">{r.lessons}</td>
                <td className="py-3 px-4 text-right">{r.hours} h</td>
                <td className="py-3 px-4 text-right">{r.students}</td>
                <td className="py-3 px-4 text-right">{r.no_shows}</td>
                <td className="py-3 px-4 text-right">{r.late_cancellations}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="grid md:grid-cols-2 gap-4">
        {rows.filter((r) => r.recent_comments.length).map((r) => (
          <div key={r.id} className="card">
            <h3 className="font-semibold mb-2">{r.name} — derniers commentaires</h3>
            <ul className="space-y-2 text-sm text-brown-800/80">{r.recent_comments.map((c, i) => <li key={i}>« {c} »</li>)}</ul>
          </div>
        ))}
      </div>
    </AppShell>
  );
}
