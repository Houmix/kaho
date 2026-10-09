import { useEffect, useState } from 'react';
import Link from 'next/link';
import api from '@/lib/api';
import { useAuth } from '@/hooks/useAuth';
import { useRequireAuth } from '@/hooks/useRequireAuth';
import AppShell from '@/components/AppShell';
import ProgressGauge from '@/components/ProgressGauge';
import { Lesson, StudentProfile } from '@/lib/types';
import { ExamStats } from '@/lib/lms';
import { ReadinessGauge } from '@/components/LmsAnalytics';

const links = [
  { href: '/student/reservation', title: 'Réserver une leçon', text: 'Créneaux disponibles et points de rendez-vous' },
  { href: '/student/notebook', title: 'Livret d’apprentissage', text: 'Bilans de leçons et compétences validées' },
  { href: '/code', title: 'Code en ligne', text: 'Cours, quiz et examens blancs' },
  { href: '/student/documents', title: 'Mes documents', text: 'Pièce d’identité, NEPH, contrat' },
  { href: '/student/purchases', title: 'Offres & heures', text: 'Formules, recharges et accès au code en ligne' },
];

export default function StudentDashboard() {
  const [profile, setProfile] = useState<StudentProfile | null>(null);
  const [toRate, setToRate] = useState<Lesson[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [stats, setStats] = useState<ExamStats | null>(null);
  const { user } = useAuth();
  const ready = useRequireAuth('STUDENT');

  useEffect(() => {
    if (!ready) return;
    Promise.all([api.get('/student-profiles/my_profile/'), api.get('/lessons/to_rate/')])
      .then(([p, t]) => { setProfile(p.data); setToRate(t.data); if (p.data.has_lms_access) api.get('/lms/exam-attempts/stats/').then((r) => setStats(r.data)).catch(() => {}); })
      .catch((e) => console.error(e))
      .finally(() => setIsLoading(false));
  }, [ready]);

  if (isLoading) return <AppShell title="Mon espace"><p className="text-brown-500">Chargement…</p></AppShell>;
  if (!profile) return <AppShell title="Mon espace"><p className="text-brown-500">Profil introuvable</p></AppShell>;

  const progress = Math.min((profile.used_hours / (profile.purchased_hours || 1)) * 100, 100);

  return (
    <AppShell title="Mon espace">
        <h1 className="text-3xl mb-6">Bonjour, {user?.first_name} 👋</h1>

        {!profile.dossier.complete && (
          <Link href="/student/documents" className="card block mb-6 hover:border-brown-300">
            <p className="font-semibold">Dossier administratif incomplet</p>
            <p className="text-sm text-brown-800/70">{profile.dossier.missing} pièce{profile.dossier.missing > 1 ? 's' : ''} à fournir{profile.dossier.pending ? ` · ${profile.dossier.pending} en vérification` : ''} →</p>
          </Link>
        )}
        {toRate.length > 0 && (
          <Link href="/student/notebook" className="card block mb-6 border-caramel bg-brown-50 hover:border-brown-300">
            <p className="font-semibold">Comment s'est passée votre dernière leçon ?</p>
            <p className="text-sm text-brown-800/70">{toRate.length} leçon{toRate.length > 1 ? 's' : ''} à noter — votre avis aide votre moniteur à s'améliorer.</p>
          </Link>
        )}

        <div className="grid md:grid-cols-3 gap-6 mb-8">
          <div className="card">
            <h2 className="text-xl mb-4">Compétences</h2>
            <ProgressGauge progress={profile.competency_progress} compact />
            <Link href="/student/notebook" className="text-sm text-brown-700 hover:underline mt-3 inline-block">Voir le livret →</Link>
          </div>
          <div className="card">
            <h2 className="text-xl mb-4">Votre progression</h2>
            <div className="flex justify-between text-sm mb-2">
              <span className="text-brown-800/70">Heures effectuées</span>
              <span className="font-semibold">{profile.used_hours.toFixed(1)} h / {profile.purchased_hours.toFixed(1)} h</span>
            </div>
            <div className="w-full bg-cream-200 rounded-full h-2.5">
              <div className="bg-brown-700 h-2.5 rounded-full transition-all" style={{ width: `${progress}%` }} />
            </div>
            <p className="mt-3 text-brown-800/70">
              Il vous reste <strong className="text-brown-900">{profile.remaining_hours.toFixed(1)} h</strong>
              {profile.reserved_hours > 0 && <span className="text-sm"> dont {profile.reserved_hours.toFixed(1)} h déjà réservées</span>}
            </p>
            {profile.referent_instructor_name && <p className="text-sm text-brown-800/60 mt-1">Moniteur référent : {profile.referent_instructor_name}</p>}
          </div>

          <div className="card">
            <h2 className="text-xl mb-4">Préparation à l’examen</h2>
            <dl className="space-y-3">
              <div className="flex justify-between">
                <dt className="text-brown-800/70">Boîte</dt>
                <dd className="font-medium">{profile.license_type === 'AUTO' ? 'Automatique' : 'Manuelle'}</dd>
              </div>
              <div className="flex justify-between items-center">
                <dt className="text-brown-800/70">Prêt pour l’examen</dt>
                <dd>
                  <span className={`badge ${profile.ready_for_exam ? 'bg-brown-700 text-cream-50' : 'bg-cream-200 text-brown-800'}`}>
                    {profile.ready_for_exam ? 'Oui' : 'Pas encore'}
                  </span>
                </dd>
              </div>
            </dl>
          </div>
        </div>

        {stats && (
          <Link href="/code" className="card block mb-8 hover:border-brown-300">
            <div className="flex flex-wrap items-center justify-between gap-4">
              <div><h2 className="text-xl mb-1">Code en ligne</h2><p className="text-sm text-brown-800/70">{stats.attempts} examen(s) blanc(s) · {stats.lessons_done} leçon(s) terminée(s){stats.etg_validated_at ? ' · inscription à l’examen validée ✓' : ''}</p></div>
              <ReadinessGauge value={stats.readiness} count={stats.readiness_count} compact />
            </div>
          </Link>
        )}

        <div className="grid md:grid-cols-2 gap-6">
          {links.map((l) => (
            <Link key={l.href} href={l.href} className="card hover:border-brown-300 transition-colors">
              <h3 className="text-xl mb-1">{l.title}</h3>
              <p className="text-brown-800/70">{l.text}</p>
            </Link>
          ))}
        </div>
    </AppShell>
  );
}
