import { useEffect, useState } from 'react';
import Link from 'next/link';
import api from '@/lib/api';
import { useAuth } from '@/hooks/useAuth';
import LmsShell, { UpsellBanner } from '@/components/LmsShell';
import { CourseItem, ExamAttempt, ExamItem, ExamStats, Upsell } from '@/lib/lms';
import { ReadinessGauge, ScoreChart, StatTiles, TopicBars } from '@/components/LmsAnalytics';
import { frDate } from '@/lib/types';

export default function LmsHome() {
  const { hasHydrated, isAuthenticated, user } = useAuth();
  const [courses, setCourses] = useState<{ courses: CourseItem[]; has_access: boolean; upsell: Upsell | null } | null>(null);
  const [exams, setExams] = useState<{ exams: ExamItem[]; history: ExamAttempt[] } | null>(null);
  const [stats, setStats] = useState<ExamStats | null>(null);

  useEffect(() => {
    if (!hasHydrated) return;
    api.get('/lms/courses/').then((r) => setCourses(r.data));
    api.get('/lms/exams/').then((r) => setExams(r.data));
    if (isAuthenticated && user?.role === 'STUDENT') api.get('/lms/exam-attempts/stats/').then((r) => setStats(r.data)).catch(() => {});
  }, [hasHydrated, isAuthenticated, user]);

  if (!courses) return <LmsShell title="Code en ligne"><p className="text-brown-500">Chargement…</p></LmsShell>;

  return (
    <LmsShell title="Code en ligne">
      <h1 className="text-3xl mb-2">Cours de code en ligne</h1>
      <p className="text-brown-800/70 mb-6">Leçons, quiz de fin de section et examens blancs en conditions réelles.</p>
      {!courses.has_access && <div className="mb-6"><UpsellBanner upsell={courses.upsell} text={isAuthenticated ? 'Votre formule n’inclut pas le code en ligne' : 'Essayez gratuitement le premier chapitre, puis débloquez tout le programme'} /></div>}

      <h2 className="text-xl mb-3">Cours</h2>
      <div className="grid md:grid-cols-2 gap-4 mb-10">
        {courses.courses.length === 0 && <p className="text-brown-800/60">Aucun cours publié.</p>}
        {courses.courses.map((c) => (
          <Link key={c.id} href={`/code/${c.slug}`} className="card hover:border-brown-300 transition-colors">
            {c.cover_url && <img src={c.cover_url} alt="" className="rounded-xl mb-3 w-full h-36 object-cover" />}
            <h3 className="text-xl">{c.title}</h3>
            <p className="text-sm text-brown-800/70 mt-1 line-clamp-2">{c.description}</p>
            <div className="mt-3 flex items-center gap-2 text-xs text-brown-800/70">
              <div className="flex-1 h-1.5 bg-cream-200 rounded-full overflow-hidden"><div className="h-full bg-brown-700" style={{ width: `${c.percent}%` }} /></div>
              <span>{c.completed_count}/{c.lesson_count} leçons</span>
            </div>
            {c.has_free_preview && !courses.has_access && <span className="badge bg-caramel/40 text-brown-900 mt-3">Premier chapitre gratuit</span>}
          </Link>
        ))}
      </div>

      <h2 className="text-xl mb-3">Examens blancs</h2>
      <div className="grid md:grid-cols-2 gap-4 mb-10">
        {exams?.exams.map((e) => (
          <div key={e.id} className="card">
            <div className="flex items-start justify-between gap-2"><h3 className="text-xl">{e.title}</h3>{e.is_demo && <span className="badge bg-caramel/40 text-brown-900">essai gratuit</span>}</div>
            <p className="text-sm text-brown-800/70 mt-1">{e.description}</p>
            <p className="text-xs text-brown-800/60 mt-2">{Math.min(e.question_count, e.available_questions)} questions · {e.seconds_per_question ? `${e.seconds_per_question} s par question` : `${e.duration_minutes} min`} · réussite à {e.pass_score} %{e.attempts ? ` · ${e.attempts} tentative(s), meilleur score ${e.best_score} %` : ''}</p>
            <Link href={e.is_demo && !isAuthenticated ? '/demo' : `/code/exam/${e.id}`} className="btn-primary mt-4 !py-2 text-sm">{e.attempts ? 'Refaire un examen' : 'Commencer'}</Link>
          </div>
        ))}
        {exams && exams.exams.length === 0 && <p className="text-brown-800/60">Aucun examen disponible.</p>}
      </div>

      {stats && (
        <section className="card mb-10">
          <div className="flex flex-wrap items-center justify-between gap-2 mb-4"><h2 className="text-xl">Votre préparation</h2>{stats.etg_validated_at && <span className="badge bg-brown-700 text-cream-50">Inscription à l'examen du code validée par votre école ✓</span>}</div>
          <div className="grid lg:grid-cols-[220px_1fr] gap-6 items-start">
            <ReadinessGauge value={stats.readiness} count={stats.readiness_count} />
            <StatTiles s={stats} />
          </div>
          <div className="grid md:grid-cols-2 gap-6 mt-6">
            <div><p className="text-sm font-medium mb-2">Évolution des scores (ligne pointillée : seuil de réussite)</p><ScoreChart points={stats.evolution} /></div>
            <div><p className="text-sm font-medium mb-2">Thème par thème</p><TopicBars topics={stats.by_topic} /></div>
          </div>
          <div className="mt-6 flex flex-wrap items-center justify-between gap-3 border-t border-cream-200 pt-4">
            <p className="text-sm text-brown-800/70">Révision ciblée : refaites en priorité les questions que vous avez manquées.</p>
            <Link href="/code/revision" className="btn-primary !py-2 text-sm">Réviser mes erreurs</Link>
          </div>
        </section>
      )}

      {exams && exams.history.length > 0 && (
        <section>
          <h2 className="text-xl mb-3">Historique</h2>
          <div className="card p-0 overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-cream-100 text-brown-800/70"><tr><th className="text-left py-2 px-4">Date</th><th className="text-left py-2 px-4">Examen</th><th className="text-right py-2 px-4">Score</th><th className="text-left py-2 px-4 pl-6">Résultat</th><th></th></tr></thead>
              <tbody>{exams.history.map((a) => (
                <tr key={a.id} className="border-t border-cream-200">
                  <td className="py-2 px-4">{frDate(a.started_at, { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' })}</td>
                  <td className="py-2 px-4">{a.exam_title}</td>
                  <td className="py-2 px-4 text-right">{a.score !== null ? `${a.correct_count}/${a.total} · ${a.score} %` : '—'}</td>
                  <td className="py-2 px-4 pl-6">{a.status === 'IN_PROGRESS' ? <span className="badge bg-caramel text-brown-900">en cours</span> : a.passed ? <span className="badge bg-brown-700 text-cream-50">réussi</span> : <span className="badge bg-red-100 text-red-700">échoué{a.status === 'EXPIRED' ? ' (temps écoulé)' : ''}</span>}</td>
                  <td className="py-2 px-4 text-right"><Link href={`/code/exam/${a.exam}?attempt=${a.id}`} className="text-brown-700 text-xs hover:underline">{a.status === 'IN_PROGRESS' ? 'Reprendre' : 'Voir la correction'}</Link></td>
                </tr>
              ))}</tbody>
            </table>
          </div>
        </section>
      )}
    </LmsShell>
  );
}
