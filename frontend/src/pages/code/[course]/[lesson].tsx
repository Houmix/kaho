import { useCallback, useEffect, useRef, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/router';
import api from '@/lib/api';
import { useAuth } from '@/hooks/useAuth';
import { useWakeLock } from '@/hooks/useWakeLock';
import LmsShell, { UpsellBanner } from '@/components/LmsShell';
import CourseSidebar from '@/components/CourseSidebar';
import Markdown from '@/components/Markdown';
import { CourseDetail, LessonDetail, Upsell } from '@/lib/lms';

export default function LessonPage() {
  const router = useRouter();
  const slug = typeof router.query.course === 'string' ? router.query.course : null;
  const lessonSlug = typeof router.query.lesson === 'string' ? router.query.lesson : null;
  const { hasHydrated, isAuthenticated, user } = useAuth();
  const [course, setCourse] = useState<CourseDetail | null>(null);
  const [lesson, setLesson] = useState<LessonDetail | null>(null);
  const [locked, setLocked] = useState<{ reason: string; upsell: Upsell | null } | null>(null);
  const [playing, setPlaying] = useState(false);
  const [busy, setBusy] = useState(false);
  const videoRef = useRef<HTMLVideoElement>(null);
  const { supported: wakeSupported, held } = useWakeLock(playing);

  const load = useCallback(async () => {
    if (!slug || !lessonSlug) return;
    const c = (await api.get(`/lms/courses/${slug}/`)).data as CourseDetail;
    setCourse(c);
    const item = c.sections.flatMap((s) => s.lessons).find((l) => l.slug === lessonSlug);
    if (!item) { setLocked({ reason: 'Leçon introuvable.', upsell: c.upsell }); return; }
    try {
      setLesson((await api.get(`/lms/lessons/${item.id}/`)).data);
      setLocked(null);
    } catch (err: any) {
      setLocked({ reason: err.response?.data?.detail || 'Accès refusé.', upsell: err.response?.data?.upsell ?? c.upsell });
    }
  }, [slug, lessonSlug]);

  useEffect(() => { if (hasHydrated) { setPlaying(false); load(); } }, [hasHydrated, load]);

  const complete = async () => {
    if (!lesson) return;
    setBusy(true);
    try { await api.post(`/lms/lessons/${lesson.id}/complete/`); await load(); } finally { setBusy(false); }
  };

  const canTrack = isAuthenticated && user?.role === 'STUDENT';
  const title = lesson?.title ?? 'Leçon';
  const section = lesson ? course?.sections.find((s) => s.id === lesson.section_id) : undefined;
  const lastInSection = !!section && section.lessons[section.lessons.length - 1]?.id === lesson?.id;
  const sectionQuiz = lastInSection && section?.quiz_id ? section.quiz_id : null;

  return (
    <LmsShell title={title}>
      <div className="grid lg:grid-cols-[300px_1fr] gap-6">
        {course && <CourseSidebar course={course} currentLessonId={lesson?.id} />}
        <article className="min-w-0">
          {locked ? (
            <div className="space-y-4">
              <p className="text-caramel font-medium text-sm uppercase tracking-wide">Contenu verrouillé</p>
              <h1 className="text-2xl">{locked.reason}</h1>
              {locked.reason.includes('quiz') ? <Link href={`/code/${slug}`} className="btn-secondary">Retour au cours</Link> : <UpsellBanner upsell={locked.upsell} />}
            </div>
          ) : !lesson ? <p className="text-brown-500">Chargement…</p> : (
            <>
              <p className="text-xs uppercase tracking-wide text-caramel font-medium"><Link href={`/code/${lesson.course_slug}`} className="hover:underline">{lesson.course_title}</Link> · {lesson.section_title}</p>
              <h1 className="text-3xl mt-1 mb-4">{lesson.title}</h1>

              {lesson.video_url && (
                <div className="mb-6">
                  <div className="aspect-video rounded-2xl overflow-hidden bg-brown-900 shadow-warm">
                    {lesson.is_mp4 ? (
                      <video ref={videoRef} src={lesson.video_url} controls playsInline className="w-full h-full" onPlay={() => setPlaying(true)} onPause={() => setPlaying(false)} onEnded={() => setPlaying(false)} />
                    ) : (
                      <iframe src={lesson.embed_url} title={lesson.title} className="w-full h-full" allow="accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture" allowFullScreen onLoad={() => setPlaying(true)} />
                    )}
                  </div>
                  <p className="text-xs text-brown-800/50 mt-1">{wakeSupported ? (held ? 'Veille de l’écran désactivée pendant la vidéo.' : 'Veille de l’écran désactivée dès la lecture.') : 'Votre navigateur ne permet pas de bloquer la veille : pensez à toucher l’écran.'}</p>
                </div>
              )}

              {lesson.content_md && <Markdown>{lesson.content_md}</Markdown>}

              <div className="mt-8 flex flex-wrap items-center gap-3 border-t border-cream-200 pt-6">
                {canTrack && (lesson.completed ? <span className="badge bg-brown-700 text-cream-50">Leçon terminée ✓</span> : <button onClick={complete} disabled={busy} className="btn-primary">{busy ? '…' : 'Marquer comme terminée'}</button>)}
                {lesson.quiz_id && <Link href={`/code/quiz/${lesson.quiz_id}`} className="btn-outline">Quiz de la leçon</Link>}
                <div className="sm:ml-auto flex flex-wrap gap-2 w-full sm:w-auto">
                  {lesson.prev && <Link href={`/code/${lesson.course_slug}/${lesson.prev.slug}`} className="btn-secondary flex-1 sm:flex-none">← {lesson.prev.title}</Link>}
                  {sectionQuiz ? <Link href={`/code/quiz/${sectionQuiz}`} className="btn-primary flex-1 sm:flex-none">Passer le quiz →</Link>
                    : lesson.next ? <Link href={`/code/${lesson.course_slug}/${lesson.next.slug}`} className="btn-secondary flex-1 sm:flex-none">{lesson.next.title} →</Link> : null}
                </div>
              </div>
              {sectionQuiz && (
                <p className="text-sm text-brown-800/60 mt-2">Dernière leçon de la section : validez le quiz{section?.unlock_threshold ? ` (≥ ${section.unlock_threshold} %)` : ''} pour débloquer la suivante.</p>
              )}
            </>
          )}
        </article>
      </div>
    </LmsShell>
  );
}
