import { useState } from 'react';
import { useRouter } from 'next/router';
import Head from 'next/head';
import Link from 'next/link';
import api from '@/lib/api';
import { useAuth } from '@/hooks/useAuth';
import { homeFor } from '@/hooks/useRequireAuth';
import Logo from '@/components/Logo';
import { apiError } from '@/lib/types';

export default function ResetPassword() {
  const router = useRouter();
  const uid = typeof router.query.uid === 'string' ? router.query.uid : null;
  const token = typeof router.query.token === 'string' ? router.query.token : null;
  const { setToken, setUser } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [info, setInfo] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  const request = async (e: React.FormEvent) => {
    e.preventDefault();
    setBusy(true); setError(''); setInfo('');
    try {
      const { data } = await api.post('/auth/password-reset/', { email });
      setInfo(data.detail);
    } catch (err) {
      setError(apiError(err, 'Une erreur est survenue.'));
    } finally { setBusy(false); }
  };

  const confirm = async (e: React.FormEvent) => {
    e.preventDefault();
    setBusy(true); setError('');
    try {
      const { data } = await api.post('/auth/password-reset/confirm/', { uid, token, new_password: password });
      setToken(data.access, data.refresh);
      setUser(data.user);
      router.push(homeFor(data.user.role));
    } catch (err) {
      setError(apiError(err, 'Lien invalide ou expiré.'));
    } finally { setBusy(false); }
  };

  const isConfirm = !!(uid && token);

  return (
    <>
      <Head><title>Mot de passe oublié — Kaho</title></Head>
      <div className="min-h-screen flex items-center justify-center p-6">
        <form onSubmit={isConfirm ? confirm : request} className="w-full max-w-sm space-y-5">
          <div className="mb-6"><Logo /></div>
          <h1 className="text-3xl">{isConfirm ? 'Nouveau mot de passe' : 'Mot de passe oublié'}</h1>

          {info && <div className="rounded-xl border border-brown-300 bg-brown-50 text-brown-900 px-4 py-3 text-sm">{info}</div>}
          {error && <div className="rounded-xl border border-red-200 bg-red-50 text-red-700 px-4 py-3 text-sm">{error}</div>}

          {isConfirm ? (
            <label className="block">
              <span className="text-sm font-medium text-brown-800">Nouveau mot de passe</span>
              <input type="password" required minLength={8} value={password} onChange={(e) => setPassword(e.target.value)} className="input-field mt-1" placeholder="8 caractères minimum" />
            </label>
          ) : (
            <label className="block">
              <span className="text-sm font-medium text-brown-800">Email de votre compte</span>
              <input type="email" required value={email} onChange={(e) => setEmail(e.target.value)} className="input-field mt-1" placeholder="vous@exemple.fr" />
            </label>
          )}

          <button type="submit" disabled={busy} className="btn-primary w-full disabled:opacity-60">
            {busy ? 'Un instant…' : isConfirm ? 'Enregistrer' : 'Envoyer le lien'}
          </button>

          <p className="text-center text-sm text-brown-800/70">
            <Link href="/login" className="text-brown-700 font-medium hover:underline">Retour à la connexion</Link>
          </p>
        </form>
      </div>
    </>
  );
}
