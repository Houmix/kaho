import { useCallback, useEffect, useState } from 'react';
import Link from 'next/link';
import api from '@/lib/api';
import { useRequireAuth } from '@/hooks/useRequireAuth';
import AdminShell from '@/components/AdminShell';

interface Overview {
  courses: { id: number; title: string; slug: string; is_published: boolean; sections: { id: number; title: string; order: number; is_free_preview: boolean; unlock_threshold: number; lessons: { id: number; title: string; is_published: boolean; has_video: boolean; minutes: number; completions: number }[]; quiz: { id: number; title: string; questions: number; attempts: number; pass_rate: number | null } | null }[] }[];
  exams: { id: number; title: string; is_published: boolean; is_demo: boolean; question_count: number; available: number; attempts: number; pass_rate: number | null }[];
  bank: { total: number; topics: { topic: string; n: number }[] };
  learners: { with_access: number; active: number };
}

const djangoAdmin = (path: string) => `${(process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api').replace(/\/api\/?$/, '')}/admin/lms/${path}`;

export default function AdminLms() {
  const ready = useRequireAuth(['SUPERVISOR', 'ADMIN']);
  const [d, setD] = useState<Overview | null>(null);
  const load = useCallback(() => api.get('/lms/admin/overview/').then((r) => setD(r.data)), []);
  useEffect(() => { if (ready) load(); }, [ready, load]);
  const toggle = async (model: string, id: number, field: string, value: boolean | number) => { await api.post('/lms/admin/overview/', { model, id, field, value }); load(); };

  if (!d) return <AdminShell title="Contenus LMS"><p className="text-brown-500">Chargement…</p></AdminShell>;

  const Toggle = ({ on, onChange, label }: { on: boolean; onChange: (v: boolean) => void; label: string }) => (
    <label className="inline-flex items-center gap-1.5 text-xs cursor-pointer"><input type="checkbox" checked={on} onChange={(e) => onChange(e.target.checked)} className="accent-brown-700" />{label}</label>
  );

  return (
    <AdminShell title="Contenus LMS" wide>
      <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
        <h1 className="text-3xl">Contenus LMS</h1>
        <div className="flex gap-2">
          <a href={djangoAdmin('course/add/')} target="_blank" rel="noreferrer" className="btn-secondary">+ Cours</a>
          <a href={djangoAdmin('question/add/')} target="_blank" rel="noreferrer" className="btn-secondary">+ Question</a>
          <a href={djangoAdmin('')} target="_blank" rel="noreferrer" className="btn-primary">Éditeur de contenu ↗</a>
        </div>
      </div>
      <p className="text-brown-800/70 mb-6">Structure, publication et statistiques. La rédaction (Markdown, vidéos, questions) se fait dans l'éditeur, qui s'ouvre dans un nouvel onglet.</p>

      <div className="grid sm:grid-cols-4 gap-4 mb-8">
        <div className="card py-4"><p className="text-sm text-brown-800/70">Apprenants avec accès</p><p className="text-3xl font-display">{d.learners.with_access}</p></div>
        <div className="card py-4"><p className="text-sm text-brown-800/70">Actifs (30 j)</p><p className="text-3xl font-display">{d.learners.active}</p></div>
        <div className="card py-4"><p className="text-sm text-brown-800/70">Banque d'examen</p><p className="text-3xl font-display">{d.bank.total}</p><p className="text-xs text-brown-800/60">{d.bank.topics.map((t) => `${t.topic} (${t.n})`).join(' · ')}</p></div>
        <div className="card py-4"><p className="text-sm text-brown-800/70">Démo publique</p><Link href="/demo" className="text-brown-700 hover:underline text-sm" target="_blank">Voir la page d'essai ↗</Link></div>
      </div>

      {d.courses.map((c) => (
        <section key={c.id} className="card mb-6">
          <div className="flex flex-wrap items-center justify-between gap-3 mb-3">
            <h2 className="text-xl">{c.title} {!c.is_published && <span className="badge bg-cream-200 text-brown-800 ml-1">brouillon</span>}</h2>
            <div className="flex items-center gap-3">
              <Toggle on={c.is_published} onChange={(v) => toggle('course', c.id, 'is_published', v)} label="Publié" />
              <Link href={`/code/${c.slug}`} target="_blank" className="text-xs text-brown-700 hover:underline">Aperçu ↗</Link>
              <a href={djangoAdmin(`course/${c.id}/change/`)} target="_blank" rel="noreferrer" className="text-xs text-brown-700 hover:underline">Modifier ↗</a>
            </div>
          </div>
          <div className="space-y-3">
            {c.sections.map((s) => (
              <div key={s.id} className="border border-cream-200 rounded-xl p-3">
                <div className="flex flex-wrap items-center justify-between gap-2 mb-2">
                  <strong>{s.order}. {s.title}</strong>
                  <div className="flex items-center gap-3">
                    <Toggle on={s.is_free_preview} onChange={(v) => toggle('section', s.id, 'is_free_preview', v)} label="Chapitre gratuit (démo)" />
                    <label className="text-xs flex items-center gap-1">Seuil <input type="number" min={0} max={100} defaultValue={s.unlock_threshold} onBlur={(e) => Number(e.target.value) !== s.unlock_threshold && toggle('section', s.id, 'unlock_threshold', Number(e.target.value))} className="input-field !py-0.5 !px-1.5 w-16 text-xs" /> %</label>
                    <a href={djangoAdmin(`section/${s.id}/change/`)} target="_blank" rel="noreferrer" className="text-xs text-brown-700 hover:underline">Modifier ↗</a>
                  </div>
                </div>
                <ul className="text-sm divide-y divide-cream-200">
                  {s.lessons.map((l) => (
                    <li key={l.id} className="py-1.5 flex items-center gap-3">
                      <span className={l.is_published ? '' : 'text-brown-800/40'}>{l.title}</span>
                      {l.has_video && <span className="text-xs text-brown-800/50">▶ vidéo</span>}
                      <span className="text-xs text-brown-800/50">{l.minutes} min</span>
                      <span className="ml-auto text-xs text-brown-800/60">{l.completions} terminée(s)</span>
                      <Toggle on={l.is_published} onChange={(v) => toggle('lesson', l.id, 'is_published', v)} label="Publiée" />
                      <a href={djangoAdmin(`lesson/${l.id}/change/`)} target="_blank" rel="noreferrer" className="text-xs text-brown-700 hover:underline">Modifier ↗</a>
                    </li>
                  ))}
                  <li className="py-1.5 flex items-center gap-3 text-sm">
                    {s.quiz ? <><span>★ {s.quiz.title}</span><span className="text-xs text-brown-800/50">{s.quiz.questions} questions</span><span className="ml-auto text-xs text-brown-800/60">{s.quiz.attempts} tentative(s){s.quiz.pass_rate !== null ? ` · ${s.quiz.pass_rate} % de réussite` : ''}</span><a href={djangoAdmin(`quiz/${s.quiz.id}/change/`)} target="_blank" rel="noreferrer" className="text-xs text-brown-700 hover:underline">Modifier ↗</a></>
                      : <a href={djangoAdmin(`quiz/add/?section=${s.id}`)} target="_blank" rel="noreferrer" className="text-xs text-brown-700 hover:underline">+ Ajouter un quiz de fin de section</a>}
                  </li>
                </ul>
              </div>
            ))}
          </div>
        </section>
      ))}

      <section className="card">
        <div className="flex items-center justify-between mb-3"><h2 className="text-xl">Examens blancs</h2><a href={djangoAdmin('exam/add/')} target="_blank" rel="noreferrer" className="text-sm text-brown-700 hover:underline">+ Examen ↗</a></div>
        <table className="w-full text-sm">
          <thead className="text-brown-800/70"><tr><th className="text-left py-2">Titre</th><th className="text-right py-2">Questions</th><th className="text-right py-2">Tentatives</th><th className="text-right py-2">Réussite</th><th className="text-right py-2">Options</th></tr></thead>
          <tbody>{d.exams.map((e) => (
            <tr key={e.id} className="border-t border-cream-200">
              <td className="py-2">{e.title}</td>
              <td className="py-2 text-right">{Math.min(e.question_count, e.available)} / {e.question_count}{e.available < e.question_count && <span className="text-red-700 text-xs ml-1">banque insuffisante</span>}</td>
              <td className="py-2 text-right">{e.attempts}</td>
              <td className="py-2 text-right">{e.pass_rate !== null ? `${e.pass_rate} %` : '—'}</td>
              <td className="py-2 text-right space-x-3"><Toggle on={e.is_published} onChange={(v) => toggle('exam', e.id, 'is_published', v)} label="Publié" /><Toggle on={e.is_demo} onChange={(v) => toggle('exam', e.id, 'is_demo', v)} label="Série d'essai" /><a href={djangoAdmin(`exam/${e.id}/change/`)} target="_blank" rel="noreferrer" className="text-xs text-brown-700 hover:underline">Modifier ↗</a></td>
            </tr>
          ))}</tbody>
        </table>
      </section>
    </AdminShell>
  );
}
