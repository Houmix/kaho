import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/router';
import api from '@/lib/api';
import { useRequireAuth } from '@/hooks/useRequireAuth';
import AppShell from '@/components/AppShell';
import { Lesson, STATUS_LABELS, frDate, hm } from '@/lib/types';

export default function StudentLessonDetail() {
  const ready = useRequireAuth('STUDENT');
  const router = useRouter();
  const id = typeof router.query.id === 'string' ? router.query.id : null;
  const [l, setL] = useState<Lesson | null>(null);
  const [error, setError] = useState('');
  useEffect(() => { if (ready && id) api.get(`/lessons/${id}/`).then((r) => setL(r.data)).catch(() => setError('Bilan introuvable.')); }, [ready, id]);

  if (error) return <AppShell title="Bilan"><p className="text-red-700">{error}</p></AppShell>;
  if (!l) return <AppShell title="Bilan"><p className="text-brown-500">Chargement…</p></AppShell>;
  const acquired = l.assessments.filter((a) => a.status === 'ACQUIRED');
  const inProgress = l.assessments.filter((a) => a.status === 'IN_PROGRESS');

  return (
    <AppShell title="Bilan de leçon">
      <p className="text-xs uppercase tracking-wide text-caramel font-medium">Bilan pédagogique</p>
      <h1 className="text-3xl mt-1 mb-1">Leçon du {frDate(l.slot.date, { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' })}</h1>
      <p className="text-brown-800/70 mb-6">{hm(l.slot.start_time)}–{hm(l.slot.end_time)} · avec <strong>{l.instructor_name}</strong> · {l.slot.meeting_point_name}{!l.attended && <span className="badge bg-red-100 text-red-700 ml-2">absence</span>}</p>

      <div className="grid md:grid-cols-2 gap-6">
        <section className="card">
          <h2 className="text-xl mb-2">Commentaires et conseils du moniteur</h2>
          {l.instructor_notes ? <p className="whitespace-pre-line">{l.instructor_notes}</p> : <p className="text-sm text-brown-800/60">Aucune remarque pour cette séance.</p>}
          {l.weather_conditions && <p className="text-sm text-brown-800/70 mt-3">Conditions : {l.weather_conditions}</p>}
        </section>
        <section className="card">
          <h2 className="text-xl mb-2">Compétences travaillées</h2>
          {l.assessments.length === 0 ? <p className="text-sm text-brown-800/60">Aucune compétence cochée pour cette séance.</p> : (
            <>
              {acquired.length > 0 && <><p className="text-sm font-medium mt-1 mb-1">Validées</p><ul className="flex flex-wrap gap-1 mb-3">{acquired.map((a) => <li key={a.competency} className="badge bg-brown-700 text-cream-50" title={a.label}>{a.code} {a.label}</li>)}</ul></>}
              {inProgress.length > 0 && <><p className="text-sm font-medium mb-1">En cours d'acquisition</p><ul className="flex flex-wrap gap-1">{inProgress.map((a) => <li key={a.competency} className="badge bg-caramel/40 text-brown-900" title={STATUS_LABELS[a.status]}>{a.code} {a.label}</li>)}</ul></>}
            </>
          )}
        </section>
        <section className="card md:col-span-2">
          <h2 className="text-xl mb-2">Votre avis sur cette leçon</h2>
          {l.rating ? <p><span className="text-caramel">{'★'.repeat(l.rating.score)}</span>{l.rating.comment && <span className="text-brown-800/70"> — « {l.rating.comment} »</span>}{l.rating.reply && <span className="block text-sm text-brown-800/70 mt-1">↳ Réponse de l'école : {l.rating.reply}</span>}</p>
            : l.attended ? <p className="text-sm">Vous n'avez pas encore noté cette leçon. <Link href="/student/notebook" className="text-brown-700 hover:underline">Donner mon avis →</Link></p> : <p className="text-sm text-brown-800/60">Leçon non effectuée.</p>}
        </section>
      </div>
      <Link href="/student/notebook" className="inline-block mt-6 text-sm text-brown-700 hover:underline">Voir tout le livret d'apprentissage →</Link>
    </AppShell>
  );
}
