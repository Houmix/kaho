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
export interface PublicQuestion { id: number; kind: QuestionKind; text_md: string; points: number; topic: string; choices: { id: number; text: string }[] }
export type Answer = number[] | string;
export interface CorrectionItem { id: number; correct: boolean; correct_answer: number[] | string; explanation_md: string; given: Answer | null }
export interface QuizData { id: number; title: string; pass_score: number; section: number | null; lesson: number | null; course_slug: string; questions: PublicQuestion[]; best_score: number | null; attempts: number }
export interface QuizResult { score: number; passed: boolean; pass_score: number; correct: number; total: number; items: CorrectionItem[]; unlocked_section: { id: number; title: string } | null; saved: boolean }

export interface ExamItem { id: number; title: string; description: string; duration_minutes: number; question_count: number; pass_score: number; is_demo: boolean; available_questions: number; attempts: number; best_score: number | null }
export interface ExamAttempt { id: number; exam: number; exam_title: string; pass_score: number; duration_minutes: number; status: 'IN_PROGRESS' | 'SUBMITTED' | 'EXPIRED'; status_display: string; score: number | null; passed: boolean | null; correct_count: number | null; total: number; started_at: string; deadline: string; seconds_left: number; submitted_at: string | null }
export interface ExamPayload { attempt: ExamAttempt; questions: PublicQuestion[]; answers: Record<string, Answer> }
export interface ExamReport { attempt: ExamAttempt; items: (PublicQuestion & CorrectionItem)[] }
export interface ExamStats { attempts: number; passed: number; average: number | null; best: number | null; last_scores: number[]; by_topic: { topic: string; correct: number; total: number; percent: number }[] }

export const KIND_LABEL: Record<QuestionKind, string> = { SINGLE: 'Une seule réponse', MULTI: 'Plusieurs réponses possibles', TRUE_FALSE: 'Vrai ou faux', SHORT: 'Réponse courte', CODE: 'Saisissez le code' };

export function fmtSeconds(s: number) {
  const m = Math.floor(s / 60), r = s % 60;
  return `${m}:${String(r).padStart(2, '0')}`;
}
