import { useState } from 'react';
import Link from 'next/link';
import api from '@/lib/api';
import { Offer } from '@/lib/offers';
import OfferCard from './OfferCard';

type Answers = { code_status?: 'TO_PASS' | 'OBTAINED'; level?: 'BEGINNER' | 'REFRESH'; gearbox?: 'AUTO' | 'MANUAL' };

const STEPS: { key: keyof Answers; question: string; options: { value: string; label: string; hint: string }[] }[] = [
  { key: 'code_status', question: 'Où en êtes-vous avec le code ?', options: [
    { value: 'TO_PASS', label: 'À passer', hint: "Je n'ai pas encore le code" },
    { value: 'OBTAINED', label: 'Obtenu', hint: "J'ai déjà réussi l'examen du code" },
  ] },
  { key: 'level', question: 'Votre expérience de conduite ?', options: [
    { value: 'BEGINNER', label: 'Débutant', hint: "Je n'ai jamais ou presque jamais conduit" },
    { value: 'REFRESH', label: 'Remise à niveau', hint: "J'ai déjà conduit, je veux reprendre confiance" },
  ] },
  { key: 'gearbox', question: 'Quelle boîte de vitesses ?', options: [
    { value: 'AUTO', label: 'Automatique', hint: 'Plus simple à apprendre' },
    { value: 'MANUAL', label: 'Manuelle', hint: 'Permis sans restriction' },
  ] },
];

export default function OfferFinder({ ctaHref }: { ctaHref: (offer: Offer) => string }) {
  const [step, setStep] = useState(0);
  const [answers, setAnswers] = useState<Answers>({});
  const [result, setResult] = useState<{ recommended: Offer | null; alternatives: Offer[] } | null>(null);
  const [busy, setBusy] = useState(false);

  const choose = async (value: string) => {
    const next = { ...answers, [STEPS[step].key]: value } as Answers;
    setAnswers(next);
    if (step < STEPS.length - 1) {
      setStep(step + 1);
      return;
    }
    setBusy(true);
    try {
      const { data } = await api.post('/offers/recommend/', next);
      setResult(data);
    } finally { setBusy(false); }
  };

  const reset = () => { setStep(0); setAnswers({}); setResult(null); };

  if (result) {
    return (
      <div>
        {result.recommended ? (
          <>
            <p className="text-center text-brown-800/70 mb-6">D'après vos réponses, voici la formule qui vous correspond le mieux :</p>
            <div className="max-w-sm mx-auto">
              <OfferCard offer={result.recommended} highlight badge="Recommandée pour vous"
                action={<Link href={ctaHref(result.recommended)} className="btn-primary w-full">Sélectionner cette offre</Link>} />
            </div>
            {result.alternatives.length > 0 && (
              <p className="text-center text-sm text-brown-800/60 mt-4">
                Autres options : {result.alternatives.map((o) => o.name).join(' · ')}
              </p>
            )}
          </>
        ) : (
          <p className="text-center text-brown-800/70">Aucune offre ne correspond pour le moment.</p>
        )}
        <div className="text-center mt-4"><button onClick={reset} className="text-sm text-brown-700 hover:underline">Recommencer</button></div>
      </div>
    );
  }

  const s = STEPS[step];
  return (
    <div className="max-w-xl mx-auto">
      <div className="flex gap-1 mb-6">
        {STEPS.map((_, i) => <div key={i} className={`h-1.5 flex-1 rounded-full ${i <= step ? 'bg-brown-700' : 'bg-cream-300'}`} />)}
      </div>
      <h3 className="text-2xl text-center mb-6">{s.question}</h3>
      <div className="grid sm:grid-cols-2 gap-3">
        {s.options.map((o) => (
          <button key={o.value} onClick={() => choose(o.value)} disabled={busy}
            className="card text-left hover:border-brown-300 hover:shadow-lg transition disabled:opacity-60">
            <div className="font-semibold text-lg">{o.label}</div>
            <div className="text-sm text-brown-800/70">{o.hint}</div>
          </button>
        ))}
      </div>
      {step > 0 && <button onClick={() => setStep(step - 1)} className="mt-4 text-sm text-brown-700 hover:underline">← Retour</button>}
    </div>
  );
}
