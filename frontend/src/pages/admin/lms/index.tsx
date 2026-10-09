import { useCallback, useEffect, useState } from 'react';
import Link from 'next/link';
import api from '@/lib/api';
import { BACKOFFICE, useRequireAuth } from '@/hooks/useRequireAuth';
import AdminShell from '@/components/AdminShell';
import { AdminCourse, AdminExam, Theme } from '@/lib/lms';
import { apiError } from '@/lib/types';

const EXAM_EMPTY = { title: '', description: '', question_count: 40, seconds_per_question: 20, duration_minutes: 30, pass_score: 88, is_published: true, is_demo: false, distribution: {} as Record<string, number> };

function ExamForm({ exam, themes, onDone }: { exam: AdminExam | null; themes: Theme[]; onDone: () => void }) {
  const [f, setF] = useState<any>(exam ? { ...exam } : { ...EXAM_EMPTY, distribution: Object.fromEntries(themes.map((t) => [t.code, t.default_count])) });
  const [error, setError] = useState('');
  const total = Object.values(f.distribution as Record<string, number>).reduce((a, b) => a + Number(b || 0), 0);
  const save = async (e: React.FormEvent) => {
    e.preventDefault(); setError('');
    try { exam ? await api.patch(`/lms/admin/exams/${exam.id}/`, f) : await api.post('/lms/admin/exams/', f); onDone(); }
    catch (err) { setError(apiError(err, 'Enregistrement impossible.')); }
  };
  return (
    <form onSubmit={save} className="card border-brown-300 space-y-3">
      <h3 className="font-semibold">{exam ? `Modifier « ${exam.title} »` : 'Nouvel examen blanc'}</h3>
      <div className="grid sm:grid-cols-2 gap-2">
        <label className="block sm:col-span-2"><span className="text-xs text-brown-800/70">Titre</span><input required value={f.title} onChange={(e) => setF({ ...f, title: e.target.value })} className="input-field !py-2" /></label>
        <label className="block sm:col-span-2"><span className="text-xs text-brown-800/70">Description</span><input value={f.description} onChange={(e) => setF({ ...f, description: e.target.value })} className="input-field !py-2" /></label>
        <label className="block"><span className="text-xs text-brown-800/70">Nombre de questions</span><input type="number" min={1} value={f.question_count} onChange={(e) => setF({ ...f, question_count: Number(e.target.value) })} className="input-field !py-2" /></label>
        <label className="block"><span className="text-xs text-brown-800/70">Secondes par question (0 = chrono global)</span><input type="number" min={0} value={f.seconds_per_question} onChange={(e) => setF({ ...f, seconds_per_question: Number(e.target.value) })} className="input-field !py-2" /></label>
        <label className="block"><span className="text-xs text-brown-800/70">Durée globale (min, si pas de chrono par question)</span><input type="number" min={1} value={f.duration_minutes} onChange={(e) => setF({ ...f, duration_minutes: Number(e.target.value) })} className="input-field !py-2" /></label>
        <label className="block"><span className="text-xs text-brown-800/70">Réussite (%) — ETG : 35/40 = 88</span><input type="number" min={1} max={100} value={f.pass_score} onChange={(e) => setF({ ...f, pass_score: Number(e.target.value) })} className="input-field !py-2" /></label>
      </div>
      <div>
        <span className="text-xs text-brown-800/70">Répartition par thème (même répartition que l'examen national) — total {total} / {f.question_count}</span>
        <div className="grid grid-cols-5 sm:grid-cols-10 gap-1 mt-1">
          {themes.map((t) => <label key={t.code} className="block text-center"><span className="text-xs font-medium" title={t.title}>{t.code}</span><input type="number" min={0} value={f.distribution[t.code] ?? 0} onChange={(e) => setF({ ...f, distribution: { ...f.distribution, [t.code]: Number(e.target.value) } })} className="input-field !py-1 !px-1 text-center text-sm" /><span className="text-[10px] text-brown-800/50">{t.bank} en banque</span></label>)}
        </div>
      </div>
      <div className="flex gap-4 text-sm">
        <label className="flex items-center gap-1.5"><input type="checkbox" checked={f.is_published} onChange={(e) => setF({ ...f, is_published: e.target.checked })} className="accent-brown-700" /> Publié</label>
        <label className="flex items-center gap-1.5"><input type="checkbox" checked={f.is_demo} onChange={(e) => setF({ ...f, is_demo: e.target.checked })} className="accent-brown-700" /> Série d'essai gratuite (sans compte)</label>
      </div>
      {error && <p className="text-sm text-red-700">{error}</p>}
      <div className="flex gap-2"><button className="btn-primary !py-2 text-sm">Enregistrer</button><button type="button" onClick={onDone} className="btn-secondary !py-2 text-sm">Annuler</button></div>
    </form>
  );
}

export default function AdminLms() {
  const ready = useRequireAuth(BACKOFFICE);
  const [courses, setCourses] = useState<AdminCourse[] | null>(null);
  const [exams, setExams] = useState<AdminExam[]>([]);
  const [themes, setThemes] = useState<Theme[]>([]);
  const [learners, setLearners] = useState<{ with_access: number; active: number } | null>(null);
  const [newCourse, setNewCourse] = useState('');
  const [editExam, setEditExam] = useState<AdminExam | null | 'new'>(null);
  const [msg, setMsg] = useState<{ ok: boolean; text: string } | null>(null);
  const load = useCallback(() => Promise.all([
    api.get('/lms/admin/courses/').then((r) => setCourses(r.data)),
    api.get('/lms/admin/exams/').then((r) => setExams(r.data)),
    api.get('/lms/admin/themes/').then((r) => setThemes(r.data)),
    api.get('/lms/admin/overview/').then((r) => setLearners(r.data.learners)),
  ]), []);
  useEffect(() => { if (ready) load(); }, [ready, load]);
  const act = async (fn: () => Promise<unknown>, ok: string) => { setMsg(null); try { await fn(); await load(); setMsg({ ok: true, text: ok }); } catch (err) { setMsg({ ok: false, text: apiError(err, 'Action impossible.') }); } };

  if (!courses) return <AdminShell title="Contenus LMS"><p className="text-brown-500">Chargement…</p></AdminShell>;
  const bankTotal = themes.reduce((a, t) => a + t.bank, 0);

  return (
    <AdminShell title="Contenus LMS" wide>
      <div className="flex flex-wrap items-center justify-between gap-3 mb-2">
        <h1 className="text-3xl">Contenus LMS</h1>
        <div className="flex gap-2"><Link href="/admin/lms/bank" className="btn-secondary">Banque de questions</Link><Link href="/demo" target="_blank" className="btn-secondary">Démo publique ↗</Link></div>
      </div>
      <p className="text-brown-800/70 mb-6">Cours, thèmes, leçons, quiz et examens blancs se créent et se modifient ici, sans outil externe.</p>
      {msg && <div className={`rounded-xl px-4 py-3 mb-4 text-sm ${msg.ok ? 'border border-brown-300 bg-brown-50' : 'border border-red-200 bg-red-50 text-red-700'}`}>{msg.text}</div>}

      <div className="grid sm:grid-cols-4 gap-4 mb-8">
        <div className="card py-4"><p className="text-sm text-brown-800/70">Apprenants avec accès</p><p className="text-3xl font-display">{learners?.with_access ?? '—'}</p></div>
        <div className="card py-4"><p className="text-sm text-brown-800/70">Actifs (30 j)</p><p className="text-3xl font-display">{learners?.active ?? '—'}</p></div>
        <div className="card py-4"><p className="text-sm text-brown-800/70">Banque d'examen</p><p className="text-3xl font-display">{bankTotal}</p><p className="text-xs text-brown-800/60">{themes.filter((t) => t.bank < t.default_count).length} thème(s) sous la répartition officielle</p></div>
        <div className="card py-4"><p className="text-sm text-brown-800/70">Examens blancs</p><p className="text-3xl font-display">{exams.length}</p></div>
      </div>

      <section className="mb-8">
        <div className="flex flex-wrap items-center justify-between gap-2 mb-3"><h2 className="text-xl">Cours</h2>
          <form onSubmit={(e) => { e.preventDefault(); act(() => api.post('/lms/admin/courses/', { title: newCourse }), 'Cours créé.').then(() => setNewCourse('')); }} className="flex gap-2"><input required placeholder="Titre du nouveau cours" value={newCourse} onChange={(e) => setNewCourse(e.target.value)} className="input-field !py-2 w-64" /><button className="btn-primary !py-2 text-sm">+ Créer</button></form>
        </div>
        <div className="grid md:grid-cols-2 gap-4">
          {courses.map((c) => {
            const missing = themes.filter((t) => !c.sections.some((s) => s.code === t.code));
            return (
              <div key={c.id} className="card">
                <div className="flex items-start justify-between gap-2">
                  <div><h3 className="text-xl">{c.title} {!c.is_published && <span className="badge bg-cream-200 text-brown-800 ml-1">brouillon</span>}</h3><p className="text-sm text-brown-800/70">{c.sections.length} section(s) · {c.lesson_count} leçon(s) publiée(s)</p></div>
                  <label className="text-xs flex items-center gap-1"><input type="checkbox" checked={c.is_published} onChange={(e) => act(() => api.patch(`/lms/admin/courses/${c.id}/`, { is_published: e.target.checked }), e.target.checked ? 'Cours publié.' : 'Cours dépublié.')} className="accent-brown-700" /> Publié</label>
                </div>
                <div className="flex flex-wrap gap-1 mt-3">{c.sections.map((s) => <span key={s.id} className={`badge ${s.code ? 'bg-brown-700 text-cream-50' : 'bg-cream-200 text-brown-800'}`} title={s.title}>{s.code || s.title.slice(0, 12)} · {s.lessons.length}</span>)}</div>
                <div className="flex flex-wrap gap-2 mt-4">
                  <Link href={`/admin/lms/course/${c.id}`} className="btn-primary !py-1.5 text-sm">Éditer la structure</Link>
                  {missing.length > 0 && <button onClick={() => act(() => api.post(`/lms/admin/courses/${c.id}/seed_themes/`), `${missing.length} thème(s) officiel(s) ajouté(s).`)} className="btn-secondary !py-1.5 text-sm">+ Ajouter les {missing.length} thème(s) officiel(s) manquant(s)</button>}
                  <Link href={`/code/${c.slug}`} target="_blank" className="text-sm text-brown-700 hover:underline self-center">Aperçu élève ↗</Link>
                </div>
              </div>
            );
          })}
        </div>
      </section>

      <section className="card mb-8">
        <div className="flex items-center justify-between mb-3"><h2 className="text-xl">Examens blancs</h2><button onClick={() => setEditExam('new')} className="btn-secondary !py-1.5 text-sm">+ Examen</button></div>
        {editExam && <div className="mb-4"><ExamForm exam={editExam === 'new' ? null : editExam} themes={themes} onDone={() => { setEditExam(null); load(); }} /></div>}
        <table className="w-full text-sm">
          <thead className="text-brown-800/70"><tr><th className="text-left py-2">Titre</th><th className="text-right py-2">Questions</th><th className="text-right py-2">Chrono</th><th className="text-right py-2">Réussite</th><th className="text-right py-2">Tentatives</th><th className="text-right py-2">Taux</th><th className="text-right py-2"></th></tr></thead>
          <tbody>{exams.map((e) => (
            <tr key={e.id} className="border-t border-cream-200">
              <td className="py-2">{e.title} {e.is_demo && <span className="badge bg-caramel/40 text-brown-900 ml-1">essai gratuit</span>} {!e.is_published && <span className="badge bg-cream-200 text-brown-800 ml-1">brouillon</span>}</td>
              <td className="py-2 text-right">{Math.min(e.question_count, e.available)} / {e.question_count}{e.available < e.question_count && <span className="text-red-700 text-xs ml-1">banque insuffisante</span>}</td>
              <td className="py-2 text-right">{e.seconds_per_question ? `${e.seconds_per_question} s / question` : `${e.duration_minutes} min`}</td>
              <td className="py-2 text-right">{e.pass_score} %</td>
              <td className="py-2 text-right">{e.attempts}</td>
              <td className="py-2 text-right">{e.pass_rate !== null ? `${e.pass_rate} %` : '—'}</td>
              <td className="py-2 text-right whitespace-nowrap space-x-3"><button onClick={() => setEditExam(e)} className="text-brown-700 text-xs hover:underline">Modifier</button><button onClick={() => confirm(`Supprimer « ${e.title} » et ses tentatives ?`) && act(() => api.delete(`/lms/admin/exams/${e.id}/`), 'Examen supprimé.')} className="text-red-700 text-xs hover:underline">Supprimer</button></td>
            </tr>
          ))}</tbody>
        </table>
      </section>

      <section className="card">
        <div className="flex items-center justify-between mb-3"><h2 className="text-xl">Banque d'examen par thème officiel</h2><Link href="/admin/lms/bank" className="text-sm text-brown-700 hover:underline">Gérer la banque →</Link></div>
        <div className="grid sm:grid-cols-2 lg:grid-cols-5 gap-2 text-sm">
          {themes.map((t) => <Link key={t.code} href={`/admin/lms/bank?topic=${t.code}`} className={`rounded-xl px-3 py-2 border ${t.bank < t.default_count ? 'border-caramel bg-brown-50' : 'border-cream-200 bg-white'} hover:border-brown-300`}><span className="font-semibold">{t.code}</span> {t.title}<br /><span className="text-xs text-brown-800/60">{t.bank} question(s) · {t.default_count} par examen</span></Link>)}
        </div>
      </section>
    </AdminShell>
  );
}
