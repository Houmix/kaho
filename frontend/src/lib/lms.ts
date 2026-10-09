export interface Upsell { id: number; name: string; price: string }

export interface LessonItem { id: number; title: string; slug: string; order: number; estimated_minutes: number; completed: boolean; has_quiz: boolean }
export interface SectionItem {
  id: number; title: string; order: number; is_free_preview: boolean; unlock_threshold: number;
  lessons: LessonItem[]; quiz_id: number | null; locked: boolean; lock_reason: string; best_score: number | null;
}
export interface CourseItem {
  id: number; title: string; slug: string; description: string; cover_url: string;
  lesson_count: number; completed_count: number; percent: number; has_free_preview: boolean;
}
export interface CourseDetail extends CourseItem { sections: SectionItem[]; has_access: boolean; upsell: Upsell | null }
export interface LessonDetail {
  id: number; title: string; slug: string; section_id: number; section_title: string; course_slug: string; course_title: string;
  video_url: string; embed_url: string; is_mp4: boolean; content_md: string; estimated_minutes: number; quiz_id: number | null; completed: boolean;
  prev: { id: number; title: string; slug: string } | null; next: { id: number; title: string; slug: string } | null;
}

export type QuestionKind = 'SINGLE' | 'MULTI' | 'TRUE_FALSE' | 'SHORT' | 'CODE';
export interface PublicQuestion { id: number; kind: QuestionKind; text_md: string; points: number; topic: string; image_url?: string; video_url?: string; video_embed?: string; video_is_file?: boolean; choices: { id: number; text: string }[] }
export type Answer = number[] | string;
export interface CorrectionItem { id: number; correct: boolean; correct_answer: number[] | string; explanation_md: string; given: Answer | null }
export interface QuizData { id: number; title: string; pass_score: number; section: number | null; lesson: number | null; course_slug: string; questions: PublicQuestion[]; best_score: number | null; attempts: number }
export interface QuizResult { score: number; passed: boolean; pass_score: number; correct: number; total: number; items: CorrectionItem[]; unlocked_section: { id: number; title: string } | null; saved: boolean }

export interface ExamItem { id: number; title: string; description: string; duration_minutes: number; question_count: number; pass_score: number; seconds_per_question: number; is_demo: boolean; available_questions: number; attempts: number; best_score: number | null }
export interface ExamAttempt { id: number; exam: number; exam_title: string; pass_score: number; duration_minutes: number; seconds_per_question: number; status: 'IN_PROGRESS' | 'SUBMITTED' | 'EXPIRED'; status_display: string; score: number | null; passed: boolean | null; correct_count: number | null; total: number; started_at: string; deadline: string; seconds_left: number; submitted_at: string | null }
export interface ExamPayload { attempt: ExamAttempt; questions: PublicQuestion[]; answers: Record<string, Answer> }
export interface ExamReport { attempt: ExamAttempt; items: (PublicQuestion & CorrectionItem)[] }
export interface ExamStats {
  attempts: number; passed: number; average: number | null; best: number | null; readiness: number | null; readiness_count: number;
  last_scores: number[]; evolution: { date: string | null; score: number; passed: boolean; exam: string }[];
  by_topic: { code: string; topic: string; correct: number; total: number; percent: number | null }[];
  quiz_attempts: number; time_seconds: number; lessons_done: number; etg_validated_at: string | null;
}
export interface StudentLmsReport extends ExamStats { history: ExamAttempt[]; quizzes: { id: number; quiz_title: string; score: number; passed: boolean; created_at: string }[]; has_lms_access: boolean; etg_validated_by: string | null }

export interface Theme { code: string; title: string; description: string; default_count: number; bank: number; label: string }
export interface AdminChoice { id?: number; text: string; is_correct: boolean; order?: number }
export interface AdminQuestion { id: number; quiz: number | null; quiz_title: string | null; kind: QuestionKind; text_md: string; explanation_md: string; expected_answer: string; points: number; order: number; topic: string; topic_label: string; image_url: string; video_url: string; in_exam_bank: boolean; is_published: boolean; choices: AdminChoice[] }
export interface AdminLessonRow { id: number; title: string; slug: string; order: number; is_published: boolean; has_video: boolean; minutes: number; completions: number }
export interface AdminQuizRow { id: number; title: string; questions: number; is_published: boolean; attempts: number; pass_rate: number | null }
export interface AdminSection { id: number; course: number; title: string; code: string; code_label: string; order: number; is_free_preview: boolean; unlock_threshold: number; lessons: AdminLessonRow[]; quiz: AdminQuizRow | null }
export interface AdminCourse { id: number; title: string; slug: string; description: string; cover_url: string; order: number; is_published: boolean; lesson_count: number; sections: AdminSection[] }
export interface AdminLesson { id: number; section: number; title: string; slug: string; order: number; video_url: string; content_md: string; estimated_minutes: number; is_published: boolean; quiz_id: number | null; completions: number }
export interface AdminQuiz { id: number; title: string; pass_score: number; is_published: boolean; section: number | null; lesson: number | null; section_title: string | null; lesson_title: string | null; question_count: number }
export interface AdminExam { id: number; title: string; description: string; duration_minutes: number; question_count: number; pass_score: number; topics: string; seconds_per_question: number; distribution: Record<string, number>; is_published: boolean; is_demo: boolean; order: number; available: number; attempts: number; pass_rate: number | null }

export function fmtDuration(seconds: number) {
  const h = Math.floor(seconds / 3600), m = Math.round((seconds % 3600) / 60);
  return h ? `${h} h ${String(m).padStart(2, '0')}` : `${m} min`;
}

export const KIND_LABEL: Record<QuestionKind, string> = { SINGLE: 'Une seule réponse', MULTI: 'Plusieurs réponses possibles', TRUE_FALSE: 'Vrai ou faux', SHORT: 'Réponse courte', CODE: 'Saisissez le code' };

export function fmtSeconds(s: number) {
  const m = Math.floor(s / 60), r = s % 60;
  return `${m}:${String(r).padStart(2, '0')}`;
}
