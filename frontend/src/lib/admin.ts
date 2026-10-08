import { Lesson, Slot, StudentProfile, Availability } from './types';
import { Package } from './offers';

export interface Overview {
  month: { revenue: number; sales: number; label: string };
  unpaid: { count: number; amount: number };
  students: { active: number; total: number };
  instructors: { total: number; bookable: number; pending_applications: number; without_password: number };
  occupancy: { percent: number | null; booked_hours: number; opened_hours: number };
  rating: { average: number | null; count: number };
  today: { lessons: number; to_review: number; no_shows_week: number };
  alerts: { kind: string; count: number; text: string; href: string }[];
}

export interface SearchResults {
  students: { id: number; name: string; email: string; remaining_hours: number; href: string }[];
  instructors: { id: number; name: string; email: string; href: string }[];
  packages: { id: number; label: string; status: string; href: string }[];
  slots: { id: number; label: string; status: string; href: string }[];
}

export interface Paginated<T> { count: number; next: string | null; previous: string | null; results: T[] }

export interface InstructorAdmin {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  full_name: string;
  is_active: boolean;
  has_password: boolean;
  created_at: string;
  profile: { id: number; hourly_rate: string; phone: string; gearbox: 'AUTO' | 'MANUAL' | 'BOTH'; gearbox_display: string; vehicle: string; bio: string; is_bookable: boolean };
  stats: { upcoming: number; lessons: number; students: number; availability_slots: number; rating_average: number | null; rating_count: number };
}

export interface Application {
  id: number;
  first_name: string;
  last_name: string;
  email: string;
  phone: string;
  gearbox: 'AUTO' | 'MANUAL' | 'BOTH';
  gearbox_display: string;
  message: string;
  diploma: string;
  driving_license: string;
  business_doc: string | null;
  status: 'PENDING' | 'APPROVED' | 'REJECTED';
  status_display: string;
  admin_note: string;
  reviewed_by_name: string | null;
  reviewed_at: string | null;
  created_user: number | null;
  created_at: string;
}

export interface RatingAdmin {
  id: number;
  score: number;
  comment: string;
  reply: string;
  is_hidden: boolean;
  student_name: string;
  instructor_name: string;
  instructor_id: number;
  lesson_date: string;
  created_at: string;
}

export interface StudentOverview {
  student: StudentProfile & { phone: string; neph_number: string; emergency_contact: string; emergency_phone: string; referent_instructor: number | null };
  packages: Package[];
  upcoming_slots: Slot[];
  past_slots: Slot[];
  lessons: Lesson[];
  documents: { id: number; document_type: string; file: string; verified: boolean; uploaded_at: string }[];
  progress: { acquired: number; in_progress: number; total: number; percent: number };
}

export interface InstructorOverview {
  instructor: InstructorAdmin;
  availabilities: Availability[];
  upcoming_slots: Slot[];
  students: StudentProfile[];
  ratings: RatingAdmin[];
}

export const GEARBOX_LABELS = { AUTO: 'Automatique', MANUAL: 'Manuelle', BOTH: 'Les deux' };

export function exportCsv(filename: string, headers: string[], rows: (string | number | null | undefined)[][]) {
  const esc = (v: unknown) => `"${String(v ?? '').replace(/"/g, '""')}"`;
  const csv = [headers, ...rows].map((r) => r.map(esc).join(';')).join('\n');
  const blob = new Blob(['﻿' + csv], { type: 'text/csv;charset=utf-8' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = filename;
  a.click();
  URL.revokeObjectURL(a.href);
}
