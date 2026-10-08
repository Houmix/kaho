import { useState } from 'react';
import Head from 'next/head';
import Link from 'next/link';
import api from '@/lib/api';
import Logo from '@/components/Logo';
import { GEARBOX_LABELS } from '@/lib/admin';
import { apiError } from '@/lib/types';

const FILE_HINT = 'PDF, JPG ou PNG — 5 Mo max';

export default function BecomeInstructor() {
  const [form, setForm] = useState({ first_name: '', last_name: '', email: '', phone: '', gearbox: 'BOTH', message: '' });
  const [files, setFiles] = useState<{ diploma?: File; driving_license?: File; business_doc?: File }>({});
  const [done, setDone] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const f = (k: keyof typeof form) => ({ value: form[k], onChange: (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => setForm({ ...form, [k]: e.target.value }) });

  const submit = async (e: React.FormEvent) => {
    e.preventDefault(); setBusy(true); setError('');
    const fd = new FormData();
    Object.entries(form).forEach(([k, v]) => fd.append(k, v));
    Object.entries(files).forEach(([k, v]) => v && fd.append(k, v));
    try {
      const { data } = await api.post('/instructor-applications/', fd, { headers: { 'Content-Type': 'multipart/form-data' } });
      setDone(data.detail);
    } catch (err) { setError(apiError(err, 'Envoi impossible. Vérifiez les champs et les pièces jointes.')); }
    finally { setBusy(false); }
  };

  const FileInput = ({ k, label, required }: { k: keyof typeof files; label: string; required?: boolean }) => (
    <label className="block">
      <span className="text-sm font-medium text-brown-800">{label}{required ? '' : <span className="text-brown-800/50 font-normal"> (si applicable)</span>}</span>
      <input type="file" required={required} accept=".pdf,.jpg,.jpeg,.png" onChange={(e) => setFiles({ ...files, [k]: e.target.files?.[0] })}
        className="mt-1 block w-full text-sm text-brown-800 file:mr-3 file:btn-secondary file:!py-1.5 file:text-sm file:border-0" />
      <span className="text-xs text-brown-800/50">{FILE_HINT}</span>
    </label>
  );

  return (
    <>
      <Head><title>Devenir moniteur — Kaho</title></Head>
      <header className="container py-4 flex items-center justify-between"><Logo /><Link href="/login" className="text-sm text-brown-700 hover:underline">Déjà moniteur ? Se connecter</Link></header>
      <main className="container max-w-2xl py-8">
        <p className="text-caramel font-medium tracking-wide uppercase text-sm mb-2">Rejoindre l'équipe</p>
        <h1 className="text-4xl mb-3">Devenir moniteur chez Kaho</h1>
        <p className="text-brown-800/70 mb-8">Déposez votre candidature avec vos justificatifs. Après vérification, nous créons votre compte et vous recevez une invitation par email.</p>

        {done ? (
          <div className="card border-brown-300 bg-brown-50">
            <h2 className="text-xl mb-2">Candidature envoyée ✓</h2>
            <p>{done}</p>
            <Link href="/" className="btn-secondary mt-4 inline-flex">Retour à l'accueil</Link>
          </div>
        ) : (
          <form onSubmit={submit} className="space-y-6">
            <section className="card space-y-4">
              <h2 className="text-xl">Vous</h2>
              <div className="grid sm:grid-cols-2 gap-3">
                <label className="block"><span className="text-sm font-medium text-brown-800">Prénom</span><input required className="input-field mt-1" {...f('first_name')} /></label>
                <label className="block"><span className="text-sm font-medium text-brown-800">Nom</span><input required className="input-field mt-1" {...f('last_name')} /></label>
                <label className="block"><span className="text-sm font-medium text-brown-800">Email</span><input required type="email" className="input-field mt-1" {...f('email')} /></label>
                <label className="block"><span className="text-sm font-medium text-brown-800">Téléphone</span><input type="tel" className="input-field mt-1" {...f('phone')} /></label>
                <label className="block sm:col-span-2"><span className="text-sm font-medium text-brown-800">Boîte de vitesses enseignée</span><select className="input-field mt-1" {...f('gearbox')}>{Object.entries(GEARBOX_LABELS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}</select></label>
              </div>
              <label className="block"><span className="text-sm font-medium text-brown-800">Quelques mots sur vous <span className="text-brown-800/50 font-normal">(expérience, disponibilités, zone)</span></span><textarea rows={4} className="input-field mt-1" {...f('message')} /></label>
            </section>

            <section className="card space-y-4">
              <h2 className="text-xl">Justificatifs</h2>
              <FileInput k="diploma" label="Diplôme ECSR / BEPECASER ou autorisation d'enseigner" required />
              <FileInput k="driving_license" label="Permis de conduire" required />
              <FileInput k="business_doc" label="Kbis / attestation auto-entrepreneur" />
            </section>

            {error && <div className="rounded-xl border border-red-200 bg-red-50 text-red-700 px-4 py-3 text-sm">{error}</div>}
            <button disabled={busy} className="btn-primary w-full sm:w-auto disabled:opacity-60">{busy ? 'Envoi…' : 'Envoyer ma candidature'}</button>
            <p className="text-xs text-brown-800/50">Vos documents sont stockés de manière privée et ne servent qu'à l'examen de votre candidature.</p>
          </form>
        )}
      </main>
    </>
  );
}
