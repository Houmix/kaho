import { BACKOFFICE, useRequireAuth } from '@/hooks/useRequireAuth';
import AdminShell from '@/components/AdminShell';
import MeetingPointsManager from '@/components/MeetingPointsManager';

export default function AdminMeetingPoints() {
  const ready = useRequireAuth(BACKOFFICE);
  return (
    <AdminShell title="Points de rendez-vous">
      <h1 className="text-3xl mb-2">Points de rendez-vous</h1>
      <p className="text-brown-800/70 mb-6">Lieux proposés aux élèves à la réservation (gare, parking, domicile de l'école…). Les moniteurs peuvent aussi en ajouter depuis leurs disponibilités.</p>
      <div className="card">{ready && <MeetingPointsManager />}</div>
    </AdminShell>
  );
}
