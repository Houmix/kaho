import { useCallback, useEffect, useRef, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/router';
import api from '@/lib/api';
import { BACKOFFICE, useRequireAuth } from '@/hooks/useRequireAuth';
import AdminShell from '@/components/AdminShell';
import Markdown from '@/components/Markdown';
import { AdminCourse, AdminLesson } from '@/lib/lms';
import { apiError } from '@/lib/types';

export default function AdminLessonEditor() {
  const ready = useRequireAuth(BACKOFFICE);
  const router = useRouter();
  const id = typeof router.query.id === 'string' ? router.query.id : null;
  const [l, setL] = useState<AdminLesson | null>(null);
  const [f, setF] = useState<Partial<AdminLesson>>({});
  const [courses, setCourses] = useState<AdminCourse[]>([]);
  const [msg, setMsg] = useState<{ ok: boolean; text: string } | null>(null);
  const [busy, setBusy] = useState(false);
  const [preview, setPreview] = useState(true);
  const ta = useRef<HTMLTextAreaElement>(null);
  const load = useCallback(() => id && api.get(`/lms/admin/lessons/${id}/`).then((r) => { setL(r.data); setF(r.data); }), [id]);
  useEffect(() => { if (ready && id) { load(); api.get('/lms/admin/courses/').then((r) => setCourses(r.data)); } }, [ready, id, load]);
  const dirty = l && JSON.stringify(f) !== JSON.stringify(l);
  const save = async () => {
    setBusy(true); setMsg(null);
    try { const r = await api.patch(`/lms/admin/lessons/${id}/`, f); setL(r.data); setF(r.data); setMsg({ ok: true, text: 'Leçon enregistrée.' }); }
    catch (err) { setMsg({ ok: false, text: apiError(err, 'Enregistrement impossible.') }); }
    finally { setBusy(false); }
  };
  const insert = (snippet: string) => {
    const el = ta.current; const v = f.content_md || '';
    if (!el) { setF({ ...f, content_md: v + '\n' + snippet }); return; }
    const s = el.selectionStart, e = el.selectionEnd;
    setF({ ...f, content_md: v.slice(0, s) + snippet + v.slice(e) });
  };
  const upload = async (file: File | undefined) => {
    if (!file) return;
    const fd = new FormData(); fd.append('file', file); fd.append('title', file.name);
    try { const r = await api.post(`/lms/admin/lessons/${id}/upload_asset/`, fd, { headers: { 'Content-Type': 'multipart/form-data' } }); insert(`\n${r.data.markdown}\n`); setMsg({ ok: true, text: 'Image ajoutée dans le contenu.' }); }
    catch (err) { setMsg({ ok: false, text: apiError(err, 'Envoi impossible.') }); }
  };
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => { if ((e.metaKey || e.ctrlKey) && e.key === 's') { e.preventDefault(); if (dirty) save(); } };
    window.addEventListener('keydown', onKey); return () => window.removeEventListener('keydown', onKey);
  });

  if (!l) return <AdminShell title="Leçon"><p className="text-brown-500">Chargement…</p></AdminShell>;
  const course = courses.find((c) => c.sections.some((s) => s.id === l.section));
  const sections = courses.flatMap((c) => c.sections.map((s) => ({ ...s, courseTitle: c.title })));

  return (
    <AdminShell title={l.title} wide>
      <Link href={course ? `/admin/lms/course/${course.id}` : '/admin/lms'} className="text-sm text-brown-700 hover:underline">← {course?.title ?? 'Contenus LMS'}</Link>
      <div className="flex flex-wrap items-center justify-between gap-3 mt-2 mb-4">
        <h1 className="text-3xl">{l.title}</h1>
        <div className="flex items-center gap-2">
          {l.quiz_id ? <Link href={`/admin/lms/quiz/${l.quiz_id}`} className="btn-secondary !py-1.5 text-sm">Quiz de la leçon</Link> : <button onClick={() => api.post(`/lms/admin/lessons/${id}/add_quiz/`).then(() => { load(); })} className="btn-secondary !py-1.5 text-sm">+ Quiz de leçon</button>}
          <Link href={course ? `/code/${course.slug}/${l.slug}` : '#'} target="_blank" className="btn-secondary !py-1.5 text-sm">Aperçu élève ↗</Link>
          <button onClick={save} disabled={!dirty || busy} className="btn-primary !py-1.5 text-sm disabled:opacity-50">{busy ? 'Enregistrement…' : dirty ? 'Enregistrer (⌘S)' : 'Enregistré'}</button>
        </div>
      </div>
      {msg && <div className={`rounded-xl px-4 py-3 mb-4 text-sm ${msg.ok ? 'border border-brown-300 bg-brown-50' : 'border border-red-200 bg-red-50 text-red-700'}`}>{msg.text}</div>}

      <div className="card grid sm:grid-cols-2 lg:grid-cols-5 gap-3 mb-4">
        <label className="block lg:col-span-2"><span className="text-xs text-brown-800/70">Titre</span><input value={f.title ?? ''} onChange={(e) => setF({ ...f, title: e.target.value })} className="input-field !py-2" /></label>
        <label className="block"><span className="text-xs text-brown-800/70">Section</span><select value={f.section ?? ''} onChange={(e) => setF({ ...f, section: Number(e.target.value) })} className="input-field !py-2">{sections.map((s) => <option key={s.id} value={s.id}>{s.courseTitle} › {s.title}</option>)}</select></label>
        <label className="block"><span className="text-xs text-brown-800/70">Durée estimée (min)</span><input type="number" min={1} value={f.estimated_minutes ?? 10} onChange={(e) => setF({ ...f, estimated_minutes: Number(e.target.value) })} className="input-field !py-2" /></label>
        <label className="flex items-center gap-2 text-sm self-end pb-2"><input type="checkbox" checked={!!f.is_published} onChange={(e) => setF({ ...f, is_published: e.target.checked })} className="accent-brown-700" /> Publiée</label>
        <label className="block lg:col-span-5"><span className="text-xs text-brown-800/70">Vidéo (lien YouTube, Vimeo ou fichier .mp4) — la veille de l'écran est bloquée pendant la lecture</span><input value={f.video_url ?? ''} onChange={(e) => setF({ ...f, video_url: e.target.value })} placeholder="https://www.youtube.com/watch?v=…" className="input-field !py-2" /></label>
      </div>

      <div className="flex flex-wrap gap-1 mb-2 text-xs">
        {[['## Titre', '\n## Titre de partie\n'], ['Liste', '\n- point 1\n- point 2\n'], ['Tableau', '\n| Colonne | Colonne |\n|---|---|\n| a | b |\n'], ['Encadré', '\n> À retenir : …\n'], ['Code', '\n```text\nschéma ou code\n```\n'], ['Lien', '[texte](https://)']].map(([lbl, snip]) => <button key={lbl} onClick={() => insert(snip)} className="badge bg-cream-100 text-brown-800 hover:bg-cream-200">{lbl}</button>)}
        <label className="badge bg-cream-100 text-brown-800 hover:bg-cream-200 cursor-pointer">Image / schéma… <input type="file" accept=".png,.jpg,.jpeg,.pdf" className="hidden" onChange={(e) => upload(e.target.files?.[0])} /></label>
        <button onClick={() => setPreview((v) => !v)} className="badge bg-cream-100 text-brown-800 ml-auto">{preview ? 'Masquer l’aperçu' : 'Afficher l’aperçu'}</button>
      </div>
      <div className={`grid gap-4 ${preview ? 'lg:grid-cols-2' : ''}`}>
        <textarea ref={ta} value={f.content_md ?? ''} onChange={(e) => setF({ ...f, content_md: e.target.value })} rows={28} spellCheck={false} className="input-field font-mono text-sm leading-relaxed" placeholder="Contenu de la leçon en Markdown…" />
        {preview && <div className="card overflow-auto max-h-[42rem]"><Markdown>{f.content_md || '*Aperçu vide*'}</Markdown></div>}
      </div>
      <p className="text-xs text-brown-800/50 mt-3">{l.completions} élève(s) ont terminé cette leçon. <button onClick={() => confirm('Supprimer cette leçon ?') && api.delete(`/lms/admin/lessons/${id}/`).then(() => router.push(course ? `/admin/lms/course/${course.id}` : '/admin/lms'))} className="text-red-700 hover:underline">Supprimer la leçon</button></p>
    </AdminShell>
  );
}
