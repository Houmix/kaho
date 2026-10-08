import { useState } from 'react';
import { useRouter } from 'next/router';
import Link from 'next/link';
import Head from 'next/head';
import api from '@/lib/api';
import { useAuth } from '@/hooks/useAuth';
import Logo from '@/components/Logo';

export default function Signup() {
  const router = useRouter();
  const offerId = typeof router.query.offer === 'string' ? router.query.offer : null;
  const { setToken, setUser } = useAuth();
  const [form, setForm] = useState({ first_name: '', last_name: '', email: '', password: '' });
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const update = (k: keyof typeof form) => (e: React.ChangeEvent<HTMLInputElement>) =>
    setForm({ ...form, [k]: e.target.value });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');
    try {
      const { data } = await api.post('/auth/register/', form);
      setToken(data.access, data.refresh);
      setUser(data.user);
      router.push(offerId ? `/student/purchases?offer=${offerId}` : '/student/dashboard');
    } catch (err: any) {
      const d = err.response?.data;
      setError(d?.email?.[0] || d?.password?.[0] || d?.detail || 'Impossible de créer le compte');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <>
      <Head><title>Inscription — Kaho</title></Head>
      <div className="min-h-screen flex items-center justify-center p-6">
        <form onSubmit={handleSubmit} className="w-full max-w-sm space-y-5">
          <div className="mb-6"><Logo /></div>
          <h1 className="text-3xl">Créer mon compte</h1>
          {offerId && <p className="text-sm text-brown-800/70">Vous pourrez choisir votre offre juste après.</p>}

          {error && <div className="rounded-xl border border-red-200 bg-red-50 text-red-700 px-4 py-3 text-sm">{error}</div>}

          <div className="grid grid-cols-2 gap-3">
            <label className="block">
              <span className="text-sm font-medium text-brown-800">Prénom</span>
              <input required value={form.first_name} onChange={update('first_name')} className="input-field mt-1" />
            </label>
            <label className="block">
              <span className="text-sm font-medium text-brown-800">Nom</span>
              <input required value={form.last_name} onChange={update('last_name')} className="input-field mt-1" />
            </label>
          </div>
          <label className="block">
            <span className="text-sm font-medium text-brown-800">Email</span>
            <input type="email" required value={form.email} onChange={update('email')} className="input-field mt-1" placeholder="vous@exemple.fr" />
          </label>
          <label className="block">
            <span className="text-sm font-medium text-brown-800">Mot de passe</span>
            <input type="password" required minLength={8} value={form.password} onChange={update('password')} className="input-field mt-1" placeholder="8 caractères minimum" />
          </label>

          <button type="submit" disabled={isLoading} className="btn-primary w-full disabled:opacity-60">
            {isLoading ? 'Création…' : 'Créer mon compte'}
          </button>

          <p className="text-center text-sm text-brown-800/70">
            Déjà inscrit ? <Link href="/login" className="text-brown-700 font-medium hover:underline">Se connecter</Link>
          </p>
        </form>
      </div>
    </>
  );
}
