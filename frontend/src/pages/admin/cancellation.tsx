import { useEffect, useState } from 'react';
import api from '@/lib/api';
import { BACKOFFICE, useRequireAuth } from '@/hooks/useRequireAuth';
import AdminShell from '@/components/AdminShell';
import BackLink from '@/components/BackLink';
import { CancellationPolicy, apiError } from '@/lib/types';

const PENALTIES: { key: CancellationPolicy['late_penalty']; label: string; help: string }[] = [
  { key: 'DEBIT_HOUR', label: 'Heure décomptée', help: "L'heure réservée est définitivement retirée du solde de l'élève." },
  { key: 'FEE', label: "Frais d'annulation", help: "L'heure est restituée, des frais forfaitaires sont enregistrés sur la leçon." },
  { key: 'DEBIT_AND_FEE', label: 'Heure décomptée + frais', help: "Les deux s'appliquent." },
  { key: 'NONE', label: 'Aucune pénalité', help: "Le motif reste obligatoire, mais l'heure est toujours restituée." },
];

export default function CancellationRules() {
  const ready = useRequireAuth(BACKOFFICE);
  const [form, setForm] = useState<{ notice_hours: string; late_penalty: CancellationPolicy['late_penalty']; late_fee: string } | null>(null);
  const [preview, setPreview] = useState('');
  const [msg, setMsg] = useState<{ ok: boolean; text: string } | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (!ready) return;
    api.get('/cancellation-policy/').then((r) => {
      setForm({ notice_hours: String(r.data.notice_hours), late_penalty: r.data.late_penalty, late_fee: String(Number(r.data.late_fee)) });
      setPreview(r.data.late_description);
    });
  }, [ready]);

  const needsFee = form?.late_penalty === 'FEE' || form?.late_penalty === 'DEBIT_AND_FEE';

  const save = async (e: React.FormEvent) => {
    e.preventDefault(); if (!form) return;
    setBusy(true); setMsg(null);
    try {
      const r = await api.put('/cancellation-policy/', { notice_hours: Number(form.notice_hours), late_penalty: form.late_penalty, late_fee: needsFee ? form.late_fee : '0' });
      setPreview(r.data.late_description);
      setMsg({ ok: true, text: 'Règles enregistrées : elles s’appliquent aux prochaines annulations.' });
    } catch (err: any) {
      const d = err?.response?.data;
      setMsg({ ok: false, text: d?.late_fee?.[0] ?? d?.notice_hours?.[0] ?? apiError(err, 'Enregistrement impossible.') });
    } finally { setBusy(false); }
  };

  return (
    <AdminShell title="Règles d'annulation">
      <BackLink fallbackHref="/admin" fallbackLabel="← Retour au tableau de bord" />
      <h1 className="text-3xl mb-2">Règles d'annulation</h1>
      <p className="text-brown-800/70 mb-6">Conditions appliquées quand un élève annule une leçon depuis son espace. Le motif est toujours obligatoire. Une dérogation (re-crédit sur justificatif) reste possible depuis le planning ou la fiche élève.</p>
      {msg && <div className={`rounded-xl px-4 py-3 mb-4 text-sm ${msg.ok ? 'border border-brown-300 bg-brown-50' : 'border border-red-200 bg-red-50 text-red-700'}`}>{msg.text}</div>}
      {!form ? <p className="text-brown-500">Chargement…</p> : (
        <form onSubmit={save} className="card max-w-2xl space-y-6">
          <label className="block">
            <span className="font-medium">Délai de préavis sans frais (heures avant la leçon)</span>
            <input type="number" min={0} max={720} required value={form.notice_hours} onChange={(e) => setForm({ ...form, notice_hours: e.target.value })} className="input-field mt-1 sm:w-40" />
            <span className="block text-xs text-brown-800/60 mt-1">Avant ce délai, l'annulation est gratuite et l'heure est automatiquement re-créditée au solde de l'élève.</span>
          </label>
          <fieldset>
            <legend className="font-medium mb-2">Si l'élève annule après le délai</legend>
            <div className="space-y-2">
              {PENALTIES.map((p) => (
                <label key={p.key} className={`flex items-start gap-3 rounded-xl border px-3 py-2 cursor-pointer ${form.late_penalty === p.key ? 'border-brown-700 bg-brown-50' : 'border-cream-300'}`}>
                  <input type="radio" name="penalty" checked={form.late_penalty === p.key} onChange={() => setForm({ ...form, late_penalty: p.key })} className="mt-1 accent-brown-700" />
                  <span><span className="font-medium">{p.label}</span><span className="block text-xs text-brown-800/60">{p.help}</span></span>
                </label>
              ))}
            </div>
          </fieldset>
          {needsFee && (
            <label className="block">
              <span className="font-medium">Montant des frais d'annulation (€)</span>
              <input type="number" min={0} step="0.01" required value={form.late_fee} onChange={(e) => setForm({ ...form, late_fee: e.target.value })} className="input-field mt-1 sm:w-40" />
            </label>
          )}
          {preview && <p className="text-sm text-brown-800/70">Actuellement, en cas d'annulation tardive : <em>{preview}</em>.</p>}
          <button disabled={busy} className="btn-primary disabled:opacity-60">{busy ? 'Enregistrement…' : 'Enregistrer les règles'}</button>
        </form>
      )}
    </AdminShell>
  );
}
