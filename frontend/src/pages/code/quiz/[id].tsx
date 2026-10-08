import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/router';
import api from '@/lib/api';
import { useAuth } from '@/hooks/useAuth';
import LmsShell, { UpsellBanner } from '@/components/LmsShell';
import QuestionCard from '@/components/QuestionCard';
import { Answer, QuizData, QuizResult } from '@/lib/lms';
import { apiError } from '@/lib/types';

export default function QuizPage() {
  const router = useRouter();
  const id = typeof router.query.id === 'string' ? router.query.id : null;
  const { hasHydrated, isAuthenticated } = useAuth();
  const [quiz, setQuiz] = useState<QuizData | null>(null);
  const [answers, setAnswers] = useState<Record<string, Answer>>({});
  const [result, setResult] = useState<QuizResult | null>(null);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (!hasHydrated || !id) return;
    api.get(`/lms/quizzes/${id}/`).then((r) => setQuiz(r.data)).catch((err) => setError(apiError(err, 'Quiz inaccessible.')));
  }, [hasHydrated, id]);

  const submit = async () => {
    if (!quiz) return;
    setBusy(true);
    try { setResult((await api.post(`/lms/quizzes/${quiz.id}/submit/`, { answers })).data); window.scrollTo({ top: 0, behavior: 'smooth' }); }
    catch (err) { setError(apiError(err, 'Envoi impossible.')); }
    finally { setBusy(false); }
  };
  const retry = () => { setAnswers({}); setResult(null); window.scrollTo({ top: 0 }); };

  if (error) return <LmsShell title="Quiz"><p className="text-red-700">{error}</p><Link href="/code" className="btn-secondary mt-4">Retour aux cours</Link></LmsShell>;
  if (!quiz) return <LmsShell title="Quiz"><p className="text-brown-500">Chargement…</p></LmsShell>;
  const answered = quiz.questions.filter((q) => { const a = answers[q.id]; return Array.isArray(a) ? a.length > 0 : !!a; }).length;

  return (
    <LmsShell title={quiz.title}>
      <div className="max-w-3xl mx-auto">
        <Link href={`/code/${quiz.course_slug}`} className="text-sm text-brown-700 hover:underline">← Retour au cours</Link>
        <h1 className="text-3xl mt-2 mb-1">{quiz.title}</h1>
        <p className="text-brown-800/70 mb-6">{quiz.questions.length} questions · réussite à {quiz.pass_score} %{quiz.best_score !== null ? ` · votre meilleur score : ${quiz.best_score} %` : ''}</p>

        {result && (
          <div className={`card mb-6 ${result.passed ? 'border-brown-500 bg-brown-50' : 'border-red-300 bg-red-50'}`}>
            <p className="text-4xl font-display">{result.score} %</p>
            <p className="font-semibold mt-1">{result.passed ? 'Quiz réussi 🎉' : 'Pas encore — relisez les explications et réessayez'}</p>
            <p className="text-sm text-brown-800/70">{result.correct} bonne(s) réponse(s) sur {result.total}{!result.saved && ' · connectez-vous pour enregistrer votre progression'}</p>
            {result.unlocked_section && <p className="mt-2 text-sm"><strong>Section suivante débloquée :</strong> {result.unlocked_section.title}</p>}
            <div className="flex flex-wrap gap-2 mt-4">
              <button onClick={retry} className="btn-secondary">Recommencer</button>
              {result.unlocked_section ? <Link href={`/code/${quiz.course_slug}`} className="btn-primary">Continuer le cours →</Link> : <Link href={`/code/${quiz.course_slug}`} className="btn-outline">Retour au cours</Link>}
            </div>
          </div>
        )}

        <div className="space-y-4">
          {quiz.questions.map((q, i) => (
            <QuestionCard key={q.id} index={i} q={q} value={answers[q.id]} onChange={(a) => setAnswers((prev) => ({ ...prev, [q.id]: a }))} correction={result?.items.find((it) => it.id === q.id)} disabled={!!result} />
          ))}
        </div>

        {!result && (
          <div className="sticky bottom-0 mt-6 py-3 bg-cream-50/90 backdrop-blur border-t border-cream-200 flex items-center justify-between gap-3">
            <span className="text-sm text-brown-800/70">{answered} / {quiz.questions.length} répondues</span>
            <button onClick={submit} disabled={busy || answered === 0} className="btn-primary disabled:opacity-50">{busy ? 'Correction…' : 'Valider mes réponses'}</button>
          </div>
        )}
        {!isAuthenticated && !result && <div className="mt-6"><UpsellBanner upsell={null} text="Créez un compte pour enregistrer vos scores et débloquer les sections suivantes" /></div>}
      </div>
    </LmsShell>
  );
}
