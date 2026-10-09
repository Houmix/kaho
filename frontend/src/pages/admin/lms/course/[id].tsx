import { useCallback, useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/router';
import api from '@/lib/api';
import { BACKOFFICE, useRequireAuth } from '@/hooks/useRequireAuth';
import AdminShell from '@/components/AdminShell';
import { AdminCourse, AdminSection, Theme } from '@/lib/lms';
import { apiError } from '@/lib/types';

export default function AdminCourseEditor() {
  const ready = useRequireAuth(BACKOFFICE);
  const router = useRouter();
  const id = typeof router.query.id === 'string' ? router.query.id : null;
  const [c, setC] = useState<AdminCourse | null>(null);
  const [themes, setThemes] = useState<Theme[]>([]);
  const [msg, setMsg] = useState<{ ok: boolean; text: string } | null>(null);
  const [newSection, setNewSection] = useState({ title: '', code: '' });
  const [newLesson, setNewLesson] = useState<Record<number, string>>({});
  const load = useCallback(() => id && api.get(`/lms/admin/courses/${id}/`).then((r) => setC(r.data)), [id]);
  useEffect(() => { if (ready && id) { load(); api.get('/lms/admin/themes/').then((r) => setThemes(r.data)); } }, [ready, id, load]);
  const act = async (fn: () => Promise<unknown>, ok: string) => { setMsg(null); try { await fn(); await load(); setMsg({ ok: true, text: ok }); } catch (err) { setMsg({ ok: false, text: apiError(err, 'Action impossible.') }); } };
  const move = (list: { id: number }[], idx: number, dir: -1 | 1, path: string) => {
    const ids = list.map((x) => x.id); const j = idx + dir; if (j < 0 || j >= ids.length) return;
    [ids[idx], ids[j]] = [ids[j], ids[idx]]; act(() => api.post(path, { ids }), 'Ordre mis à jour.');
  };

  if (!c) return <AdminShell title="Cours"><p className="text-brown-500">Chargement…</p></AdminShell>;
  const field = (k: keyof AdminCourse, label: string, textarea = false) => (
    <label className="block"><span className="text-xs text-brown-800/70">{label}</span>
      {textarea ? <textarea rows={2} defaultValue={String(c[k] ?? '')} onBlur={(e) => e.target.value !== c[k] && act(() => api.patch(`/lms/admin/courses/${c.id}/`, { [k]: e.target.value }), 'Cours mis à jour.')} className="input-field !py-2" />
        : <input defaultValue={String(c[k] ?? '')} onBlur={(e) => e.target.value !== c[k] && act(() => api.patch(`/lms/admin/courses/${c.id}/`, { [k]: e.target.value }), 'Cours mis à jour.')} className="input-field !py-2" />}</label>
  );

  return (
    <AdminShell title={c.title} wide>
      <Link href="/admin/lms" className="text-sm text-brown-700 hover:underline">← Contenus LMS</Link>
      <div className="flex flex-wrap items-start justify-between gap-3 mt-2 mb-4">
        <h1 className="text-3xl">{c.title}</h1>
        <div className="flex items-center gap-3">
          <label className="text-sm flex items-center gap-1.5"><input type="checkbox" checked={c.is_published} onChange={(e) => act(() => api.patch(`/lms/admin/courses/${c.id}/`, { is_published: e.target.checked }), 'Publication mise à jour.')} className="accent-brown-700" /> Publié</label>
          <Link href={`/code/${c.slug}`} target="_blank" className="btn-secondary !py-1.5 text-sm">Aperçu élève ↗</Link>
          <button onClick={() => confirm(`Supprimer le cours « ${c.title} », ses sections, leçons et quiz ?`) && api.delete(`/lms/admin/courses/${c.id}/`).then(() => router.push('/admin/lms'))} className="text-red-700 text-sm hover:underline">Supprimer</button>
        </div>
      </div>
      {msg && <div className={`rounded-xl px-4 py-3 mb-4 text-sm ${msg.ok ? 'border border-brown-300 bg-brown-50' : 'border border-red-200 bg-red-50 text-red-700'}`}>{msg.text}</div>}

      <div className="grid lg:grid-cols-[320px_1fr] gap-6">
        <section className="card space-y-3 self-start">
          <h2 className="text-xl">Informations</h2>
          {field('title', 'Titre')}{field('description', 'Description', true)}{field('cover_url', 'Image de couverture (URL)')}
          <p className="text-xs text-brown-800/50">Adresse : /code/{c.slug}</p>
          <form onSubmit={(e) => { e.preventDefault(); act(() => api.post('/lms/admin/sections/', { course: c.id, title: newSection.title || (themes.find((t) => t.code === newSection.code)?.title ?? ''), code: newSection.code, order: c.sections.length + 1, unlock_threshold: 0 }), 'Section ajoutée.').then(() => setNewSection({ title: '', code: '' })); }} className="border-t border-cream-200 pt-3 space-y-2">
            <h3 className="font-semibold text-sm">Ajouter une section</h3>
            <select value={newSection.code} onChange={(e) => setNewSection({ ...newSection, code: e.target.value })} className="input-field !py-2 text-sm"><option value="">Section libre (hors thème officiel)</option>{themes.map((t) => <option key={t.code} value={t.code}>{t.code} — {t.title}</option>)}</select>
            <input placeholder="Titre (optionnel si thème)" value={newSection.title} onChange={(e) => setNewSection({ ...newSection, title: e.target.value })} className="input-field !py-2 text-sm" />
            <button className="btn-primary !py-2 text-sm w-full">+ Ajouter</button>
          </form>
        </section>

        <div className="space-y-4">
          {c.sections.length === 0 && <p className="text-brown-800/60">Aucune section. Ajoutez les thèmes officiels depuis la page Contenus LMS ou créez une section.</p>}
          {c.sections.map((s: AdminSection, idx) => (
            <section key={s.id} className="card">
              <div className="flex flex-wrap items-center gap-2 mb-2">
                <div className="flex flex-col gap-0.5"><button onClick={() => move(c.sections, idx, -1, '/lms/admin/sections/reorder/')} disabled={idx === 0} className="text-xs text-brown-800/50 disabled:opacity-30">▲</button><button onClick={() => move(c.sections, idx, 1, '/lms/admin/sections/reorder/')} disabled={idx === c.sections.length - 1} className="text-xs text-brown-800/50 disabled:opacity-30">▼</button></div>
                {s.code && <span className="badge bg-brown-700 text-cream-50">{s.code}</span>}
                <input defaultValue={s.title} onBlur={(e) => e.target.value !== s.title && act(() => api.patch(`/lms/admin/sections/${s.id}/`, { title: e.target.value }), 'Section renommée.')} className="input-field !py-1.5 font-semibold flex-1 min-w-48" />
                <select value={s.code} onChange={(e) => act(() => api.patch(`/lms/admin/sections/${s.id}/`, { code: e.target.value }), 'Thème mis à jour.')} className="input-field !py-1.5 text-xs w-44"><option value="">Hors thème</option>{themes.map((t) => <option key={t.code} value={t.code}>{t.code} — {t.title}</option>)}</select>
                <label className="text-xs flex items-center gap-1"><input type="checkbox" checked={s.is_free_preview} onChange={(e) => act(() => api.patch(`/lms/admin/sections/${s.id}/`, { is_free_preview: e.target.checked }), 'Démo mise à jour.')} className="accent-brown-700" /> gratuit (démo)</label>
                <label className="text-xs flex items-center gap-1">verrou <input type="number" min={0} max={100} defaultValue={s.unlock_threshold} onBlur={(e) => Number(e.target.value) !== s.unlock_threshold && act(() => api.patch(`/lms/admin/sections/${s.id}/`, { unlock_threshold: Number(e.target.value) }), 'Seuil mis à jour.')} className="input-field !py-0.5 !px-1 w-14 text-xs" /> %</label>
                <button onClick={() => confirm(`Supprimer la section « ${s.title} » et ses ${s.lessons.length} leçon(s) ?`) && act(() => api.delete(`/lms/admin/sections/${s.id}/`), 'Section supprimée.')} className="text-red-700 text-xs hover:underline ml-auto">Supprimer</button>
              </div>
              <ul className="text-sm divide-y divide-cream-200">
                {s.lessons.map((l, li) => (
                  <li key={l.id} className="py-1.5 flex items-center gap-2">
                    <div className="flex gap-1"><button onClick={() => move(s.lessons, li, -1, '/lms/admin/lessons/reorder/')} disabled={li === 0} className="text-[10px] text-brown-800/50 disabled:opacity-30">▲</button><button onClick={() => move(s.lessons, li, 1, '/lms/admin/lessons/reorder/')} disabled={li === s.lessons.length - 1} className="text-[10px] text-brown-800/50 disabled:opacity-30">▼</button></div>
                    <Link href={`/admin/lms/lesson/${l.id}`} className={`font-medium text-brown-700 hover:underline ${!l.is_published ? 'opacity-60' : ''}`}>{l.title}</Link>
                    {l.has_video && <span className="text-xs text-brown-800/50">▶ vidéo</span>}<span className="text-xs text-brown-800/50">{l.minutes} min</span>
                    <span className="ml-auto text-xs text-brown-800/60">{l.completions} terminée(s)</span>
                    <label className="text-xs flex items-center gap-1"><input type="checkbox" checked={l.is_published} onChange={(e) => act(() => api.patch(`/lms/admin/lessons/${l.id}/`, { is_published: e.target.checked }), 'Leçon mise à jour.')} className="accent-brown-700" /> publiée</label>
                  </li>
                ))}
                <li className="py-1.5 flex items-center gap-2">
                  <form onSubmit={(e) => { e.preventDefault(); act(() => api.post('/lms/admin/lessons/', { section: s.id, title: newLesson[s.id], order: s.lessons.length + 1, is_published: false }), 'Leçon créée (brouillon).').then(() => setNewLesson({ ...newLesson, [s.id]: '' })); }} className="flex gap-2 flex-1"><input required placeholder="Titre de la nouvelle leçon" value={newLesson[s.id] || ''} onChange={(e) => setNewLesson({ ...newLesson, [s.id]: e.target.value })} className="input-field !py-1 text-xs flex-1" /><button className="btn-secondary !py-1 text-xs">+ Leçon</button></form>
                  {s.quiz ? <Link href={`/admin/lms/quiz/${s.quiz.id}`} className="text-xs text-brown-700 font-medium hover:underline whitespace-nowrap">★ {s.quiz.title} ({s.quiz.questions} q.{s.quiz.attempts ? ` · ${s.quiz.pass_rate} % réussite` : ''})</Link>
                    : <button onClick={() => act(() => api.post(`/lms/admin/sections/${s.id}/add_quiz/`), 'Quiz créé.')} className="text-xs text-brown-700 hover:underline whitespace-nowrap">+ Quiz de fin de section</button>}
                </li>
              </ul>
            </section>
          ))}
        </div>
      </div>
    </AdminShell>
  );
}
