import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/router';
import api from '@/lib/api';
import { useAuth } from '@/hooks/useAuth';
import LmsShell, { UpsellBanner } from '@/components/LmsShell';
import CourseSidebar from '@/components/CourseSidebar';
import { CourseDetail } from '@/lib/lms';

export default function CoursePage() {
  const router = useRouter();
  const slug = typeof router.query.course === 'string' ? router.query.course : null;
  const { hasHydrated } = useAuth();
  const [course, setCourse] = useState<CourseDetail | null>(null);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!hasHydrated || !slug) return;
    api.get(`/lms/courses/${slug}/`).then((r) => setCourse(r.data)).catch(() => setError('Cours introuvable.'));
  }, [hasHydrated, slug]);

  if (error) return <LmsShell title="Cours"><p className="text-red-700">{error}</p></LmsShell>;
  if (!course) return <LmsShell title="Cours"><p className="text-brown-500">Chargement…</p></LmsShell>;

  const firstOpen = course.sections.find((s) => !s.locked && s.lessons.length);
  const nextLesson = course.sections.flatMap((s) => (s.locked ? [] : s.lessons)).find((l) => !l.completed) ?? firstOpen?.lessons[0];

  return (
    <LmsShell title={course.title}>
      <div className="grid lg:grid-cols-[300px_1fr] gap-6">
        <CourseSidebar course={course} />
        <div>
          <Link href="/code" className="text-sm text-brown-700 hover:underline">← Tous les cours</Link>
          <h1 className="text-3xl mt-2 mb-2">{course.title}</h1>
          <p className="text-brown-800/70 mb-6">{course.description}</p>
          {!course.has_access && <div className="mb-6"><UpsellBanner upsell={course.upsell} /></div>}
          <div className="card mb-6 flex flex-wrap items-center justify-between gap-3">
            <div><p className="font-semibold">{course.completed_count} / {course.lesson_count} leçons terminées</p><p className="text-sm text-brown-800/70">{course.percent} % du cours</p></div>
            {nextLesson && <Link href={`/code/${course.slug}/${nextLesson.slug}`} className="btn-primary">{course.completed_count ? 'Continuer' : 'Commencer'} : {nextLesson.title}</Link>}
          </div>
          <div className="space-y-4">
            {course.sections.map((s) => (
              <section key={s.id} className={`card ${s.locked ? 'opacity-75' : ''}`}>
                <div className="flex items-start justify-between gap-3">
                  <h2 className="text-xl">{s.order}. {s.title}</h2>
                  {s.locked ? <span className="badge bg-cream-200 text-brown-800">🔒 verrouillé</span> : s.best_score !== null ? <span className="badge bg-brown-700 text-cream-50">quiz : {s.best_score} %</span> : s.is_free_preview ? <span className="badge bg-caramel/40 text-brown-900">gratuit</span> : null}
                </div>
                {s.locked && <p className="text-sm text-brown-800/70 mt-1">{s.lock_reason}</p>}
                <ul className="mt-3 divide-y divide-cream-200 text-sm">
                  {s.lessons.map((l) => (
                    <li key={l.id} className="py-2 flex items-center gap-3">
                      <span className={`w-5 h-5 rounded-full border text-[11px] flex items-center justify-center ${l.completed ? 'bg-brown-700 border-brown-700 text-cream-50' : 'border-brown-300'}`}>{l.completed ? '✓' : ''}</span>
                      {s.locked ? <span className="text-brown-800/60">{l.title}</span> : <Link href={`/code/${course.slug}/${l.slug}`} className="hover:underline">{l.title}</Link>}
                      <span className="ml-auto text-xs text-brown-800/60">{l.estimated_minutes} min</span>
                    </li>
                  ))}
                  {s.quiz_id && <li className="py-2">{s.locked ? <span className="text-brown-800/60">★ Quiz de fin de section</span> : <Link href={`/code/quiz/${s.quiz_id}`} className="text-brown-700 font-medium hover:underline">★ Quiz de fin de section{s.unlock_threshold ? ` (≥ ${s.unlock_threshold} % pour débloquer la suite)` : ''}</Link>}</li>}
                </ul>
              </section>
            ))}
          </div>
        </div>
      </div>
    </LmsShell>
  );
}
