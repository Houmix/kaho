import { useCallback, useEffect, useState } from 'react';
import api from '@/lib/api';
import { useRequireAuth } from '@/hooks/useRequireAuth';
import AppShell from '@/components/AppShell';
import { Dossier, DocumentItem, apiError, frDate } from '@/lib/types';

const HELP: Record<string, string> = {
  IDENTITY: 'Carte d’identité, passeport ou titre de séjour en cours de validité (recto-verso).',
  PHOTO: 'Code ePhoto (photo-signature numérique) délivré par un photographe ou une cabine agréée.',
  PROOF_ADDRESS: 'Facture (énergie, téléphone), quittance de loyer ou avis d’imposition de moins de 6 mois.',
  JDC: 'Attestation de participation à la JDC, ou attestation de recensement (16 à 25 ans).',
  ASSR2: 'Attestation scolaire de sécurité routière de niveau 2 (ou ASR) — si vous avez moins de 21 ans.',
  NEPH_CERTIFICATE: 'Attestation d’inscription au permis (NEPH) délivrée par l’ANTS.',
  CONTRACT: 'Contrat de formation signé (remis par l’école).',
};
const statusCls: Record<string, string> = { MISSING: 'bg-cream-200 text-brown-800', PENDING: 'bg-caramel text-brown-900', VERIFIED: 'bg-brown-700 text-cream-50', REJECTED: 'bg-red-100 text-red-700' };
const statusLabel: Record<string, string> = { MISSING: 'À fournir', PENDING: 'En attente de validation', VERIFIED: 'Validé', REJECTED: 'Refusé — à redéposer' };
const ACCEPT = '.pdf,.jpg,.jpeg,.png';

type Pending = { file: File; type: string; state: 'ready' | 'sending' | 'done' | 'error'; error?: string };

export default function StudentDocuments() {
  const ready = useRequireAuth('STUDENT');
  const [dossier, setDossier] = useState<Dossier | null>(null);
  const [docs, setDocs] = useState<DocumentItem[]>([]);
  const [queue, setQueue] = useState<Pending[]>([]);
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState<{ ok: boolean; text: string } | null>(null);

  const load = useCallback(() => api.get('/documents/my_dossier/').then((r) => { setDossier(r.data.dossier); setDocs(r.data.documents); }), []);
  useEffect(() => { if (ready) load(); }, [ready, load]);

  const send = async (type: string, file: File) => {
    const fd = new FormData(); fd.append('document_type', type); fd.append('file', file);
    await api.post('/documents/', fd, { headers: { 'Content-Type': 'multipart/form-data' } });
  };
  const uploadOne = async (type: string, file: File) => {
    setBusy(true); setMsg(null);
    try { await send(type, file); await load(); setMsg({ ok: true, text: 'Pièce déposée, en attente de validation par votre école.' }); }
    catch (err) { setMsg({ ok: false, text: apiError(err, 'Dépôt impossible.') }); }
    finally { setBusy(false); }
  };
  const addFiles = (files: FileList | null) => {
    if (!files || !dossier) return;
    const missing = dossier.items.filter((i) => i.status !== 'VERIFIED').map((i) => i.type);
    const guess = (name: string, idx: number) => {
      const n = name.toLowerCase();
      const hit = dossier.items.find((i) => i.status !== 'VERIFIED' && ((i.type === 'IDENTITY' && /cni|identit|passeport/.test(n)) || (i.type === 'PHOTO' && /photo/.test(n)) || (i.type === 'PROOF_ADDRESS' && /domicile|facture|loyer|edf/.test(n)) || (i.type === 'JDC' && /jdc|recens/.test(n)) || (i.type === 'ASSR2' && /assr|asr/.test(n)) || (i.type === 'NEPH_CERTIFICATE' && /neph|ants/.test(n)) || (i.type === 'CONTRACT' && /contrat/.test(n))));
      return hit?.type ?? missing[idx % Math.max(1, missing.length)] ?? 'IDENTITY';
    };
    setQueue((q) => [...q, ...Array.from(files).map((file, i) => ({ file, type: guess(file.name, q.length + i), state: 'ready' as const }))]);
  };
  const sendQueue = async () => {
    setBusy(true); setMsg(null);
    let okCount = 0;
    for (let i = 0; i < queue.length; i++) {
      const item = queue[i];
      if (item.state === 'done') continue;
      setQueue((q) => q.map((x, j) => (j === i ? { ...x, state: 'sending' } : x)));
      try { await send(item.type, item.file); okCount++; setQueue((q) => q.map((x, j) => (j === i ? { ...x, state: 'done' } : x))); }
      catch (err) { setQueue((q) => q.map((x, j) => (j === i ? { ...x, state: 'error', error: apiError(err, 'Échec') } : x))); }
    }
    await load();
    setMsg({ ok: true, text: `${okCount} pièce(s) déposée(s), en attente de validation.` });
    setQueue((q) => q.filter((x) => x.state !== 'done'));
    setBusy(false);
  };
  const remove = async (doc: DocumentItem) => {
    if (!confirm(`Supprimer « ${doc.file_name} » ? Vous pourrez redéposer un fichier.`)) return;
    try { await api.delete(`/documents/${doc.id}/`); await load(); setMsg({ ok: true, text: 'Fichier supprimé.' }); }
    catch (err) { setMsg({ ok: false, text: apiError(err, 'Suppression impossible.') }); }
  };

  if (!dossier) return <AppShell title="Documents"><p className="text-brown-500">Chargement…</p></AppShell>;
  const required = dossier.items.filter((i) => i.required);

  return (
    <AppShell title="Mes documents">
      <h1 className="text-3xl mb-2">Mes documents</h1>
      <p className="text-brown-800/70 mb-6">{required.length} pièces sont nécessaires, plus l'ASSR 2 et la JDC selon votre âge. Formats : PDF, JPG, PNG — 5 Mo par fichier. Vous pouvez déposer plusieurs fichiers d'un coup.</p>

      <div className={`card mb-6 ${dossier.complete ? 'border-brown-300 bg-brown-50' : ''}`}>
        <div className="flex items-center justify-between gap-3">
          <div>
            <p className="font-semibold">{dossier.complete ? 'Dossier complet ✓' : 'Dossier incomplet'}</p>
            <p className="text-sm text-brown-800/70">{dossier.complete ? 'Toutes vos pièces sont validées.' : `${dossier.missing} à fournir · ${dossier.pending} en attente de validation`}</p>
          </div>
          <div className="flex gap-1">{required.map((i) => <span key={i.type} className={`w-3 h-3 rounded-full ${i.status === 'VERIFIED' ? 'bg-brown-700' : i.status === 'PENDING' ? 'bg-caramel' : 'bg-cream-300'}`} title={i.label} />)}</div>
        </div>
      </div>

      {msg && <div className={`rounded-xl px-4 py-3 mb-6 text-sm ${msg.ok ? 'border border-brown-300 bg-brown-50' : 'border border-red-200 bg-red-50 text-red-700'}`}>{msg.text}</div>}

      <section className="card mb-6 border-dashed border-2 border-brown-300" onDragOver={(e) => e.preventDefault()} onDrop={(e) => { e.preventDefault(); addFiles(e.dataTransfer.files); }}>
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div><h2 className="text-xl">Déposer plusieurs pièces</h2><p className="text-sm text-brown-800/70">Glissez vos fichiers ici ou sélectionnez-les, puis indiquez le type de chaque pièce.</p></div>
          <label className="btn-primary cursor-pointer">Choisir des fichiers<input type="file" multiple accept={ACCEPT} className="hidden" onChange={(e) => { addFiles(e.target.files); e.target.value = ''; }} /></label>
        </div>
        {queue.length > 0 && (
          <ul className="mt-4 divide-y divide-cream-200 text-sm">
            {queue.map((p, i) => (
              <li key={i} className="py-2 flex flex-wrap items-center gap-2">
                <span className="flex-1 min-w-40 truncate">{p.file.name} <span className="text-brown-800/50">({Math.round(p.file.size / 1024)} Ko)</span></span>
                <select value={p.type} disabled={p.state !== 'ready'} onChange={(e) => setQueue((q) => q.map((x, j) => (j === i ? { ...x, type: e.target.value } : x)))} className="input-field !py-1.5 text-sm w-64">
                  {dossier.items.map((it) => <option key={it.type} value={it.type} disabled={it.status === 'VERIFIED'}>{it.label}{it.status === 'VERIFIED' ? ' (déjà validée)' : ''}</option>)}
                </select>
                {p.state === 'ready' && <button onClick={() => setQueue((q) => q.filter((_, j) => j !== i))} className="text-brown-800/50 hover:text-red-600" aria-label="Retirer">✕</button>}
                {p.state === 'sending' && <span className="text-brown-800/60">Envoi…</span>}
                {p.state === 'done' && <span className="text-brown-700">✓ déposé</span>}
                {p.state === 'error' && <span className="text-red-700">{p.error}</span>}
              </li>
            ))}
            <li className="pt-3"><button onClick={sendQueue} disabled={busy || queue.every((p) => p.state !== 'ready')} className="btn-primary disabled:opacity-50">{busy ? 'Envoi en cours…' : `Envoyer ${queue.filter((p) => p.state === 'ready').length} fichier(s)`}</button></li>
          </ul>
        )}
      </section>

      <h2 className="text-xl mb-3">Mes pièces</h2>
      <div className="space-y-3">
        {dossier.items.map((item) => {
          const doc = docs.find((d) => d.document_type === item.type);
          const canUpload = item.status !== 'VERIFIED';
          return (
            <section key={item.type} className="card py-4">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div className="min-w-0">
                  <h3 className="font-semibold">{item.label}{!item.required && <span className="text-xs text-brown-800/50 font-normal"> · facultatif selon l'âge</span>}</h3>
                  <p className="text-sm text-brown-800/70">{HELP[item.type]}</p>
                  {doc && (
                    <p className="mt-2 text-sm text-brown-800/70">
                      <a href={doc.file} target="_blank" rel="noreferrer" className="text-brown-700 hover:underline">{doc.file_name}</a> · déposé le {frDate(doc.uploaded_at, { day: 'numeric', month: 'short', year: 'numeric' })}
                      {doc.reviewed_at && ` · vérifié le ${frDate(doc.reviewed_at, { day: 'numeric', month: 'short' })}`}
                    </p>
                  )}
                  {item.status === 'REJECTED' && item.note && <p className="mt-2 text-sm border-l-2 border-red-300 pl-3 text-red-700">Motif du refus : {item.note}</p>}
                </div>
                <div className="flex flex-col items-end gap-2">
                  <span className={`badge ${statusCls[item.status]}`}>{statusLabel[item.status]}</span>
                  {canUpload && (
                    <div className="flex gap-2 text-sm">
                      <label className={`${doc ? 'btn-secondary' : 'btn-primary'} !py-1.5 cursor-pointer ${busy ? 'opacity-60' : ''}`}>{doc ? 'Remplacer' : 'Déposer'}<input type="file" accept={ACCEPT} className="hidden" disabled={busy} onChange={(e) => { const f = e.target.files?.[0]; if (f) uploadOne(item.type, f); e.target.value = ''; }} /></label>
                      {doc && <button onClick={() => remove(doc)} className="text-red-700 hover:underline">Supprimer</button>}
                    </div>
                  )}
                </div>
              </div>
            </section>
          );
        })}
      </div>
    </AppShell>
  );
}
