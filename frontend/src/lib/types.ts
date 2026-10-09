export interface MeetingPoint {
  id: number;
  name: string;
  address: string;
}

export interface Slot {
  id: number;
  date: string;
  start_time: string;
  end_time: string;
  status: 'AVAILABLE' | 'BOOKED' | 'CANCELLED' | 'CANCELLED_LATE' | 'NO_SHOW';
  status_display: string;
  meeting_point: number;
  meeting_point_name: string;
  student: number | null;
  student_name: string | null;
  instructor: number;
  instructor_name: string;
  duration_hours: number;
  is_past: boolean;
  has_lesson: boolean;
  lesson_id: number | null;
  hours_debited: boolean;
  hours_refunded: boolean;
  refund_note: string;
  cancel_reason: string;
  cancellation_fee: string;
  can_assess: boolean;
  assessment_opens_at: string;
  free_cancel_until: string | null;
}

export interface CancellationPolicy {
  notice_hours: number;
  late_penalty: 'DEBIT_HOUR' | 'FEE' | 'DEBIT_AND_FEE' | 'NONE';
  penalty_display: string;
  late_fee: string;
  late_description: string;
}

export interface FreeWindow {
  instructor_id: number;
  instructor_name: string;
  date: string;
  start_time: string;
  end_time: string;
  meeting_point: number | null;
  meeting_point_name: string | null;
  meeting_point_address: string | null;
}

export interface Availability {
  id: number;
  weekday: number;
  weekday_display: string;
  start_time: string;
  end_time: string;
  meeting_point: number | null;
  meeting_point_name: string | null;
}

export type AbsenceStatus = 'PENDING' | 'APPROVED' | 'REJECTED';
export interface Unavailability {
  id: number;
  instructor?: number;
  instructor_name?: string;
  start: string;
  end: string;
  reason: string;
  status: AbsenceStatus;
  status_display: string;
  reviewed_by_name?: string | null;
  reviewed_at?: string | null;
  review_note?: string;
}

export interface DossierItem { type: string; label: string; status: 'MISSING' | 'PENDING' | 'VERIFIED' | 'REJECTED'; note: string; required: boolean }
export interface Dossier { items: DossierItem[]; complete: boolean; pending: number; missing: number }
export interface DocumentItem {
  id: number;
  student: number;
  student_name: string;
  document_type: string;
  document_type_display: string;
  file: string;
  file_name: string;
  uploaded_at: string;
  status: 'PENDING' | 'VERIFIED' | 'REJECTED';
  status_display: string;
  review_note: string;
  reviewed_at: string | null;
  verified_by_name: string | null;
}

export interface CompetencyProgress {
  acquired: number;
  in_progress: number;
  total: number;
  percent: number;
}

export type StudentStatus = 'INCOMPLETE' | 'REGISTERED' | 'CODE' | 'DRIVING' | 'EXAM' | 'LICENSED' | 'ARCHIVED';
export const STUDENT_STATUSES: { key: StudentStatus; label: string; cls: string }[] = [
  { key: 'INCOMPLETE', label: 'Dossier incomplet', cls: 'bg-cream-200 text-brown-800' },
  { key: 'REGISTERED', label: 'Inscrit / NEPH en attente', cls: 'bg-caramel/40 text-brown-900' },
  { key: 'CODE', label: 'Code en cours', cls: 'bg-caramel text-brown-900' },
  { key: 'DRIVING', label: 'Prêt pour la conduite', cls: 'bg-brown-300 text-brown-900' },
  { key: 'EXAM', label: 'Examen réservé', cls: 'bg-brown-500 text-cream-50' },
  { key: 'LICENSED', label: 'Permis obtenu', cls: 'bg-brown-700 text-cream-50' },
  { key: 'ARCHIVED', label: 'Archivé', cls: 'bg-cream-100 text-brown-800/50' },
];
export const statusOf = (k: string) => STUDENT_STATUSES.find((s) => s.key === k) ?? STUDENT_STATUSES[0];

export interface StudentProfile {
  id: number;
  user: { id: number; first_name: string; last_name: string; email: string };
  status: StudentStatus;
  status_display: string;
  phone?: string;
  purchased_hours: number;
  used_hours: number;
  remaining_hours: number;
  reserved_hours: number;
  bookable_hours: number;
  lms_access: boolean;
  lms_access_until: string | null;
  has_lms_access: boolean;
  ready_for_exam: boolean;
  license_type: 'AUTO' | 'MANUAL';
  referent_instructor_name: string | null;
  competency_progress: CompetencyProgress;
  dossier: Dossier;
  formula: { name: string; paid_at: string | null; expires_at: string | null; hours: number } | null;
  created_at?: string;
}

export interface InstructorDashboard {
  profile: { hourly_rate: string; bio: string; is_bookable: boolean };
  today: Slot[];
  upcoming: Slot[];
  to_review: Slot[];
  students: StudentProfile[];
  month: { hours: number; lessons: number; amount: number; hourly_rate: number };
  rating: { average: number | null; count: number };
}

export type AssessmentStatus = 'NOT_COVERED' | 'IN_PROGRESS' | 'ACQUIRED';
export const STATUS_LABELS: Record<AssessmentStatus, string> = { NOT_COVERED: 'Non abordé', IN_PROGRESS: 'En cours', ACQUIRED: 'Acquis' };

export interface Competency {
  id: number;
  code: string;
  label: string;
  group: number;
  group_label: string;
  order: number;
}

export interface Assessment {
  competency: number;
  code: string;
  label: string;
  group: number;
  status: AssessmentStatus;
  status_display: string;
}

export interface Lesson {
  id: number;
  slot: Slot;
  student: number;
  student_name: string;
  instructor_name: string;
  attended: boolean;
  weather_conditions: string;
  instructor_notes: string;
  assessments: Assessment[];
  rating: { score: number; comment: string; reply: string; created_at: string } | null;
  created_at: string;
}

export interface Logbook {
  student: StudentProfile;
  progress: CompetencyProgress;
  competencies: (Competency & { status: AssessmentStatus; last_assessed: string | null })[];
  lessons: Lesson[];
}

export interface PerformanceRow {
  id: number;
  name: string;
  is_bookable: boolean;
  lessons: number;
  hours: number;
  no_shows: number;
  late_cancellations: number;
  students: number;
  rating_average: number | null;
  rating_count: number;
  recent_comments: string[];
}

export const WEEKDAYS = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche'];

export function hm(t: string) {
  return t.slice(0, 5);
}

export function frDate(iso: string, opts: Intl.DateTimeFormatOptions = { weekday: 'long', day: 'numeric', month: 'long' }) {
  return new Date(iso.length === 10 ? `${iso}T00:00:00` : iso).toLocaleDateString('fr-FR', opts);
}

export function apiError(err: any, fallback: string): string {
  const d = err?.response?.data;
  if (!d) return fallback;
  if (typeof d.detail === 'string') return d.detail;
  const first = Object.values(d)[0];
  return Array.isArray(first) ? String(first[0]) : fallback;
}
