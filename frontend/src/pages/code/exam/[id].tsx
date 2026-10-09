import { useCallback, useEffect, useRef, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/router';
import api from '@/lib/api';
import { useRequireAuth } from '@/hooks/useRequireAuth';
import LmsShell from '@/components/LmsShell';
import QuestionCard from '@/components/QuestionCard';
import { Answer, ExamItem, ExamPayload, ExamReport, fmtSeconds } from '@/lib/lms';
import { apiError } from '@/lib/types';

export default function ExamPage() {
  const ready = useRequireAuth('STUDENT');
  const router = useRouter();
  const examId = typeof router.query.id === 'string' ? router.query.id : null;
  const attemptParam = typeof router.query.attempt === 'string' ? router.query.attempt : null;
  const [exam, setExam] = useState<ExamItem | null>(null);
  const [payload, setPayload] = useState<ExamPayload | null>(null);
  const [report, setReport] = useState<ExamReport | null>(null);
  const [answers, setAnswers] = useState<Record<string, Answer>>({});
  const [left, setLeft] = useState(0);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const [current, setCurrent] = useState(0);
  const [qLeft, setQLeft] = useState(0);
  const dirty = useRef<Record<string, Answer>>({});
  const perQuestion = payload?.attempt.seconds_per_question ?? 0;

  useEffect(() => {
    if (!ready || !examId) return;
    api.get('/lms/exams/').then((r) => setExam(r.data.exams.find((e: ExamItem) => String(e.id) === examId) ?? null));
    if (attemptParam) {
      api.get(`/lms/exam-attempts/${attemptParam}/`).then((r) => {
        if (r.data.items) setReport(r.data); else { setPayload(r.data); setAnswers(r.data.answers || {}); setLeft(r.data.attempt.seconds_left); }
      }).catch((err) => setError(apiError(err, 'Tentative introuvable.')));
    }
  }, [ready, examId, attemptParam]);

  const start = async () => {
    setBusy(true); setError('');
    try {
      const r = await api.post(`/lms/exams/${examId}/start/`);
      setPayload(r.data); setAnswers(r.data.answers || {}); setLeft(r.data.attempt.seconds_left); setCurrent(0);
      router.replace(`/code/exam/${examId}?attempt=${r.data.attempt.id}`, undefined, { shallow: true });
    } catch (err) { setError(apiError(err, 'Impossible de démarrer.')); }
    finally { setBusy(false); }
  };

  const submit = useCallback(async (auto = false) => {
    if (!payload) return;
    setBusy(true);
    try {
      const r = await api.post(`/lms/exam-attempts/${payload.attempt.id}/submit/`, { answers });
      setReport(r.data); setPayload(null);
      window.scrollTo({ top: 0 });
    } catch (err: any) {
      if (auto) { const r = await api.get(`/lms/exam-attempts/${payload.attempt.id}/`); if (r.data.items) { setReport(r.data); setPayload(null); } }
      else setError(apiError(err, 'Remise impossible.'));
    } finally { setBusy(false); }
  }, [payload, answers]);

  // Chronomètre + remise automatique
  useEffect(() => {
    if (!payload) return;
    const t = setInterval(() => setLeft((s) => { if (s <= 1) { clearInterval(t); submit(true); return 0; } return s - 1; }), 1000);
    return () => clearInterval(t);
  }, [payload, submit]);

  // Mode officiel : chrono strict par question, passage automatique à la suivante, remise à la fin
  useEffect(() => {
    if (!payload || !perQuestion) return;
    setQLeft(perQuestion);
    const t = setInterval(() => setQLeft((s) => {
      if (s <= 1) {
        clearInterval(t);
        if (current < payload.questions.length - 1) setCurrent((c) => c + 1); else submit(true);
        return 0;
      }
      return s - 1;
    }), 1000);
    return () => clearInterval(t);
  }, [payload, perQuestion, current, submit]);

  // Sauvegarde progressive toutes les 5 s
  useEffect(() => {
    if (!payload) return;
    const t = setInterval(async () => {
      const pending = dirty.current; dirty.current = {};
      if (Object.keys(pending).length === 0) return;
      try { await api.patch(`/lms/exam-attempts/${payload.attempt.id}/answers/`, { answers: pending }); }
      catch (err: any) { if (err.response?.status === 409) submit(true); }
    }, 5000);
    return () => clearInterval(t);
  }, [payload, submit]);

  const setAnswer = (qid: number, a: Answer) => { setAnswers((prev) => ({ ...prev, [qid]: a })); dirty.current[qid] = a; };
  const answeredCount = payload ? payload.questions.filter((q) => { const a = answers[q.id]; return Array.isArray(a) ? a.length > 0 : !!a; }).length : 0;

  if (error) return <LmsShell title="Examen blanc"><p className="text-red-700">{error}</p><Link href="/code" className="btn-secondary mt-4">Retour</Link></LmsShell>;

  // Rapport de correction (différée)
  if (report) {
    const a = report.attempt;
    return (
      <LmsShell title={a.exam_title}>
        <div className="max-w-3xl mx-auto">
          <Link href="/code" className="text-sm text-brown-700 hover:underline">← Cours et examens</Link>
          <div className={`card mt-2 mb-6 ${a.passed ? 'border-brown-500 bg-brown-50' : 'border-red-300 bg-red-50'}`}>
            <p className="text-xs uppercase tracking-wide text-caramel font-medium">{a.exam_title}{a.status === 'EXPIRED' ? ' · temps écoulé' : ''}</p>
            <p className="text-5xl font-display mt-1">{a.score} %</p>
            <p className="font-semibold mt-1">{a.passed ? 'Examen réussi 🎉' : `Non validé — il faut ${a.pass_score} %`}</p>
            <p className="text-sm text-brown-800/70">{a.correct_count} bonnes réponses sur {a.total}</p>
            <div className="flex flex-wrap gap-2 mt-4"><button onClick={() => { setReport(null); router.replace(`/code/exam/${examId}`, undefined, { shallow: true }); }} className="btn-primary">Refaire un examen</button><Link href="/code" className="btn-secondary">Mes statistiques</Link></div>
          </div>
          <h2 className="text-xl mb-3">Correction détaillée</h2>
          <div className="space-y-4">{report.items.map((it, i) => <QuestionCard key={it.id} index={i} q={it} value={it.given ?? undefined} onChange={() => {}} correction={it} disabled />)}</div>
        </div>
      </LmsShell>
    );
  }

  // Écran de démarrage
  if (!payload) {
    return (
      <LmsShell title={exam?.title ?? 'Examen blanc'}>
        <div className="max-w-xl mx-auto">
          <Link href="/code" className="text-sm text-brown-700 hover:underline">← Cours et examens</Link>
          {!exam ? <p className="text-brown-500 mt-4">Chargement…</p> : (
            <div className="card mt-2">
              <h1 className="text-3xl">{exam.title}</h1>
              <p className="text-brown-800/70 mt-2">{exam.description}</p>
              <ul className="mt-4 text-sm space-y-1 text-brown-800/80">
                <li>• {Math.min(exam.question_count, exam.available_questions)} questions tirées au hasard dans la banque</li>
                {exam.seconds_per_question ? <li>• <strong>{exam.seconds_per_question} secondes</strong> par question, sans retour en arrière — comme à l'examen officiel</li> : <li>• {exam.duration_minutes} minutes — remise automatique à la fin du temps</li>}
                <li>• Correction et explications <strong>après</strong> la remise, comme à l'examen</li>
                <li>• Réussite à partir de {exam.pass_score} %</li>
                {exam.attempts > 0 && <li>• {exam.attempts} tentative(s), meilleur score {exam.best_score} %</li>}
              </ul>
              <button onClick={start} disabled={busy} className="btn-primary mt-6 w-full">{busy ? 'Préparation…' : 'Démarrer l’examen'}</button>
            </div>
          )}
        </div>
      </LmsShell>
    );
  }

  // Examen en cours
  const q = payload.questions[current];
  const urgent = left < 120;
  return (
    <LmsShell title={payload.attempt.exam_title}>
      <div className="max-w-3xl mx-auto">
        <div className={`sticky top-0 z-10 -mx-4 px-4 py-2 mb-4 flex items-center justify-between gap-3 border-b ${urgent ? 'bg-red-50 border-red-200' : 'bg-cream-50/95 backdrop-blur border-cream-200'}`}>
          <span className="text-sm text-brown-800/70">{payload.attempt.exam_title} · {answeredCount}/{payload.questions.length} répondues</span>
          {perQuestion
            ? <span className={`font-mono text-2xl font-semibold ${qLeft <= 5 ? 'text-red-700' : ''}`} aria-live="polite">⏱ {qLeft} s</span>
            : <span className={`font-mono text-lg font-semibold ${urgent ? 'text-red-700' : ''}`} aria-live="polite">⏱ {fmtSeconds(left)}</span>}
        </div>
        {perQuestion ? (
          <div className="mb-4">
            <div className="h-1.5 bg-cream-200 rounded-full overflow-hidden"><div className={`h-full transition-all ${qLeft <= 5 ? 'bg-red-500' : 'bg-brown-700'}`} style={{ width: `${(qLeft / perQuestion) * 100}%` }} /></div>
            <p className="text-xs text-brown-800/60 mt-1">Question {current + 1} / {payload.questions.length}</p>
          </div>
        ) : (
          <div className="flex flex-wrap gap-1 mb-4">
            {payload.questions.map((qq, i) => { const a = answers[qq.id]; const done = Array.isArray(a) ? a.length > 0 : !!a; return <button key={qq.id} onClick={() => setCurrent(i)} className={`w-8 h-8 rounded-lg text-xs font-medium border ${i === current ? 'bg-brown-700 text-cream-50 border-brown-700' : done ? 'bg-brown-100 border-brown-300' : 'bg-white border-cream-300'}`}>{i + 1}</button>; })}
          </div>
        )}
        <QuestionCard index={current} q={q} value={answers[q.id]} onChange={(a) => setAnswer(q.id, a)} />
        <div className="mt-4 flex items-center justify-between gap-3">
          {perQuestion ? <span /> : <button onClick={() => setCurrent((c) => Math.max(0, c - 1))} disabled={current === 0} className="btn-secondary disabled:opacity-40">← Précédente</button>}
          {current < payload.questions.length - 1
            ? <button onClick={() => setCurrent((c) => c + 1)} className="btn-primary">{perQuestion ? 'Valider et passer à la suivante →' : 'Suivante →'}</button>
            : <button onClick={() => (perQuestion || answeredCount >= payload.questions.length ? true : confirm(`${payload.questions.length - answeredCount} question(s) sans réponse. Remettre quand même ?`)) && submit()} disabled={busy} className="btn-primary">{busy ? 'Remise…' : 'Remettre ma copie'}</button>}
        </div>
        <p className="text-xs text-brown-800/50 mt-3">{perQuestion ? 'Chaque question est chronométrée : sans réponse dans le temps imparti, elle est comptée fausse et la suivante s’affiche.' : 'Vos réponses sont sauvegardées automatiquement. Vous pouvez naviguer librement entre les questions avant de remettre.'}</p>
      </div>
    </LmsShell>
  );
}
