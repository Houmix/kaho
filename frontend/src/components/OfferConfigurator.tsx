import { useEffect, useMemo, useState } from 'react';
import api from '@/lib/api';
import { Offer, billingSuffix, formatPrice, offerHighlights } from '@/lib/offers';
import { Competency, apiError } from '@/lib/types';

interface Props { base: Offer; offers: Offer[]; onDone: (text: string, ok?: boolean) => void; onCancel: () => void }

/** Configurateur élève : formule de base + options + compétences à travailler → demande enregistrée (puis paiement en ligne ou à l'école). */
export default function OfferConfigurator({ base, offers, onDone, onCancel }: Props) {
  const addons = useMemo(() => offers.filter((o) => o.is_addon && o.id !== base.id), [offers, base]);
  const [selected, setSelected] = useState<number[]>([]);
  const [skills, setSkills] = useState<string[]>([]);
  const [competencies, setCompetencies] = useState<Competency[]>([]);
  const [busy, setBusy] = useState(false);
  const pickers = [base, ...addons.filter((a) => selected.includes(a.id))].filter((o) => o.lets_student_pick_skills);
  const allowed = pickers.flatMap((o) => o.skills);
  useEffect(() => { if (pickers.length) api.get('/competencies/').then((r) => setCompetencies(r.data.results ?? r.data)); }, [pickers.length]);
  const total = Number(base.price) + addons.filter((a) => selected.includes(a.id)).reduce((s, a) => s + Number(a.price), 0);
  const choices = competencies.filter((c) => allowed.length === 0 || allowed.includes(c.code));

  const submit = async () => {
    setBusy(true);
    try {
      const r = await api.post('/packages/', { offer: base.id, addons: selected, skills });
      onDone(`Demande enregistrée : ${base.name}${selected.length ? ` + ${selected.length} option(s)` : ''} — ${formatPrice(r.data.bundle_total)}. Payez en ligne ci-dessous ou auprès de votre école.`);
    } catch (err) { onDone(apiError(err, 'Enregistrement impossible.'), false); }
    finally { setBusy(false); }
  };

  return (
    <section className="card border-brown-300 mb-8">
      <div className="flex flex-wrap items-start justify-between gap-3 mb-4">
        <div><p className="text-xs uppercase tracking-wide text-caramel font-medium">Composez votre formule</p><h2 className="text-2xl">{base.name}</h2><p className="text-sm text-brown-800/70">{offerHighlights(base).join(' · ')}</p></div>
        <button onClick={onCancel} className="text-sm text-brown-700 hover:underline">← Changer de formule</button>
      </div>
      {addons.length > 0 && (
        <div className="mb-4">
          <h3 className="font-semibold mb-2">Options</h3>
          <div className="grid sm:grid-cols-2 gap-2">
            {addons.map((a) => (
              <label key={a.id} className={`flex items-start gap-3 rounded-xl border px-3 py-2.5 cursor-pointer ${selected.includes(a.id) ? 'border-brown-700 bg-brown-50' : 'border-cream-300 bg-white hover:border-brown-300'}`}>
                <input type="checkbox" checked={selected.includes(a.id)} onChange={(e) => setSelected(e.target.checked ? [...selected, a.id] : selected.filter((x) => x !== a.id))} className="accent-brown-700 mt-1" />
                <span className="flex-1"><span className="font-medium">{a.name}</span> <span className="text-brown-700 font-semibold">+ {formatPrice(a.price)}</span><br /><span className="text-xs text-brown-800/70">{a.description || offerHighlights(a).join(' · ')}</span></span>
              </label>
            ))}
          </div>
        </div>
      )}
      {pickers.length > 0 && (
        <div className="mb-4">
          <h3 className="font-semibold mb-1">Compétences à travailler</h3>
          <p className="text-xs text-brown-800/60 mb-2">Choisissez ce que vous souhaitez perfectionner (stationnement, autoroute, conduite de nuit…). Votre moniteur adaptera les leçons.</p>
          <div className="flex flex-wrap gap-1.5">
            {choices.map((c) => <button key={c.code} type="button" onClick={() => setSkills(skills.includes(c.code) ? skills.filter((x) => x !== c.code) : [...skills, c.code])} className={`badge !px-3 !py-1.5 text-left ${skills.includes(c.code) ? 'bg-brown-700 text-cream-50' : 'bg-cream-100 text-brown-800 hover:bg-cream-200'}`}>{c.code} {c.label}</button>)}
          </div>
        </div>
      )}
      <div className="flex flex-wrap items-center justify-between gap-3 border-t border-cream-200 pt-4">
        <div><p className="text-sm text-brown-800/70">Total</p><p className="text-3xl font-display text-brown-700">{formatPrice(total)} <span className="text-sm font-sans text-brown-800/60">{base.billing_type === 'MONTHLY' ? billingSuffix(base) : base.installments > 1 ? `soit ${base.installments} × ${formatPrice(total / base.installments)} sans frais` : ''}</span></p></div>
        <button onClick={submit} disabled={busy} className="btn-primary">{busy ? 'Enregistrement…' : 'Valider ma formule'}</button>
      </div>
    </section>
  );
}
