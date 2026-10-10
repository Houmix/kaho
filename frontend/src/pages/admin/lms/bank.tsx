import { useCallback, useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/router';
import api from '@/lib/api';
import { BACKOFFICE, useRequireAuth } from '@/hooks/useRequireAuth';
import AdminShell from '@/components/AdminShell';
import QuestionEditor from '@/components/QuestionEditor';
import Markdown from '@/components/Markdown';
import { AdminQuestion, KIND_LABEL, Theme } from '@/lib/lms';
import { apiError } from '@/lib/types';

export default function AdminQuestionBank() {
  const ready = useRequireAuth(BACKOFFICE);
  const router = useRouter();
  const [themes, setThemes] = useState<Theme[]>([]);
  const [topic, setTopic] = useState('');
  const [q, setQ] = useState('');
  const [onlyBank, setOnlyBank] = useState(true);
  const [success, setSuccess] = useState('');
  const [items, setItems] = useState<AdminQuestion[] | null>(null);
  const [editing, setEditing] = useState<AdminQuestion | null | 'new'>(null);
  const [msg, setMsg] = useState<{ ok: boolean; text: string } | null>(null);
  useEffect(() => { if (router.isReady && typeof router.query.topic === 'string') setTopic(router.query.topic); }, [router.isReady, router.query]);
  const load = useCallback(() => Promise.all([
    api.get('/lms/admin/questions/', { params: { topic: topic || undefined, q: q || undefined, bank: onlyBank ? 1 : undefined, with_stats: 1, sort: success ? 'success' : undefined, max_success: success && success !== 'none' ? success : undefined, unanswered: success === 'none' ? 1 : undefined } }).then((r) => setItems(r.data)),
    api.get('/lms/admin/themes/').then((r) => setThemes(r.data)),
  ]), [topic, q, onlyBank, success]);
  useEffect(() => { if (!ready) return; const t = setTimeout(load, 200); return () => clearTimeout(t); }, [ready, load]);
  const act = async (fn: () => Promise<unknown>, ok: string) => { setMsg(null); try { await fn(); await load(); setMsg({ ok: true, text: ok }); } catch (err) { setMsg({ ok: false, text: apiError(err, 'Action impossible.') }); } };

  return (
    <AdminShell title="Banque de questions" wide>
      <Link href="/admin/lms" className="text-sm text-brown-700 hover:underline">← Contenus LMS</Link>
      <div className="flex flex-wrap items-center justify-between gap-3 mt-2 mb-2"><h1 className="text-3xl">Banque de questions</h1><button onClick={() => setEditing('new')} className="btn-primary">+ Nouvelle question</button></div>
      <p className="text-brown-800/70 mb-4">Les questions marquées « banque » alimentent les examens blancs (tirage selon la répartition officielle). Une question peut aussi appartenir à un quiz de thème.</p>
      {msg && <div className={`rounded-xl px-4 py-3 mb-4 text-sm ${msg.ok ? 'border border-brown-300 bg-brown-50' : 'border border-red-200 bg-red-50 text-red-700'}`}>{msg.text}</div>}
      <div className="flex flex-wrap gap-1 mb-3">
        <button onClick={() => setTopic('')} className={`badge !px-3 !py-1.5 ${topic === '' ? 'bg-brown-700 text-cream-50' : 'bg-cream-100 text-brown-800'}`}>Tous</button>
        {themes.map((t) => <button key={t.code} onClick={() => setTopic(t.code)} title={t.title} className={`badge !px-3 !py-1.5 ${topic === t.code ? 'bg-brown-700 text-cream-50' : t.bank < t.default_count ? 'bg-caramel/40 text-brown-900' : 'bg-cream-100 text-brown-800'}`}>{t.code} · {t.bank}/{t.default_count}</button>)}
      </div>
      <div className="flex flex-wrap gap-2 mb-4 items-center">
        <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Rechercher dans les énoncés…" className="input-field !py-2 sm:w-72" />
        <label className="text-sm flex items-center gap-1.5"><input type="checkbox" checked={onlyBank} onChange={(e) => setOnlyBank(e.target.checked)} className="accent-brown-700" /> Banque d'examen uniquement</label>
        <select value={success} onChange={(e) => setSuccess(e.target.value)} className="input-field !py-2 sm:w-60" aria-label="Taux de réussite">
          <option value="">Tous les taux de réussite</option>
          <option value="50">Taux de réussite ≤ 50 % (difficiles)</option>
          <option value="70">Taux de réussite ≤ 70 %</option>
          <option value="100">Triées par difficulté</option>
          <option value="none">Jamais posées</option>
        </select>
        <span className="text-sm text-brown-800/60">{items?.length ?? '…'} question(s)</span>
      </div>
      {editing === 'new' && <div className="mb-4"><QuestionEditor themes={themes} onSaved={() => { setEditing(null); load(); setMsg({ ok: true, text: 'Question ajoutée à la banque.' }); }} onCancel={() => setEditing(null)} /></div>}
      <div className="space-y-3">
        {items?.map((it) => editing !== 'new' && editing?.id === it.id ? (
          <QuestionEditor key={it.id} question={it} themes={themes} onSaved={() => { setEditing(null); load(); setMsg({ ok: true, text: 'Question enregistrée.' }); }} onCancel={() => setEditing(null)} />
        ) : (
          <article key={it.id} className={`card py-3 ${!it.is_published ? 'opacity-60' : ''}`}>
            <div className="flex items-start gap-3">
              <div className="flex-1 min-w-0">
                <p className="text-xs uppercase tracking-wide text-caramel font-medium">{it.topic_label} · {KIND_LABEL[it.kind]}{it.quiz_title && ` · quiz : ${it.quiz_title}`}{!it.in_exam_bank && ' · hors banque'}{typeof it.success_rate === 'number' && <span className={`ml-2 badge normal-case tracking-normal ${it.success_rate <= 50 ? 'bg-red-100 text-red-700' : 'bg-cream-200 text-brown-800'}`}>{it.success_rate} % de réussite · {it.answers_count} réponse(s)</span>}</p>
                <Markdown className="prose-compact">{it.text_md}</Markdown>
                {it.choices.length > 0 && <ul className="mt-1 text-sm flex flex-wrap gap-x-4 gap-y-0.5">{it.choices.map((c) => <li key={c.id} className={c.is_correct ? 'text-brown-700 font-medium' : 'text-brown-800/60'}>{c.is_correct ? '✓' : '○'} {c.text}</li>)}</ul>}
              </div>
              <div className="flex flex-col gap-1 text-xs whitespace-nowrap">
                <button onClick={() => setEditing(it)} className="text-brown-700 hover:underline">Modifier</button>
                <button onClick={() => act(() => api.post(`/lms/admin/questions/${it.id}/duplicate/`), 'Question dupliquée.')} className="text-brown-700 hover:underline">Dupliquer</button>
                <button onClick={() => confirm('Supprimer cette question ?') && act(() => api.delete(`/lms/admin/questions/${it.id}/`), 'Question supprimée.')} className="text-red-700 hover:underline">Supprimer</button>
              </div>
            </div>
          </article>
        ))}
        {items && items.length === 0 && <p className="text-brown-800/60">Aucune question pour ce filtre.</p>}
      </div>
    </AdminShell>
  );
}
