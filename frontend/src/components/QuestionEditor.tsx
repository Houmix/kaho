import { useEffect, useState } from 'react';
import api from '@/lib/api';
import Markdown from './Markdown';
import { AdminChoice, AdminQuestion, KIND_LABEL, QuestionKind, Theme } from '@/lib/lms';
import { apiError } from '@/lib/types';

const EMPTY: Omit<AdminQuestion, 'id' | 'quiz_title' | 'topic_label'> = { quiz: null, kind: 'SINGLE', text_md: '', explanation_md: '', expected_answer: '', points: 1, order: 0, topic: 'L', in_exam_bank: true, is_published: true, choices: [{ text: '', is_correct: true }, { text: '', is_correct: false }] };

interface Props { question?: AdminQuestion | null; quizId?: number | null; themes: Theme[]; onSaved: (q: AdminQuestion) => void; onCancel: () => void }

/** Formulaire question : type, énoncé Markdown, propositions (bonne réponse cochée), explication, thème, banque d'examen. */
export default function QuestionEditor({ question, quizId, themes, onSaved, onCancel }: Props) {
  const [f, setF] = useState<any>(question ? { ...question } : { ...EMPTY, quiz: quizId ?? null, choices: EMPTY.choices.map((c) => ({ ...c })) });
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const [preview, setPreview] = useState(false);
  useEffect(() => { setF(question ? { ...question } : { ...EMPTY, quiz: quizId ?? null, choices: EMPTY.choices.map((c) => ({ ...c })) }); }, [question, quizId]);
  const set = (k: string, v: unknown) => setF((p: any) => ({ ...p, [k]: v }));
  const withChoices = f.kind === 'SINGLE' || f.kind === 'MULTI' || f.kind === 'TRUE_FALSE';
  const setKind = (k: QuestionKind) => {
    const choices: AdminChoice[] = k === 'TRUE_FALSE' ? [{ text: 'Vrai', is_correct: true }, { text: 'Faux', is_correct: false }] : f.choices;
    setF((p: any) => ({ ...p, kind: k, choices }));
  };
  const setChoice = (i: number, patch: Partial<AdminChoice>) => setF((p: any) => ({ ...p, choices: p.choices.map((c: AdminChoice, j: number) => (j === i ? { ...c, ...patch } : (patch.is_correct && f.kind !== 'MULTI' ? { ...c, is_correct: false } : c))) }));
  const save = async (e: React.FormEvent) => {
    e.preventDefault(); setBusy(true); setError('');
    try {
      const body = { ...f, choices: withChoices ? f.choices.filter((c: AdminChoice) => c.text.trim()) : [] };
      const r = question ? await api.patch(`/lms/admin/questions/${question.id}/`, body) : await api.post('/lms/admin/questions/', body);
      onSaved(r.data);
    } catch (err) { setError(apiError(err, 'Enregistrement impossible.')); }
    finally { setBusy(false); }
  };

  return (
    <form onSubmit={save} className="card border-brown-300 space-y-3">
      <div className="flex flex-wrap gap-2 items-end">
        <label className="block"><span className="text-xs text-brown-800/70">Type</span>
          <select value={f.kind} onChange={(e) => setKind(e.target.value as QuestionKind)} className="input-field !py-2">{(Object.keys(KIND_LABEL) as QuestionKind[]).map((k) => <option key={k} value={k}>{KIND_LABEL[k]}</option>)}</select></label>
        <label className="block"><span className="text-xs text-brown-800/70">Thème officiel</span>
          <select value={f.topic} onChange={(e) => set('topic', e.target.value)} className="input-field !py-2">{themes.map((t) => <option key={t.code} value={t.code}>{t.code} — {t.title}</option>)}<option value="">Autre / hors thème</option></select></label>
        <label className="block w-20"><span className="text-xs text-brown-800/70">Points</span><input type="number" min={1} value={f.points} onChange={(e) => set('points', Number(e.target.value))} className="input-field !py-2" /></label>
        <label className="flex items-center gap-1.5 text-sm pb-2"><input type="checkbox" checked={f.in_exam_bank} onChange={(e) => set('in_exam_bank', e.target.checked)} className="accent-brown-700" /> Banque d'examen</label>
        <label className="flex items-center gap-1.5 text-sm pb-2"><input type="checkbox" checked={f.is_published} onChange={(e) => set('is_published', e.target.checked)} className="accent-brown-700" /> Publiée</label>
      </div>
      <label className="block"><span className="text-xs text-brown-800/70">Énoncé (Markdown : image avec ![](url), code avec ```)</span>
        <textarea required rows={3} value={f.text_md} onChange={(e) => set('text_md', e.target.value)} className="input-field font-mono text-sm" /></label>
      {withChoices ? (
        <div className="space-y-1.5">
          <span className="text-xs text-brown-800/70">Propositions — cochez la ou les bonnes réponses{f.kind === 'MULTI' ? ' (plusieurs)' : ''}</span>
          {f.choices.map((c: AdminChoice, i: number) => (
            <div key={i} className="flex items-center gap-2">
              <input type={f.kind === 'MULTI' ? 'checkbox' : 'radio'} name="correct" checked={c.is_correct} onChange={(e) => setChoice(i, { is_correct: f.kind === 'MULTI' ? e.target.checked : true })} className="accent-brown-700" aria-label="Bonne réponse" />
              <input value={c.text} onChange={(e) => setChoice(i, { text: e.target.value })} placeholder={`Proposition ${i + 1}`} className="input-field !py-1.5 text-sm" readOnly={f.kind === 'TRUE_FALSE'} />
              {f.kind !== 'TRUE_FALSE' && f.choices.length > 2 && <button type="button" onClick={() => set('choices', f.choices.filter((_: AdminChoice, j: number) => j !== i))} className="text-brown-800/50 hover:text-red-600" aria-label="Supprimer">✕</button>}
            </div>
          ))}
          {f.kind !== 'TRUE_FALSE' && f.choices.length < 6 && <button type="button" onClick={() => set('choices', [...f.choices, { text: '', is_correct: false }])} className="text-sm text-brown-700 hover:underline">+ Ajouter une proposition</button>}
        </div>
      ) : (
        <label className="block"><span className="text-xs text-brown-800/70">{f.kind === 'CODE' ? 'Code attendu (espaces ignorés)' : 'Réponses acceptées, séparées par | (ex : octogone|un octogone)'}</span>
          <input required value={f.expected_answer} onChange={(e) => set('expected_answer', e.target.value)} className="input-field !py-2 font-mono text-sm" /></label>
      )}
      <label className="block"><span className="text-xs text-brown-800/70">Explication après correction (rappel de la règle, schéma, lien vidéo)</span>
        <textarea rows={2} value={f.explanation_md} onChange={(e) => set('explanation_md', e.target.value)} className="input-field font-mono text-sm" /></label>
      {preview && <div className="rounded-xl border border-cream-200 p-3 bg-white"><Markdown className="prose-compact">{f.text_md || '*Énoncé vide*'}</Markdown>{f.explanation_md && <div className="mt-2 border-l-2 border-caramel pl-3 text-sm"><Markdown className="prose-compact">{f.explanation_md}</Markdown></div>}</div>}
      {error && <p className="text-sm text-red-700">{error}</p>}
      <div className="flex gap-2">
        <button disabled={busy} className="btn-primary !py-2 text-sm">{busy ? 'Enregistrement…' : question ? 'Enregistrer' : 'Ajouter la question'}</button>
        <button type="button" onClick={() => setPreview((v) => !v)} className="btn-secondary !py-2 text-sm">{preview ? 'Masquer l’aperçu' : 'Aperçu'}</button>
        <button type="button" onClick={onCancel} className="text-sm text-brown-700 hover:underline">Annuler</button>
      </div>
    </form>
  );
}
