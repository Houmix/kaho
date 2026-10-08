import { useCallback, useEffect, useState } from 'react';
import api from '@/lib/api';
import { useRequireAuth } from '@/hooks/useRequireAuth';
import AppShell from '@/components/AppShell';
import ProgressGauge from '@/components/ProgressGauge';
import { AssessmentStatus, Lesson, Logbook, STATUS_LABELS, apiError, frDate, hm } from '@/lib/types';

const statusCls: Record<AssessmentStatus, string> = {
  NOT_COVERED: 'bg-cream-100 text-brown-800/60',
  IN_PROGRESS: 'bg-caramel/30 text-brown-900',
  ACQUIRED: 'bg-brown-700 text-cream-50',
};

function RatingForm({ lesson, onDone }: { lesson: Lesson; onDone: () => void }) {
  const [score, setScore] = useState(0);
  const [comment, setComment] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const submit = async () => {
    if (!score) return;
    setBusy(true); setError('');
    try { await api.post(`/lessons/${lesson.id}/rate/`, { score, comment }); onDone(); }
    catch (err) { setError(apiError(err, 'Impossible d’enregistrer votre avis.')); }
    finally { setBusy(false); }
  };
  return (
    <div className="card border-caramel bg-brown-50">
      <p className="font-semibold">Comment s'est passée votre leçon du {frDate(lesson.slot.date)} avec {lesson.instructor_name} ?</p>
      <div className="flex gap-1 my-3" role="radiogroup" aria-label="Note sur 5">
        {[1, 2, 3, 4, 5].map((n) => (
          <button key={n} type="button" role="radio" aria-checked={score === n} onClick={() => setScore(n)}
            className={`text-3xl leading-none ${n <= score ? 'text-caramel' : 'text-cream-300'} hover:text-caramel`} aria-label={`${n} sur 5`}>★</button>
        ))}
      </div>
      <textarea value={comment} onChange={(e) => setComment(e.target.value)} placeholder="Un mot sur la pédagogie, l'écoute, le rythme… (facultatif)" className="input-field" rows={2} />
      {error && <p className="text-sm text-red-700 mt-2">{error}</p>}
      <button onClick={submit} disabled={!score || busy} className="btn-primary mt-3 disabled:opacity-50">{busy ? 'Envoi…' : 'Envoyer mon avis'}</button>
    </div>
  );
}

export default function Notebook() {
  const ready = useRequireAuth('STUDENT');
  const [logbook, setLogbook] = useState<Logbook | null>(null);
  const [toRate, setToRate] = useState<Lesson[]>([]);

  const load = useCallback(async () => {
    const [lb, tr] = await Promise.all([api.get('/student-profiles/my_logbook/'), api.get('/lessons/to_rate/')]);
    setLogbook(lb.data);
    setToRate(tr.data);
  }, []);

  useEffect(() => { if (ready) load(); }, [ready, load]);

  if (!logbook) return <AppShell title="Livret"><p className="text-brown-500">Chargement…</p></AppShell>;

  const groups = Array.from(new Set(logbook.competencies.map((c) => c.group))).sort();

  return (
    <AppShell title="Livret d'apprentissage">
      <h1 className="text-3xl mb-6">Mon livret d'apprentissage</h1>

      {toRate.length > 0 && (
        <section className="mb-8 space-y-4">
          <h2 className="text-xl">Votre avis compte</h2>
          {toRate.map((l) => <RatingForm key={l.id} lesson={l} onDone={load} />)}
        </section>
      )}

      <section className="card mb-8">
        <h2 className="text-xl mb-4">Progression globale</h2>
        <ProgressGauge progress={logbook.progress} />
      </section>

      <section className="mb-10">
        <h2 className="text-xl mb-3">Compétences (programme REMC)</h2>
        <div className="space-y-4">
          {groups.map((g) => {
            const items = logbook.competencies.filter((c) => c.group === g);
            return (
              <div key={g} className="card">
                <h3 className="font-semibold mb-3">{g}. {items[0].group_label}</h3>
                <ul className="divide-y divide-cream-200">
                  {items.map((c) => (
                    <li key={c.id} className="py-2 flex items-center justify-between gap-3 text-sm">
                      <span><span className="text-brown-800/50 mr-2">{c.code}</span>{c.label}</span>
                      <span className={`badge shrink-0 ${statusCls[c.status]}`}>{STATUS_LABELS[c.status]}</span>
                    </li>
                  ))}
                </ul>
              </div>
            );
          })}
        </div>
      </section>

      <section>
        <h2 className="text-xl mb-3">Bilans de leçons</h2>
        {logbook.lessons.length === 0 ? (
          <p className="text-brown-800/60">Aucun bilan pour le moment — ils apparaîtront après vos premières leçons.</p>
        ) : (
          <div className="space-y-3">
            {logbook.lessons.map((l) => (
              <article key={l.id} className="card">
                <div className="flex flex-wrap items-baseline justify-between gap-2">
                  <h3 className="font-semibold">{frDate(l.slot.date)} · {hm(l.slot.start_time)} — {l.instructor_name}</h3>
                  {!l.attended && <span className="badge bg-red-100 text-red-700">Absent</span>}
                  {l.rating && <span className="text-caramel text-sm">{'★'.repeat(l.rating.score)}</span>}
                </div>
                {l.weather_conditions && <p className="text-sm text-brown-800/60 mt-1">Conditions : {l.weather_conditions}</p>}
                {l.instructor_notes && <p className="mt-2 whitespace-pre-line">{l.instructor_notes}</p>}
                {l.assessments.length > 0 && (
                  <div className="flex flex-wrap gap-1.5 mt-3">
                    {l.assessments.map((a) => <span key={a.competency} className={`badge ${statusCls[a.status]}`}>{a.code} {a.status_display}</span>)}
                  </div>
                )}
              </article>
            ))}
          </div>
        )}
      </section>
    </AppShell>
  );
}
