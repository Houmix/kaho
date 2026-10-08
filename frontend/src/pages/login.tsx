import { useState } from 'react';
import { useRouter } from 'next/router';
import Link from 'next/link';
import Head from 'next/head';
import api from '@/lib/api';
import { useAuth } from '@/hooks/useAuth';
import Logo from '@/components/Logo';
import { homeFor } from '@/hooks/useRequireAuth';

export default function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const router = useRouter();
  const { setToken, setUser } = useAuth();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');
    try {
      const { data } = await api.post('/auth/token/', { username: email, password });
      setToken(data.access, data.refresh);
      const me = await api.get('/users/me/');
      setUser(me.data);
      router.push(homeFor(me.data.role));
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Email ou mot de passe incorrect');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <>
      <Head><title>Connexion — Kaho</title></Head>
      <div className="min-h-screen grid md:grid-cols-2">
        <div className="hidden md:flex flex-col justify-between bg-brown-700 text-cream-50 p-10">
          <img src="/logo.svg" alt="Kaho" className="h-9 w-auto brightness-0 invert" />
          <div>
            <h2 className="text-3xl mb-3">Bon retour.</h2>
            <p className="text-cream-200">Vos prochaines leçons et votre livret vous attendent.</p>
          </div>
          <img src="/hero.svg" alt="" className="w-full rounded-2xl opacity-90" />
        </div>

        <div className="flex items-center justify-center p-6">
          <form onSubmit={handleLogin} className="w-full max-w-sm space-y-5">
            <div className="md:hidden mb-6"><Logo /></div>
            <h1 className="text-3xl">Connexion</h1>

            {error && (
              <div className="rounded-xl border border-red-200 bg-red-50 text-red-700 px-4 py-3 text-sm">{error}</div>
            )}

            <label className="block">
              <span className="text-sm font-medium text-brown-800">Email</span>
              <input type="email" required value={email} onChange={(e) => setEmail(e.target.value)} className="input-field mt-1" placeholder="vous@exemple.fr" />
            </label>

            <label className="block">
              <span className="text-sm font-medium text-brown-800">Mot de passe</span>
              <input type="password" required value={password} onChange={(e) => setPassword(e.target.value)} className="input-field mt-1" placeholder="••••••••" />
            </label>

            <button type="submit" disabled={isLoading} className="btn-primary w-full disabled:opacity-60">
              {isLoading ? 'Connexion…' : 'Se connecter'}
            </button>

            <p className="text-center text-sm">
              <Link href="/reset-password" className="text-brown-700 hover:underline">Mot de passe oublié ?</Link>
            </p>

            <p className="text-center text-sm text-brown-800/70">
              Pas encore de compte ?{' '}
              <Link href="/signup" className="text-brown-700 font-medium hover:underline">S’inscrire</Link>
            </p>
          </form>
        </div>
      </div>
    </>
  );
}
