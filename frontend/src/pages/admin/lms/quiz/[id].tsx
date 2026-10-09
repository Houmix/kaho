import { useCallback, useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/router';
import api from '@/lib/api';
import { BACKOFFICE, useRequireAuth } from '@/hooks/useRequireAuth';
import AdminShell from '@/components/AdminShell';
import QuestionEditor from '@/components/QuestionEditor';
import Markdown from '@/components/Markdown';
import { AdminQuestion, AdminQuiz, KIND_LABEL, Theme } from '@/lib/lms';
import { apiError } from '@/lib/types';

export default function AdminQuizEditor() {
  const ready = useRequireAuth(BACKOFFICE);
  const router = useRouter();
  const id = typeof router.query.id === 'string' ? router.query.id : null;
  const [quiz, setQuiz] = useState<AdminQuiz | null>(null);
  const [questions, setQuestions] = useState<AdminQuestion[]>([]);
  const [themes, setThemes] = useState<Theme[]>([]);
  const [editing, setEditing] = useState<AdminQuestion | null | 'new'>(null);
  const [msg, setMsg] = useState<{ ok: boolean; text: string } | null>(null);
  const load = useCallback(() => id && Promise.all([api.get(`/lms/admin/quizzes/${id}/`).then((r) => setQuiz(r.data)), api.get(`/lms/admin/quizzes/${id}/questions/`).then((r) => setQuestions(r.data))]), [id]);
  useEffect(() => { if (ready && id) { load(); api.get('/lms/admin/themes/').then((r) => setThemes(r.data)); } }, [ready, id, load]);
  const act = async (fn: () => Promise<unknown>, ok: string) => { setMsg(null); try { await fn(); await load(); setMsg({ ok: true, text: ok }); } catch (err) { setMsg({ ok: false, text: apiError(err, 'Action impossible.') }); } };
  const move = (idx: number, dir: -1 | 1) => { const ids = questions.map((q) => q.id); const j = idx + dir; if (j < 0 || j >= ids.length) return; [ids[idx], ids[j]] = [ids[j], ids[idx]]; act(() => api.post('/lms/admin/questions/reorder/', { ids }), 'Ordre mis à jour.'); };

  if (!quiz) return <AdminShell title="Quiz"><p className="text-brown-500">Chargement…</p></AdminShell>;
  return (
    <AdminShell title={quiz.title} wide>
      <Link href="/admin/lms" className="text-sm text-brown-700 hover:underline">← Contenus LMS</Link>
      <div className="flex flex-wrap items-center justify-between gap-3 mt-2 mb-4">
        <div><h1 className="text-3xl">{quiz.title}</h1><p className="text-sm text-brown-800/70">{quiz.section_title ? `Fin de section : ${quiz.section_title}` : `Leçon : ${quiz.lesson_title}`} · {questions.length} question(s)</p></div>
        <div className="flex items-center gap-3 text-sm">
          <label className="block">Réussite <input type="number" min={1} max={100} defaultValue={quiz.pass_score} onBlur={(e) => Number(e.target.value) !== quiz.pass_score && act(() => api.patch(`/lms/admin/quizzes/${id}/`, { pass_score: Number(e.target.value) }), 'Seuil mis à jour.')} className="input-field !py-1 !px-2 w-16 text-sm" /> %</label>
          <label className="flex items-center gap-1.5"><input type="checkbox" checked={quiz.is_published} onChange={(e) => act(() => api.patch(`/lms/admin/quizzes/${id}/`, { is_published: e.target.checked }), 'Publication mise à jour.')} className="accent-brown-700" /> Publié</label>
          <Link href={`/code/quiz/${quiz.id}`} target="_blank" className="btn-secondary !py-1.5 text-sm">Aperçu élève ↗</Link>
        </div>
      </div>
      <input defaultValue={quiz.title} onBlur={(e) => e.target.value !== quiz.title && act(() => api.patch(`/lms/admin/quizzes/${id}/`, { title: e.target.value }), 'Titre mis à jour.')} className="input-field !py-2 mb-4 max-w-lg" aria-label="Titre du quiz" />
      {msg && <div className={`rounded-xl px-4 py-3 mb-4 text-sm ${msg.ok ? 'border border-brown-300 bg-brown-50' : 'border border-red-200 bg-red-50 text-red-700'}`}>{msg.text}</div>}

      <div className="space-y-3 mb-4">
        {questions.map((q, i) => editing !== 'new' && editing?.id === q.id ? (
          <QuestionEditor key={q.id} question={q} themes={themes} onSaved={() => { setEditing(null); load(); setMsg({ ok: true, text: 'Question enregistrée.' }); }} onCancel={() => setEditing(null)} />
        ) : (
          <article key={q.id} className={`card py-3 ${!q.is_published ? 'opacity-60' : ''}`}>
            <div className="flex items-start gap-3">
              <div className="flex flex-col gap-0.5 pt-1"><button onClick={() => move(i, -1)} disabled={i === 0} className="text-xs text-brown-800/50 disabled:opacity-30">▲</button><button onClick={() => move(i, 1)} disabled={i === questions.length - 1} className="text-xs text-brown-800/50 disabled:opacity-30">▼</button></div>
              <div className="flex-1 min-w-0">
                <p className="text-xs uppercase tracking-wide text-caramel font-medium">Q{i + 1} · {KIND_LABEL[q.kind]}{q.topic ? ` · ${q.topic_label}` : ''}{q.in_exam_bank && ' · banque'}</p>
                <Markdown className="prose-compact">{q.text_md}</Markdown>
                {q.choices.length > 0 && <ul className="mt-1 text-sm flex flex-wrap gap-x-4 gap-y-0.5">{q.choices.map((c) => <li key={c.id} className={c.is_correct ? 'text-brown-700 font-medium' : 'text-brown-800/60'}>{c.is_correct ? '✓' : '○'} {c.text}</li>)}</ul>}
                {!q.choices.length && <p className="text-sm text-brown-800/70">Réponse : <code className="bg-cream-200 px-1 rounded">{q.expected_answer}</code></p>}
              </div>
              <div className="flex flex-col gap-1 text-xs whitespace-nowrap">
                <button onClick={() => setEditing(q)} className="text-brown-700 hover:underline">Modifier</button>
                <button onClick={() => act(() => api.post(`/lms/admin/questions/${q.id}/duplicate/`), 'Question dupliquée.')} className="text-brown-700 hover:underline">Dupliquer</button>
                <button onClick={() => confirm('Supprimer cette question ?') && act(() => api.delete(`/lms/admin/questions/${q.id}/`), 'Question supprimée.')} className="text-red-700 hover:underline">Supprimer</button>
              </div>
            </div>
          </article>
        ))}
      </div>
      {editing === 'new' ? <QuestionEditor quizId={quiz.id} themes={themes} onSaved={() => { setEditing(null); load(); setMsg({ ok: true, text: 'Question ajoutée.' }); }} onCancel={() => setEditing(null)} />
        : <button onClick={() => setEditing('new')} className="btn-primary">+ Ajouter une question</button>}
      <div className="flex items-center justify-between mt-8 border-t border-cream-200 pt-4 text-sm">
        <Link href="/admin/lms" className="text-brown-700 hover:underline">← Retour aux contenus LMS</Link>
        <button onClick={() => confirm('Supprimer ce quiz et ses questions ?') && api.delete(`/lms/admin/quizzes/${id}/`).then(() => router.push('/admin/lms'))} className="text-red-700 hover:underline text-xs">Supprimer le quiz</button>
      </div>
    </AdminShell>
  );
}
