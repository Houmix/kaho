import { useCallback, useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/router';
import api from '@/lib/api';
import { useRequireAuth } from '@/hooks/useRequireAuth';
import LmsShell from '@/components/LmsShell';
import QuestionCard from '@/components/QuestionCard';
import { Answer, CorrectionItem, PublicQuestion } from '@/lib/lms';

interface Rev { count: number; questions: PublicQuestion[]; topics: { code: string; label: string; n: number }[] }

export default function RevisionPage() {
  const ready = useRequireAuth('STUDENT');
  const router = useRouter();
  const [topic, setTopic] = useState('');
  const [data, setData] = useState<Rev | null>(null);
  const [answers, setAnswers] = useState<Record<string, Answer>>({});
  const [result, setResult] = useState<{ score: number; correct: number; total: number; items: CorrectionItem[] } | null>(null);
  const [busy, setBusy] = useState(false);
  useEffect(() => { if (router.isReady && typeof router.query.topic === 'string') setTopic(router.query.topic); }, [router.isReady, router.query]);
  const load = useCallback(() => api.get('/lms/revision/', { params: { topic: topic || undefined } }).then((r) => { setData(r.data); setAnswers({}); setResult(null); }), [topic]);
  useEffect(() => { if (ready) load(); }, [ready, load]);
  const submit = async () => {
    setBusy(true);
    try { setResult((await api.post('/lms/revision/', { answers })).data); window.scrollTo({ top: 0, behavior: 'smooth' }); } finally { setBusy(false); }
  };
  const answered = data ? data.questions.filter((q) => { const a = answers[q.id]; return Array.isArray(a) ? a.length > 0 : !!a; }).length : 0;

  return (
    <LmsShell title="Révision ciblée">
      <div className="max-w-3xl mx-auto">
        <Link href="/code" className="text-sm text-brown-700 hover:underline">← Cours et examens</Link>
        <h1 className="text-3xl mt-2 mb-1">Révision ciblée</h1>
        <p className="text-brown-800/70 mb-4">Les questions que vous avez manquées en quiz ou en examen blanc, à refaire jusqu'à les maîtriser. Correction immédiate.</p>
        {data && data.topics.length > 0 && (
          <div className="flex flex-wrap gap-1 mb-4">
            <button onClick={() => setTopic('')} className={`badge !px-3 !py-1.5 ${topic === '' ? 'bg-brown-700 text-cream-50' : 'bg-cream-100 text-brown-800'}`}>Tous ({data.topics.reduce((a, t) => a + t.n, 0)})</button>
            {data.topics.map((t) => <button key={t.code} onClick={() => setTopic(t.code)} className={`badge !px-3 !py-1.5 ${topic === t.code ? 'bg-brown-700 text-cream-50' : 'bg-cream-100 text-brown-800'}`}>{t.label} ({t.n})</button>)}
          </div>
        )}
        {!data ? <p className="text-brown-500">Chargement…</p> : data.questions.length === 0 ? (
          <div className="card"><p className="font-semibold">Rien à réviser pour le moment 🎉</p><p className="text-sm text-brown-800/70 mt-1">Passez un quiz de thème ou un examen blanc : vos erreurs apparaîtront ici.</p><Link href="/code" className="btn-primary mt-4 inline-block">Retour aux cours</Link></div>
        ) : (
          <>
            {result && (
              <div className={`card mb-6 ${result.score >= 88 ? 'border-brown-500 bg-brown-50' : 'border-caramel bg-brown-50'}`}>
                <p className="text-4xl font-display">{result.score} %</p>
                <p className="font-semibold mt-1">{result.correct} bonne(s) réponse(s) sur {result.total}</p>
                <div className="flex gap-2 mt-4"><button onClick={load} className="btn-primary">Nouvelle série</button><Link href="/code" className="btn-secondary">Mes statistiques</Link></div>
              </div>
            )}
            <div className="space-y-4">{data.questions.map((q, i) => <QuestionCard key={q.id} index={i} q={q} value={answers[q.id]} onChange={(a) => setAnswers((p) => ({ ...p, [q.id]: a }))} correction={result?.items.find((it) => it.id === q.id)} disabled={!!result} />)}</div>
            {!result && <div className="sticky bottom-0 mt-6 py-3 bg-cream-50/90 backdrop-blur border-t border-cream-200 flex items-center justify-between gap-3"><span className="text-sm text-brown-800/70">{answered} / {data.questions.length} répondues</span><button onClick={submit} disabled={busy || answered === 0} className="btn-primary disabled:opacity-50">{busy ? 'Correction…' : 'Corriger'}</button></div>}
          </>
        )}
      </div>
    </LmsShell>
  );
}
