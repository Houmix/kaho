import Head from 'next/head';
import Link from 'next/link';
import Logo from '@/components/Logo';

export default function ServerError() {
  return (
    <>
      <Head><title>Une erreur est survenue — Kaho</title></Head>
      <div className="min-h-screen flex flex-col">
        <header className="container py-4"><Logo /></header>
        <main className="container flex-1 flex flex-col justify-center py-10 max-w-2xl">
          <p className="text-caramel font-medium tracking-wide uppercase text-sm mb-2">Erreur 500</p>
          <h1 className="text-4xl md:text-5xl mb-3">Quelque chose s'est mal passé.</h1>
          <p className="text-brown-800/70 mb-8">Ce n'est pas de votre fait. Réessayez dans un instant ; si le problème persiste, contactez votre auto-école.</p>
          <div className="flex flex-wrap gap-3">
            <button onClick={() => window.location.reload()} className="btn-primary">Réessayer</button>
            <Link href="/" className="btn-secondary">Accueil</Link>
          </div>
        </main>
      </div>
    </>
  );
}
