import { useEffect, useState } from 'react';
import api from '@/lib/api';
import { InstructorAdmin } from '@/lib/admin';
import { Offer, PAYMENT_METHODS, formatPrice } from '@/lib/offers';
import { STUDENT_STATUSES, StudentProfile, apiError, statusOf } from '@/lib/types';

export type ActionKey = 'status' | 'credit' | 'debit' | 'payment' | 'link' | 'lms' | 'referent';
const ACTIONS: { key: ActionKey; label: string; icon: string }[] = [
  { key: 'status', label: 'Changer le statut', icon: '◉' },
  { key: 'credit', label: 'Créditer des heures', icon: '+' },
  { key: 'debit', label: 'Retirer des heures', icon: '−' },
  { key: 'payment', label: 'Saisir un règlement', icon: '€' },
  { key: 'link', label: 'Envoyer un lien de paiement', icon: '↗' },
  { key: 'lms', label: 'Accès code en ligne', icon: '▣' },
  { key: 'referent', label: 'Moniteur référent', icon: '◆' },
];

interface Props {
  student: StudentProfile & { referent_instructor?: number | null };
  onDone: (text: string) => void;
  onError?: (text: string) => void;
  initial?: ActionKey;
  compact?: boolean;
}

/** Panneau d'actions rapides sur un élève : utilisable dans un tiroir (liste) ou dans la fiche. */
export default function StudentActions({ student, onDone, onError, initial, compact }: Props) {
  const [action, setAction] = useState<ActionKey>(initial ?? 'status');
  const [offers, setOffers] = useState<Offer[]>([]);
  const [instructors, setInstructors] = useState<InstructorAdmin[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [f, setF] = useState<Record<string, string>>({ hours: '', note: '', offer: '', amount: '', label: '', method: 'CASH', channel: 'email', months: '6', until: '', referent: String(student.referent_instructor ?? '') });
  const [link, setLink] = useState('');
  const set = (k: string, v: string) => setF((p) => ({ ...p, [k]: v }));
  const id = student.id;

  useEffect(() => {
    api.get('/offers/').then((r) => setOffers(r.data)).catch(() => {});
    api.get('/admin/instructors/', { params: { page_size: 200, active: 1 } }).then((r) => setInstructors(r.data.results)).catch(() => {});
  }, []);
  useEffect(() => { if (initial) setAction(initial); }, [initial]);

  const run = async (fn: () => Promise<any>, ok: (r: any) => string) => {
    setBusy(true); setError(''); setLink('');
    try { const r = await fn(); onDone(ok(r)); setF((p) => ({ ...p, hours: '', note: '', amount: '', label: '' })); }
    catch (err) { const t = apiError(err, 'Action impossible.'); setError(t); onError?.(t); }
    finally { setBusy(false); }
  };
  const offerFields = (
    <>
      <select value={f.offer} onChange={(e) => set('offer', e.target.value)} className="input-field !py-2">
        <option value="">Montant libre…</option>
        {offers.map((o) => <option key={o.id} value={o.id}>{o.name} — {formatPrice(o.price)}{o.hours ? ` · ${o.hours} h` : ''}</option>)}
      </select>
      {!f.offer && (
        <div className="grid grid-cols-3 gap-2">
          <input type="number" min="1" step="1" placeholder="Montant €" value={f.amount} onChange={(e) => set('amount', e.target.value)} className="input-field !py-2" required />
          <input type="number" min="0" step="0.5" placeholder="Heures" value={f.hours} onChange={(e) => set('hours', e.target.value)} className="input-field !py-2" />
          <input placeholder="Libellé (acompte…)" value={f.label} onChange={(e) => set('label', e.target.value)} className="input-field !py-2" />
        </div>
      )}
    </>
  );

  return (
    <div className={compact ? '' : 'grid sm:grid-cols-[200px_1fr] gap-4'}>
      <div className={`flex ${compact ? 'flex-wrap gap-1 mb-3' : 'flex-col gap-0.5'}`}>
        {ACTIONS.map((a) => (
          <button key={a.key} type="button" onClick={() => { setAction(a.key); setError(''); setLink(''); }}
            className={`text-left rounded-lg px-2.5 py-1.5 text-sm flex items-center gap-2 ${action === a.key ? 'bg-brown-700 text-cream-50' : 'hover:bg-cream-200 text-brown-800'}`}>
            <span className="w-4 text-center opacity-70">{a.icon}</span>{a.label}
          </button>
        ))}
      </div>
      <div className="min-w-0">
        {error && <p className="text-sm text-red-700 mb-2">{error}</p>}
        {link && <p className="text-xs bg-cream-100 rounded-lg p-2 mb-2 break-all">Lien : <a href={link} target="_blank" rel="noreferrer" className="text-brown-700 underline">{link}</a></p>}

        {action === 'status' && (
          <div>
            <p className="text-sm text-brown-800/70 mb-2">Statut actuel : <span className={`badge ${statusOf(student.status).cls}`}>{student.status_display}</span></p>
            <div className="flex flex-wrap gap-1.5">
              {STUDENT_STATUSES.map((s) => (
                <button key={s.key} disabled={busy || s.key === student.status} onClick={() => run(() => api.post(`/admin/students/${id}/set_status/`, { status: s.key }), () => `Statut : ${s.label}.`)}
                  className={`badge !px-3 !py-1.5 ${s.key === student.status ? 'ring-2 ring-brown-700 ' + s.cls : 'bg-cream-100 text-brown-800 hover:bg-cream-200'}`}>{s.label}</button>
              ))}
            </div>
          </div>
        )}

        {(action === 'credit' || action === 'debit') && (
          <form onSubmit={(e) => { e.preventDefault(); run(() => api.post(`/admin/students/${id}/${action === 'credit' ? 'adjust_hours' : 'debit_hours'}/`, { hours: f.hours, note: f.note }), () => `${f.hours} h ${action === 'credit' ? 'créditée(s)' : 'retirée(s)'}.`); }} className="space-y-2">
            <p className="text-sm text-brown-800/70">{action === 'credit' ? 'Geste commercial, régularisation : tracé comme un achat offert.' : 'Correction d’une erreur de saisie. Solde actuel :'} <strong>{student.remaining_hours.toFixed(1)} h</strong></p>
            <div className="flex gap-2">
              <input type="number" step="0.5" min="0.5" placeholder="Heures" value={f.hours} onChange={(e) => set('hours', e.target.value)} className="input-field w-28 !py-2" required />
              <input placeholder="Motif (obligatoire)" value={f.note} onChange={(e) => set('note', e.target.value)} className="input-field !py-2" required />
            </div>
            <button disabled={busy} className="btn-primary !py-2 text-sm">{action === 'credit' ? 'Créditer' : 'Retirer'}</button>
          </form>
        )}

        {action === 'payment' && (
          <form onSubmit={(e) => { e.preventDefault(); run(() => api.post(`/admin/students/${id}/record_payment/`, { offer: f.offer || undefined, amount: f.amount, hours: f.hours || 0, label: f.label, method: f.method, note: f.note }), (r) => `Règlement enregistré (${r.data.payment_method_display}), reçu ${r.data.invoice_number} généré, heures et accès crédités.`); }} className="space-y-2">
            <p className="text-sm text-brown-800/70">Règlement reçu hors ligne : l'achat est validé et un reçu (facture acquittée) est généré.</p>
            {offerFields}
            <div className="flex gap-2">
              <select value={f.method} onChange={(e) => set('method', e.target.value)} className="input-field !py-2 w-44">{PAYMENT_METHODS.map((m) => <option key={m.key} value={m.key}>{m.label}</option>)}</select>
              <input placeholder="Note (n° de chèque, dossier CPF…)" value={f.note} onChange={(e) => set('note', e.target.value)} className="input-field !py-2" />
            </div>
            <button disabled={busy} className="btn-primary !py-2 text-sm">Enregistrer le règlement</button>
          </form>
        )}

        {action === 'link' && (
          <form onSubmit={(e) => { e.preventDefault(); run(() => api.post(`/admin/students/${id}/payment_link/`, { offer: f.offer || undefined, amount: f.amount, hours: f.hours || 0, label: f.label, channel: f.channel }).then((r) => { setLink(r.data.link); return r; }), (r) => `Lien de paiement ${formatPrice(r.data.amount_paid)} envoyé par ${f.channel === 'both' ? 'email et SMS' : f.channel === 'sms' ? 'SMS' : 'email'}.`); }} className="space-y-2">
            <p className="text-sm text-brown-800/70">Paiement sécurisé par carte (Stripe). Les heures sont créditées automatiquement dès le paiement.</p>
            {offerFields}
            <div className="flex gap-2 items-center text-sm">
              <span className="text-brown-800/70">Envoyer par</span>
              {[['email', 'Email'], ['sms', 'SMS'], ['both', 'Les deux']].map(([k, l]) => <label key={k} className="flex items-center gap-1"><input type="radio" name="channel" checked={f.channel === k} onChange={() => set('channel', k)} className="accent-brown-700" />{l}</label>)}
              {!student.phone && f.channel !== 'email' && <span className="text-red-700 text-xs">(pas de mobile renseigné)</span>}
            </div>
            <button disabled={busy} className="btn-primary !py-2 text-sm">{busy ? 'Génération…' : 'Générer et envoyer le lien'}</button>
          </form>
        )}

        {action === 'lms' && (
          <div className="space-y-2">
            <p className="text-sm text-brown-800/70">Accès actuel : <strong>{student.has_lms_access ? (student.lms_access_until ? `jusqu'au ${new Date(student.lms_access_until).toLocaleDateString('fr-FR')}` : 'illimité') : 'aucun'}</strong></p>
            <form onSubmit={(e) => { e.preventDefault(); run(() => api.post(`/admin/students/${id}/adjust_lms/`, { months: f.until ? undefined : f.months, until: f.until || undefined, note: f.note }), () => 'Accès code en ligne mis à jour.'); }} className="space-y-2">
              <div className="flex gap-2 items-center text-sm">
                <span>Prolonger de</span><input type="number" min="1" value={f.months} onChange={(e) => set('months', e.target.value)} className="input-field w-20 !py-2" /><span>mois, ou jusqu'au</span>
                <input type="date" value={f.until} onChange={(e) => set('until', e.target.value)} className="input-field !py-2 w-40" />
              </div>
              <input placeholder="Motif (obligatoire)" value={f.note} onChange={(e) => set('note', e.target.value)} className="input-field !py-2" required />
              <div className="flex gap-2">
                <button disabled={busy} className="btn-primary !py-2 text-sm">Activer / prolonger</button>
                {student.lms_access && <button type="button" disabled={busy || !f.note} onClick={() => run(() => api.post(`/admin/students/${id}/adjust_lms/`, { enabled: false, note: f.note }), () => 'Accès code en ligne retiré.')} className="btn-outline !py-2 text-sm text-red-700 border-red-300">Retirer l'accès</button>}
              </div>
            </form>
          </div>
        )}

        {action === 'referent' && (
          <div className="space-y-2">
            <p className="text-sm text-brown-800/70">Moniteur référent : suit la progression, apparaît sur la fiche et dans les filtres.</p>
            <select value={f.referent} onChange={(e) => { set('referent', e.target.value); run(() => api.patch(`/admin/students/${id}/update_profile/`, { referent_instructor: e.target.value || null }), () => 'Moniteur référent mis à jour.'); }} className="input-field !py-2">
              <option value="">— aucun —</option>
              {instructors.map((i) => <option key={i.id} value={i.id}>{i.full_name}{i.profile.zones ? ` · ${i.profile.zones}` : ''}</option>)}
            </select>
          </div>
        )}
      </div>
    </div>
  );
}
