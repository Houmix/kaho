import { useCallback, useEffect, useState } from 'react';
import { useRouter } from 'next/router';
import api from '@/lib/api';
import { useRequireAuth } from '@/hooks/useRequireAuth';
import AdminShell from '@/components/AdminShell';
import { InstructorAdmin, Paginated, RatingAdmin } from '@/lib/admin';
import { apiError, frDate } from '@/lib/types';

function Row({ r, onChange }: { r: RatingAdmin; onChange: (text: string, ok?: boolean) => void }) {
  const [reply, setReply] = useState(r.reply);
  const save = async (data: object, text: string) => {
    try { await api.patch(`/admin/ratings/${r.id}/`, data); onChange(text); }
    catch (err) { onChange(apiError(err, 'Enregistrement impossible.'), false); }
  };
  return (
    <article className={`card ${r.is_hidden ? 'opacity-60' : ''} ${r.score <= 2 && !r.reply ? 'border-caramel' : ''}`}>
      <div className="flex flex-wrap justify-between gap-2 text-sm">
        <div><span className="text-caramel text-lg">{'★'.repeat(r.score)}<span className="text-cream-300">{'★'.repeat(5 - r.score)}</span></span> <strong>{r.instructor_name}</strong> <span className="text-brown-800/60">noté par {r.student_name} · leçon du {frDate(r.lesson_date, { day: 'numeric', month: 'short' })}</span></div>
        <label className="flex items-center gap-2 text-brown-800/70"><input type="checkbox" checked={r.is_hidden} onChange={(e) => save({ is_hidden: e.target.checked }, e.target.checked ? 'Avis masqué (exclu des moyennes).' : 'Avis réaffiché.')} className="accent-brown-700" /> Masquer</label>
      </div>
      {r.comment ? <p className="mt-2">« {r.comment} »</p> : <p className="mt-2 text-brown-800/40 text-sm">Sans commentaire</p>}
      <div className="mt-3 flex gap-2 items-start">
        <textarea value={reply} onChange={(e) => setReply(e.target.value)} rows={2} placeholder="Réponse de l'école (visible par l'élève dans son livret)" className="input-field !py-2 text-sm" />
        <button onClick={() => save({ reply }, 'Réponse enregistrée.')} disabled={reply === r.reply} className="btn-primary !py-2 text-sm disabled:opacity-40">Répondre</button>
      </div>
    </article>
  );
}

export default function AdminReviews() {
  const ready = useRequireAuth(['SUPERVISOR', 'ADMIN']);
  const router = useRouter();
  const [instructor, setInstructor] = useState('');
  const [unanswered, setUnanswered] = useState(false);
  const [low, setLow] = useState(false);
  const [data, setData] = useState<Paginated<RatingAdmin> | null>(null);
  const [instructors, setInstructors] = useState<InstructorAdmin[]>([]);
  const [msg, setMsg] = useState<{ ok: boolean; text: string } | null>(null);

  useEffect(() => { if (router.isReady && typeof router.query.instructor === 'string') setInstructor(router.query.instructor); }, [router.isReady, router.query]);
  const load = useCallback(() => api.get('/admin/ratings/', { params: { instructor: instructor || undefined, unanswered: unanswered ? 1 : undefined, max_score: low ? 3 : undefined, page_size: 100 } }).then((r) => setData(r.data)), [instructor, unanswered, low]);
  useEffect(() => { if (ready) { load(); api.get('/admin/instructors/', { params: { page_size: 200 } }).then((r) => setInstructors(r.data.results)); } }, [ready, load]);

  return (
    <AdminShell title="Avis des élèves">
      <h1 className="text-3xl mb-2">Avis des élèves</h1>
      <p className="text-brown-800/70 mb-6">Répondez aux avis (la réponse apparaît dans le livret de l'élève) ou masquez ceux qui sont inappropriés — ils sont alors exclus des moyennes.</p>
      {msg && <div className={`rounded-xl px-4 py-3 mb-4 text-sm ${msg.ok ? 'border border-brown-300 bg-brown-50' : 'border border-red-200 bg-red-50 text-red-700'}`}>{msg.text}</div>}
      <div className="flex flex-wrap gap-3 items-center mb-6">
        <select value={instructor} onChange={(e) => setInstructor(e.target.value)} className="input-field sm:w-56 !py-2"><option value="">Tous les moniteurs</option>{instructors.map((i) => <option key={i.id} value={i.id}>{i.full_name}</option>)}</select>
        <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={unanswered} onChange={(e) => setUnanswered(e.target.checked)} className="accent-brown-700" /> Sans réponse</label>
        <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={low} onChange={(e) => setLow(e.target.checked)} className="accent-brown-700" /> Notes ≤ 3</label>
        {data && <span className="text-sm text-brown-800/60 ml-auto">{data.count} avis</span>}
      </div>
      {!data ? <p className="text-brown-500">Chargement…</p> : data.results.length === 0 ? <p className="text-brown-800/60">Aucun avis.</p> : (
        <div className="space-y-3">{data.results.map((r) => <Row key={r.id} r={r} onChange={(text, ok = true) => { setMsg({ ok, text }); load(); }} />)}</div>
      )}
    </AdminShell>
  );
}
