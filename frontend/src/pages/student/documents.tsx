import { useCallback, useEffect, useState } from 'react';
import api from '@/lib/api';
import { useRequireAuth } from '@/hooks/useRequireAuth';
import AppShell from '@/components/AppShell';
import { Dossier, DocumentItem, apiError, frDate } from '@/lib/types';

const HELP: Record<string, string> = {
  IDENTITY: 'Carte d’identité, passeport ou titre de séjour en cours de validité (recto-verso).',
  NEPH_CERTIFICATE: 'Attestation d’inscription au permis (NEPH) délivrée par l’ANTS.',
  CONTRACT: 'Contrat de formation signé (remis par l’école).',
};
const statusCls: Record<string, string> = { MISSING: 'bg-cream-200 text-brown-800', PENDING: 'bg-caramel text-brown-900', VERIFIED: 'bg-brown-700 text-cream-50', REJECTED: 'bg-red-100 text-red-700' };
const statusLabel: Record<string, string> = { MISSING: 'À fournir', PENDING: 'En vérification', VERIFIED: 'Validé', REJECTED: 'Refusé — à redéposer' };

export default function StudentDocuments() {
  const ready = useRequireAuth('STUDENT');
  const [dossier, setDossier] = useState<Dossier | null>(null);
  const [docs, setDocs] = useState<DocumentItem[]>([]);
  const [busy, setBusy] = useState<string | null>(null);
  const [msg, setMsg] = useState<{ ok: boolean; text: string } | null>(null);

  const load = useCallback(() => api.get('/documents/my_dossier/').then((r) => { setDossier(r.data.dossier); setDocs(r.data.documents); }), []);
  useEffect(() => { if (ready) load(); }, [ready, load]);

  const upload = async (type: string, file: File) => {
    setBusy(type); setMsg(null);
    const fd = new FormData();
    fd.append('document_type', type);
    fd.append('file', file);
    try {
      await api.post('/documents/', fd, { headers: { 'Content-Type': 'multipart/form-data' } });
      await load();
      setMsg({ ok: true, text: 'Pièce déposée. Elle sera vérifiée par votre école.' });
    } catch (err) { setMsg({ ok: false, text: apiError(err, 'Dépôt impossible.') }); }
    finally { setBusy(null); }
  };

  if (!dossier) return <AppShell title="Documents"><p className="text-brown-500">Chargement…</p></AppShell>;

  return (
    <AppShell title="Mes documents">
      <h1 className="text-3xl mb-2">Mes documents</h1>
      <p className="text-brown-800/70 mb-6">Trois pièces sont nécessaires pour constituer votre dossier. Formats acceptés : PDF, JPG, PNG — 5 Mo maximum.</p>

      <div className={`card mb-6 ${dossier.complete ? 'border-brown-300 bg-brown-50' : ''}`}>
        <div className="flex items-center justify-between gap-3">
          <div>
            <p className="font-semibold">{dossier.complete ? 'Dossier complet ✓' : 'Dossier incomplet'}</p>
            <p className="text-sm text-brown-800/70">{dossier.complete ? 'Toutes vos pièces sont validées.' : `${dossier.missing} à fournir · ${dossier.pending} en vérification`}</p>
          </div>
          <div className="flex gap-1">{dossier.items.map((i) => <span key={i.type} className={`w-3 h-3 rounded-full ${i.status === 'VERIFIED' ? 'bg-brown-700' : i.status === 'PENDING' ? 'bg-caramel' : 'bg-cream-300'}`} title={i.label} />)}</div>
        </div>
      </div>

      {msg && <div className={`rounded-xl px-4 py-3 mb-6 text-sm ${msg.ok ? 'border border-brown-300 bg-brown-50' : 'border border-red-200 bg-red-50 text-red-700'}`}>{msg.text}</div>}

      <div className="space-y-4">
        {dossier.items.map((item) => {
          const doc = docs.find((d) => d.document_type === item.type);
          const canUpload = item.status !== 'VERIFIED';
          return (
            <section key={item.type} className="card">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <h2 className="text-xl">{item.label}</h2>
                  <p className="text-sm text-brown-800/70">{HELP[item.type]}</p>
                </div>
                <span className={`badge ${statusCls[item.status]}`}>{statusLabel[item.status]}</span>
              </div>
              {item.status === 'REJECTED' && item.note && <p className="mt-3 text-sm border-l-2 border-red-300 pl-3 text-red-700">Motif : {item.note}</p>}
              {doc && (
                <p className="mt-3 text-sm text-brown-800/70">
                  <a href={doc.file} target="_blank" rel="noreferrer" className="text-brown-700 hover:underline">{doc.file_name}</a> · déposé le {frDate(doc.uploaded_at, { day: 'numeric', month: 'short', year: 'numeric' })}
                  {doc.reviewed_at && ` · vérifié le ${frDate(doc.reviewed_at, { day: 'numeric', month: 'short' })}`}
                </p>
              )}
              {canUpload && (
                <label className={`mt-4 inline-flex ${busy === item.type ? 'btn-secondary opacity-60' : doc ? 'btn-secondary' : 'btn-primary'} cursor-pointer`}>
                  {busy === item.type ? 'Envoi…' : doc ? 'Remplacer le fichier' : 'Déposer le fichier'}
                  <input type="file" accept=".pdf,.jpg,.jpeg,.png" className="hidden" disabled={busy !== null} onChange={(e) => { const f = e.target.files?.[0]; if (f) upload(item.type, f); e.target.value = ''; }} />
                </label>
              )}
            </section>
          );
        })}
      </div>
    </AppShell>
  );
}
