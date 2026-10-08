import Markdown from './Markdown';
import { Answer, CorrectionItem, KIND_LABEL, PublicQuestion } from '@/lib/lms';

interface Props {
  index: number;
  q: PublicQuestion;
  value: Answer | undefined;
  onChange: (a: Answer) => void;
  correction?: CorrectionItem;
  disabled?: boolean;
}

export default function QuestionCard({ index, q, value, onChange, correction, disabled }: Props) {
  const multi = q.kind === 'MULTI';
  const selected = Array.isArray(value) ? value : [];
  const toggle = (id: number) => {
    if (disabled) return;
    onChange(multi ? (selected.includes(id) ? selected.filter((x) => x !== id) : [...selected, id]) : [id]);
  };
  const correctIds = correction && Array.isArray(correction.correct_answer) ? correction.correct_answer : [];

  return (
    <section className={`card ${correction ? (correction.correct ? 'border-brown-500' : 'border-red-300') : ''}`}>
      <div className="flex items-start justify-between gap-3 mb-2">
        <span className="text-xs uppercase tracking-wide text-caramel font-medium">Question {index + 1} · {KIND_LABEL[q.kind]}{q.topic ? ` · ${q.topic}` : ''}</span>
        {correction && <span className={`badge shrink-0 ${correction.correct ? 'bg-brown-700 text-cream-50' : 'bg-red-100 text-red-700'}`}>{correction.correct ? 'Correct' : 'Incorrect'}</span>}
      </div>
      <Markdown className="prose-compact mb-4">{q.text_md}</Markdown>

      {q.kind === 'SHORT' || q.kind === 'CODE' ? (
        <>
          {q.kind === 'CODE' ? (
            <textarea value={typeof value === 'string' ? value : ''} onChange={(e) => onChange(e.target.value)} disabled={disabled} rows={4} spellCheck={false}
              className="input-field font-mono text-sm bg-brown-900 text-cream-100 placeholder:text-cream-100/40" placeholder="// votre code" />
          ) : (
            <input value={typeof value === 'string' ? value : ''} onChange={(e) => onChange(e.target.value)} disabled={disabled} className="input-field" placeholder="Votre réponse" />
          )}
          {correction && !correction.correct && <p className="mt-2 text-sm">Réponse attendue : <code className="bg-cream-200 px-1.5 py-0.5 rounded">{String(correction.correct_answer)}</code></p>}
        </>
      ) : (
        <div className="space-y-2">
          {q.choices.map((c) => {
            const on = selected.includes(c.id);
            const isGood = correctIds.includes(c.id);
            let cls = 'border-cream-300 bg-white hover:border-brown-300';
            if (correction) cls = isGood ? 'border-brown-700 bg-brown-50' : on ? 'border-red-300 bg-red-50' : 'border-cream-200 opacity-70';
            else if (on) cls = 'border-brown-700 bg-brown-50';
            return (
              <button key={c.id} type="button" onClick={() => toggle(c.id)} disabled={disabled} aria-pressed={on}
                className={`w-full text-left flex items-center gap-3 rounded-xl border px-3 py-2.5 text-sm transition-colors ${cls}`}>
                <span className={`w-5 h-5 shrink-0 ${multi ? 'rounded' : 'rounded-full'} border flex items-center justify-center ${on ? 'bg-brown-700 border-brown-700 text-cream-50' : 'border-brown-300'}`}>{on ? '✓' : ''}</span>
                <span>{c.text}</span>
                {correction && isGood && <span className="ml-auto text-xs text-brown-700">bonne réponse</span>}
              </button>
            );
          })}
        </div>
      )}

      {correction?.explanation_md && (
        <div className="mt-4 border-l-2 border-caramel pl-3 text-sm text-brown-800/90"><Markdown className="prose-compact">{correction.explanation_md}</Markdown></div>
      )}
    </section>
  );
}
