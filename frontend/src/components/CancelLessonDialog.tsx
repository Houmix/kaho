import { useEffect, useState } from 'react';
import api from '@/lib/api';
import { CancellationPolicy, Slot, apiError, frDate, hm } from '@/lib/types';

/** Annulation d'une leçon par l'élève : rappelle la règle de l'école, exige un motif, annonce la conséquence avant de valider. */
export default function CancelLessonDialog({ slot, onClose, onDone }: { slot: Slot; onClose: () => void; onDone: (text: string) => void }) {
  const [policy, setPolicy] = useState<CancellationPolicy | null>(null);
  const [reason, setReason] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => { api.get('/cancellation-policy/').then((r) => setPolicy(r.data)).catch(() => {}); }, []);

  const freeUntil = slot.free_cancel_until ? new Date(slot.free_cancel_until) : null;
  const late = freeUntil ? new Date() > freeUntil : false;
  const fmt = (d: Date) => d.toLocaleString('fr-FR', { weekday: 'long', day: 'numeric', month: 'long', hour: '2-digit', minute: '2-digit' });

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!reason.trim()) { setError('Merci d’indiquer le motif de votre annulation.'); return; }
    setBusy(true); setError('');
    try {
      const r = await api.post(`/slots/${slot.id}/cancel/`, { reason: reason.trim() });
      const s: Slot = r.data;
      onDone(s.status === 'CANCELLED_LATE'
        ? `Leçon annulée hors délai : ${policy?.late_description ?? 'une pénalité s’applique'}.`
        : 'Leçon annulée : votre heure a été re-créditée sur votre solde.');
    } catch (err) { setError(apiError(err, 'Annulation impossible.')); }
    finally { setBusy(false); }
  };

  return (
    <div className="fixed inset-0 z-40 bg-brown-900/40 flex items-end sm:items-center justify-center p-4" onClick={onClose}>
      <form onSubmit={submit} onClick={(e) => e.stopPropagation()} className="card w-full max-w-md space-y-4" role="dialog" aria-modal="true" aria-label="Annuler la leçon">
        <div>
          <h2 className="text-xl">Annuler cette leçon ?</h2>
          <p className="text-sm text-brown-800/70 mt-1">{frDate(slot.date)} · {hm(slot.start_time)}–{hm(slot.end_time)} · {slot.instructor_name}</p>
        </div>
        {freeUntil && (late ? (
          <div className="rounded-xl border border-caramel bg-brown-50 px-3 py-2 text-sm">
            <strong>Annulation tardive.</strong> L'annulation gratuite était possible jusqu'au {fmt(freeUntil)}
            {policy ? ` (${policy.notice_hours} h avant la leçon). Si vous annulez maintenant, ${policy.late_description}.` : '.'}
          </div>
        ) : (
          <div className="rounded-xl border border-cream-300 bg-cream-50 px-3 py-2 text-sm">
            Annulation <strong>gratuite</strong> jusqu'au {fmt(freeUntil)} : votre heure vous est re-créditée.
          </div>
        ))}
        <label className="block">
          <span className="text-sm font-medium text-brown-800">Motif de l'annulation <span className="text-red-700">*</span></span>
          <textarea value={reason} onChange={(e) => setReason(e.target.value)} className="input-field mt-1" rows={3} maxLength={500} required placeholder="Ex : maladie, empêchement professionnel…" />
        </label>
        {error && <p className="text-sm text-red-700">{error}</p>}
        <div className="flex flex-wrap justify-end gap-2">
          <button type="button" onClick={onClose} className="btn-secondary">Garder ma leçon</button>
          <button type="submit" disabled={busy} className="btn-primary disabled:opacity-60">{busy ? 'Annulation…' : 'Confirmer l’annulation'}</button>
        </div>
      </form>
    </div>
  );
}
