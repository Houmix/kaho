import Link from 'next/link';
import { CourseDetail } from '@/lib/lms';

export default function CourseSidebar({ course, currentLessonId }: { course: CourseDetail; currentLessonId?: number }) {
  return (
    <aside className="card p-0 overflow-hidden lg:sticky lg:top-20 max-h-[calc(100vh-6rem)] overflow-y-auto">
      <div className="p-4 border-b border-cream-200">
        <Link href={`/code/${course.slug}`} className="font-semibold hover:underline">{course.title}</Link>
        <div className="mt-2 flex items-center gap-2 text-xs text-brown-800/70">
          <div className="flex-1 h-1.5 bg-cream-200 rounded-full overflow-hidden"><div className="h-full bg-brown-700" style={{ width: `${course.percent}%` }} /></div>
          <span>{course.percent} %</span>
        </div>
      </div>
      <nav className="p-2 text-sm">
        {course.sections.map((s) => (
          <div key={s.id} className="mb-2">
            <div className="px-2 py-1.5 flex items-center justify-between gap-2 text-xs uppercase tracking-wide text-brown-800/60 font-medium">
              <span>{s.order}. {s.title}</span>
              {s.locked ? <span title={s.lock_reason}>🔒</span> : s.best_score !== null ? <span className="text-caramel">{s.best_score} %</span> : s.is_free_preview ? <span className="badge bg-caramel/40 text-brown-900 !py-0">gratuit</span> : null}
            </div>
            {s.lessons.map((l) => (
              <Link key={l.id} href={s.locked ? '#' : `/code/${course.slug}/${l.slug}`} aria-disabled={s.locked}
                className={`flex items-center gap-2 px-2 py-1.5 rounded-lg ${l.id === currentLessonId ? 'bg-brown-700 text-cream-50' : s.locked ? 'text-brown-800/40 cursor-not-allowed' : 'hover:bg-cream-100'}`}>
                <span className={`w-4 h-4 rounded-full border text-[10px] flex items-center justify-center shrink-0 ${l.completed ? 'bg-brown-700 border-brown-700 text-cream-50' : 'border-brown-300'} ${l.id === currentLessonId && l.completed ? 'bg-cream-50 text-brown-700' : ''}`}>{l.completed ? '✓' : ''}</span>
                <span className="truncate">{l.title}</span>
                <span className="ml-auto text-[11px] opacity-60">{l.estimated_minutes} min</span>
              </Link>
            ))}
            {s.quiz_id && (
              <Link href={s.locked ? '#' : `/code/quiz/${s.quiz_id}`} className={`flex items-center gap-2 px-2 py-1.5 rounded-lg ${s.locked ? 'text-brown-800/40 cursor-not-allowed' : 'hover:bg-cream-100 text-brown-700 font-medium'}`}>
                <span className="w-4 text-center">★</span> Quiz de fin de section
              </Link>
            )}
          </div>
        ))}
      </nav>
    </aside>
  );
}
