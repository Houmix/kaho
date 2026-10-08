import { useEffect, useState } from 'react';
import Head from 'next/head';
import Link from 'next/link';
import api from '@/lib/api';
import Logo from '@/components/Logo';
import QuestionCard from '@/components/QuestionCard';
import { UpsellBanner } from '@/components/LmsShell';
import { Answer, PublicQuestion, Upsell } from '@/lib/lms';

interface Demo {
  chapters: { course: { slug: string; title: string }; section: { id: number; title: string }; lessons: { id: number; title: string; slug: string; estimated_minutes: number }[]; quiz_id: number | null }[];
  demo_exam: { title: string; pass_score: number } | null;
  upsell: Upsell | null;
  bank_size: number;
}
interface DemoResult { score: number; correct: number; total: number; passed: boolean; items: any[]; upsell: Upsell | null; bank_size: number }

export default function DemoPage() {
  const [demo, setDemo] = useState<Demo | null>(null);
  const [questions, setQuestions] = useState<PublicQuestion[] | null>(null);
  const [answers, setAnswers] = useState<Record<string, Answer>>({});
  const [result, setResult] = useState<DemoResult | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => { api.get('/lms/demo/').then((r) => setDemo(r.data)); }, []);

  const startQuiz = async () => { setBusy(true); try { setQuestions((await api.post('/lms/exams/demo/')).data.questions); setAnswers({}); setResult(null); } finally { setBusy(false); } };
  const submit = async () => {
    if (!questions) return;
    setBusy(true);
    try { setResult((await api.post('/lms/exams/demo/', { answers, question_ids: questions.map((q) => q.id) })).data); window.scrollTo({ top: document.getElementById('serie')?.offsetTop ?? 0, behavior: 'smooth' }); }
    finally { setBusy(false); }
  };
  const answered = questions ? questions.filter((q) => { const a = answers[q.id]; return Array.isArray(a) ? a.length > 0 : !!a; }).length : 0;

  return (
    <>
      <Head><title>Essai gratuit du code en ligne — Kaho</title></Head>
      <header className="bg-white border-b border-cream-200"><div className="container flex items-center justify-between py-3"><Logo /><div className="flex gap-2"><Link href="/login" className="text-brown-700 font-medium px-3 py-2 text-sm">Connexion</Link><Link href="/signup" className="btn-primary !py-2 text-sm">S'inscrire</Link></div></div></header>
      <main className="container max-w-3xl py-8">
        <p className="text-caramel font-medium tracking-wide uppercase text-sm mb-2">Essai gratuit, sans compte</p>
        <h1 className="text-4xl mb-3">Testez le code en ligne</h1>
        <p className="text-brown-800/70 mb-8">Un chapitre complet en accès libre et une série de 10 questions corrigées, pour vous faire une idée avant de choisir une formule.</p>

        {!demo ? <p className="text-brown-500">Chargement…</p> : (
          <>
            <h2 className="text-2xl mb-3">1. Un chapitre complet offert</h2>
            {demo.chapters.length === 0 ? <p className="text-brown-800/60 mb-8">Aucun chapitre en accès libre pour le moment.</p> : demo.chapters.map((ch) => (
              <section key={ch.section.id} className="card mb-8">
                <p className="text-xs uppercase tracking-wide text-caramel font-medium">{ch.course.title}</p>
                <h3 className="text-xl mt-1 mb-3">{ch.section.title}</h3>
                <ul className="divide-y divide-cream-200 text-sm">
                  {ch.lessons.map((l) => <li key={l.id} className="py-2 flex items-center justify-between"><Link href={`/code/${ch.course.slug}/${l.slug}`} className="text-brown-700 font-medium hover:underline">{l.title}</Link><span className="text-xs text-brown-800/60">{l.estimated_minutes} min</span></li>)}
                  {ch.quiz_id && <li className="py-2"><Link href={`/code/quiz/${ch.quiz_id}`} className="text-brown-700 font-medium hover:underline">★ Quiz de fin de section (correction instantanée)</Link></li>}
                </ul>
              </section>
            ))}

            <h2 id="serie" className="text-2xl mb-3">2. Série d'essai : 10 questions</h2>
            {!questions ? (
              <div className="card mb-8">
                <p className="text-brown-800/70">{demo.demo_exam?.title ?? "Série d'essai"} — 10 questions tirées au hasard, correction immédiate avec explications.</p>
                <button onClick={startQuiz} disabled={busy} className="btn-primary mt-4">{busy ? 'Préparation…' : 'Commencer la série'}</button>
              </div>
            ) : (
              <>
                {result && (
                  <div className={`card mb-6 ${result.passed ? 'border-brown-500 bg-brown-50' : 'border-caramel bg-brown-50'}`}>
                    <p className="text-4xl font-display">{result.score} %</p>
                    <p className="font-semibold mt-1">{result.correct} bonne(s) réponse(s) sur {result.total}</p>
                    <p className="text-sm text-brown-800/70 mt-1">{result.passed ? 'Bravo ! Prêt(e) pour la suite ?' : 'Les explications ci-dessous vous aideront à progresser.'}</p>
                  </div>
                )}
                <div className="space-y-4 mb-6">{questions.map((q, i) => <QuestionCard key={q.id} index={i} q={q} value={answers[q.id]} onChange={(a) => setAnswers((prev) => ({ ...prev, [q.id]: a }))} correction={result?.items.find((it: any) => it.id === q.id)} disabled={!!result} />)}</div>
                {!result ? (
                  <div className="sticky bottom-0 py-3 bg-cream-50/90 backdrop-blur border-t border-cream-200 flex items-center justify-between gap-3 mb-8"><span className="text-sm text-brown-800/70">{answered} / {questions.length}</span><button onClick={submit} disabled={busy || answered === 0} className="btn-primary disabled:opacity-50">Voir ma correction</button></div>
                ) : (
                  <div className="mb-8"><UpsellBanner upsell={result.upsell} text={`Débloquez les ${result.bank_size} questions, tous les cours et les examens blancs chronométrés`} /><button onClick={startQuiz} className="text-sm text-brown-700 hover:underline mt-3">Refaire une série</button></div>
                )}
              </>
            )}

            {!result && <UpsellBanner upsell={demo.upsell} text={`Le programme complet : tous les chapitres, ${demo.bank_size} questions et les examens blancs en conditions réelles`} />}
          </>
        )}
      </main>
    </>
  );
}
