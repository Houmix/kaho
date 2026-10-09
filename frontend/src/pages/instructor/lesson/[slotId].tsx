import { useEffect, useState } from 'react';
import { useRouter } from 'next/router';
import Link from 'next/link';
import api from '@/lib/api';
import { STAFF_ROLES, useRequireAuth } from '@/hooks/useRequireAuth';
import AppShell from '@/components/AppShell';
import ProgressGauge from '@/components/ProgressGauge';
import BackLink from '@/components/BackLink';
import { AssessmentStatus, Competency, Lesson, Logbook, STATUS_LABELS, Slot, apiError, frDate, hm } from '@/lib/types';

type Choice = Exclude<AssessmentStatus, 'NOT_COVERED'>;

export default function LessonForm() {
  const ready = useRequireAuth(STAFF_ROLES);
  const router = useRouter();
  const slotId = typeof router.query.slotId === 'string' ? Number(router.query.slotId) : null;
  const [slot, setSlot] = useState<Slot | null>(null);
  const [existing, setExisting] = useState<Lesson | null>(null);
  const [competencies, setCompetencies] = useState<Competency[]>([]);
  const [logbook, setLogbook] = useState<Logbook | null>(null);
  const [attended, setAttended] = useState(true);
  const [weather, setWeather] = useState('');
  const [notes, setNotes] = useState('');
  const [choices, setChoices] = useState<Record<number, Choice>>({});
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (!ready || !slotId) return;
    (async () => {
      const [s, c] = await Promise.all([api.get(`/slots/${slotId}/`), api.get('/competencies/')]);
      setSlot(s.data);
      setCompetencies(c.data);
      if (s.data.student) api.get(`/student-profiles/${s.data.student}/logbook/`).then((r) => setLogbook(r.data));
      if (s.data.lesson_id) {
        const l = (await api.get(`/lessons/${s.data.lesson_id}/`)).data as Lesson;
        setExisting(l);
        setAttended(l.attended);
        setWeather(l.weather_conditions);
        setNotes(l.instructor_notes);
        const init: Record<number, Choice> = {};
        l.assessments.forEach((a) => { if (a.status !== 'NOT_COVERED') init[a.competency] = a.status; });
        setChoices(init);
      }
    })();
  }, [ready, slotId]);

  const toggle = (id: number, value: Choice) =>
    setChoices((prev) => (prev[id] === value ? (({ [id]: _, ...rest }) => rest)(prev) : { ...prev, [id]: value }));

  const submit = async () => {
    if (!slot) return;
    setBusy(true); setError('');
    const payload = {
      slot_id: slot.id, attended, weather_conditions: weather, instructor_notes: notes,
      assessments: Object.entries(choices).map(([competency, status]) => ({ competency: Number(competency), status })),
    };
    try {
      if (existing) await api.patch(`/lessons/${existing.id}/`, payload);
      else await api.post('/lessons/', payload);
      router.push(router.query.from === 'planning' ? '/instructor/planning' : '/instructor/dashboard');
    } catch (err) {
      setError(apiError(err, 'Impossible d’enregistrer le bilan.'));
    } finally { setBusy(false); }
  };

  if (!slot) return <AppShell title="Bilan de leçon"><p className="text-brown-500">Chargement…</p></AppShell>;

  const locked = !existing && !slot.can_assess;
  const opens = new Date(slot.assessment_opens_at);
  const opensLabel = `${opens.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })}${opens.toDateString() === new Date().toDateString() ? '' : ' le ' + opens.toLocaleDateString('fr-FR', { day: 'numeric', month: 'long' })}`;
  const current = new Map(logbook?.competencies.map((c) => [c.id, c.status]) ?? []);
  const groups = Array.from(new Set(competencies.map((c) => c.group))).sort();

  return (
    <AppShell title="Bilan de leçon">
      <BackLink fallbackHref="/instructor/dashboard" fallbackLabel="← Retour au tableau de bord" />
      <h1 className="text-3xl mt-2 mb-1">{existing ? 'Modifier le bilan' : 'Bilan de leçon'}</h1>
      <p className="text-brown-800/70 mb-2">{slot.student_name} · {frDate(slot.date)} · {hm(slot.start_time)}–{hm(slot.end_time)} · {slot.meeting_point_name}</p>
      {slot.student && <div className="flex flex-wrap gap-2 mb-6">
        <Link href={`/admin/students/${slot.student}?from=planning`} className="btn-secondary !py-1.5 text-sm">Fiche élève & historique</Link>
        {logbook?.student.phone && <a href={`tel:${logbook.student.phone}`} className="btn-secondary !py-1.5 text-sm">📞 Appeler</a>}
        {logbook?.student.phone && <a href={`sms:${logbook.student.phone}`} className="btn-secondary !py-1.5 text-sm">💬 SMS</a>}
        {logbook?.student.user.email && <a href={`mailto:${logbook.student.user.email}`} className="btn-secondary !py-1.5 text-sm">✉ Email</a>}
      </div>}

      {logbook && (
        <div className="card mb-6 flex flex-wrap items-center justify-between gap-4">
          <div><p className="text-sm text-brown-800/70">Progression de l'élève</p><ProgressGauge progress={logbook.progress} compact /></div>
          <p className="text-sm text-brown-800/70">{logbook.student.remaining_hours.toFixed(1)} h restantes · {logbook.lessons.length} bilan{logbook.lessons.length > 1 ? 's' : ''}</p>
        </div>
      )}

      {error && <div className="rounded-xl border border-red-200 bg-red-50 text-red-700 px-4 py-3 mb-6 text-sm">{error}</div>}
      {locked && (
        <div className="rounded-xl border border-caramel bg-brown-50 px-4 py-3 mb-6 text-sm" role="status">
          🔒 <strong>Bilan verrouillé.</strong> Il pourra être saisi à partir de {opensLabel} (10 dernières minutes de la leçon), puis après sa fin.
        </div>
      )}

      <fieldset disabled={locked} className={locked ? 'opacity-50' : ''}>
      <section className="card mb-6 space-y-4">
        <label className="flex items-center gap-3">
          <input type="checkbox" checked={attended} onChange={(e) => setAttended(e.target.checked)} className="w-5 h-5 accent-brown-700" />
          <span className="font-medium">Élève présent</span>
          {!attended && <span className="text-sm text-red-700">L'heure sera décomptée (absence non justifiée)</span>}
        </label>
        <label className="block">
          <span className="text-sm font-medium text-brown-800">Conditions (météo, trafic, route)</span>
          <input value={weather} onChange={(e) => setWeather(e.target.value)} className="input-field mt-1" placeholder="Ex : pluie, circulation dense, périphérique" />
        </label>
        <label className="block">
          <span className="text-sm font-medium text-brown-800">Observations pour l'élève</span>
          <textarea value={notes} onChange={(e) => setNotes(e.target.value)} className="input-field mt-1" rows={4} placeholder="Points forts, axes de travail pour la prochaine séance…" />
        </label>
      </section>

      <section className="mb-8">
        <h2 className="text-xl mb-1">Compétences travaillées</h2>
        <p className="text-sm text-brown-800/60 mb-4">Ne cochez que ce qui a été abordé aujourd'hui ; le statut précédent est rappelé à droite.</p>
        <div className="space-y-4">
          {groups.map((g) => {
            const items = competencies.filter((c) => c.group === g);
            return (
              <div key={g} className="card">
                <h3 className="font-semibold mb-3">{g}. {items[0].group_label}</h3>
                <ul className="divide-y divide-cream-200">
                  {items.map((c) => {
                    const prev = current.get(c.id) ?? 'NOT_COVERED';
                    return (
                      <li key={c.id} className="py-2 grid grid-cols-[1fr_auto] sm:grid-cols-[1fr_auto_auto] items-center gap-2 text-sm">
                        <span><span className="text-brown-800/50 mr-2">{c.code}</span>{c.label}</span>
                        <div className="flex gap-1">
                          {(['IN_PROGRESS', 'ACQUIRED'] as Choice[]).map((v) => (
                            <button key={v} type="button" onClick={() => toggle(c.id, v)} aria-pressed={choices[c.id] === v}
                              className={`px-3 py-1 rounded-full text-xs font-medium border ${choices[c.id] === v ? (v === 'ACQUIRED' ? 'bg-brown-700 text-cream-50 border-brown-700' : 'bg-caramel/40 text-brown-900 border-caramel') : 'bg-white border-cream-300 text-brown-800 hover:border-brown-300'}`}>
                              {STATUS_LABELS[v]}
                            </button>
                          ))}
                        </div>
                        <span className="hidden sm:inline text-xs text-brown-800/50 w-20 text-right">{prev === 'NOT_COVERED' ? '—' : STATUS_LABELS[prev]}</span>
                      </li>
                    );
                  })}
                </ul>
              </div>
            );
          })}
        </div>
      </section>

      </fieldset>

      <div className="flex flex-wrap gap-3">
        <button onClick={submit} disabled={busy || locked} className="btn-primary disabled:opacity-60">{busy ? 'Enregistrement…' : existing ? 'Mettre à jour le bilan' : 'Enregistrer le bilan'}</button>
        <Link href={router.query.from === 'planning' ? '/instructor/planning' : '/instructor/dashboard'} className="btn-secondary">Annuler</Link>
      </div>
    </AppShell>
  );
}
