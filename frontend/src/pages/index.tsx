import { useEffect, useState } from 'react';
import Link from 'next/link';
import Head from 'next/head';
import { useRouter } from 'next/router';
import api from '@/lib/api';
import { useAuth } from '@/hooks/useAuth';
import Logo from '@/components/Logo';
import { CATEGORY_LABELS, Offer, OfferCategory } from '@/lib/offers';
import { homeFor } from '@/hooks/useRequireAuth';
import OfferCard from '@/components/OfferCard';
import OfferFinder from '@/components/OfferFinder';

const features = [
  { title: 'Réservation simple', text: 'Choisissez un créneau et un point de rendez-vous en quelques secondes.' },
  { title: 'Livret numérique', text: 'Chaque leçon laisse une trace : compétences validées, conditions, remarques.' },
  { title: 'Fonctionne hors-ligne', text: 'Sur un parking sans réseau, tout se synchronise au retour de la connexion.' },
];

export default function Home() {
  const { isAuthenticated, user } = useAuth();
  const router = useRouter();
  const [offers, setOffers] = useState<Offer[]>([]);
  const [category, setCategory] = useState<OfferCategory | null>(null);
  const categories = (Object.keys(CATEGORY_LABELS) as OfferCategory[]).filter((c) => offers.some((o) => o.category === c));
  const visible = offers.filter((o) => !category || o.category === category);

  useEffect(() => {
    api.get('/offers/').then((r) => setOffers(r.data)).catch(() => setOffers([]));
  }, []);

  useEffect(() => {
    if (!isAuthenticated) return;
    router.push(homeFor(user?.role));
  }, [isAuthenticated, user, router]);

  if (isAuthenticated) return null;

  return (
    <>
      <Head><title>Kaho — Auto-école indépendante</title></Head>

      <header className="sticky top-0 z-10 bg-cream-50/90 backdrop-blur border-b border-cream-200">
        <nav className="container flex items-center justify-between py-3">
          <Logo />
          <div className="flex items-center gap-3">
            <Link href="/login" className="text-brown-700 hover:text-brown-900 font-medium px-3 py-2">Connexion</Link>
            <Link href="/signup" className="btn-primary">S’inscrire</Link>
          </div>
        </nav>
      </header>

      <main>
        <section className="container grid md:grid-cols-2 gap-10 items-center py-14 md:py-24">
          <div>
            <p className="text-caramel font-medium tracking-wide uppercase text-sm mb-3">Monitrice indépendante</p>
            <h1 className="text-4xl md:text-5xl leading-tight text-brown-900 mb-5">
              Apprenez à conduire, <span className="text-brown-500">à votre rythme</span>.
            </h1>
            <p className="text-lg text-brown-800/80 mb-8 max-w-prose">
              Des leçons là où vous êtes, un suivi clair de votre progression, et une réservation qui tient dans votre poche.
            </p>
            <div className="flex flex-wrap gap-3">
              <Link href="/signup" className="btn-primary">Commencer</Link>
              <a href="#tarifs" className="btn-outline">Voir les tarifs</a>
            </div>
          </div>
          <img src="/hero.svg" alt="" className="w-full rounded-3xl shadow-warm" />
        </section>

        <section className="container pb-4">
          <div>
            <h2 className="text-3xl text-center mb-10">Pensé pour la route</h2>
            <div className="grid md:grid-cols-3 gap-6">
              {features.map((f) => (
                <div key={f.title} className="card">
                  <h3 className="text-xl mb-2">{f.title}</h3>
                  <p className="text-brown-800/75">{f.text}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section id="simulateur" className="container py-16">
          <h2 className="text-3xl text-center mb-2">Quelle formule pour vous ?</h2>
          <p className="text-center text-brown-800/70 mb-8">Trois questions, et nous vous proposons l'offre adaptée.</p>
          <OfferFinder ctaHref={(o) => `/signup?offer=${o.id}`} />
        </section>

        <section id="tarifs" className="bg-white border-y border-cream-200 py-16">
          <div className="container">
            <h2 className="text-3xl text-center mb-6">Nos offres</h2>
            {categories.length > 1 && (
              <div className="flex flex-wrap justify-center gap-2 mb-8">
                <button onClick={() => setCategory(null)} className={`badge !px-4 !py-2 ${category === null ? 'bg-brown-700 text-cream-50' : 'bg-cream-100 text-brown-800 hover:bg-cream-200'}`}>Toutes</button>
                {categories.map((c) => (
                  <button key={c} onClick={() => setCategory(c)} className={`badge !px-4 !py-2 ${category === c ? 'bg-brown-700 text-cream-50' : 'bg-cream-100 text-brown-800 hover:bg-cream-200'}`}>{CATEGORY_LABELS[c]}</button>
                ))}
              </div>
            )}
            {offers.length === 0 ? (
              <p className="text-center text-brown-800/60">Les offres seront bientôt disponibles.</p>
            ) : (
              <div className="grid md:grid-cols-3 gap-6">
                {visible.map((o) => (
                  <OfferCard key={o.id} offer={o} highlight={o.is_featured}
                    action={<Link href={`/signup?offer=${o.id}`} className={o.is_featured ? 'btn-primary w-full' : 'btn-secondary w-full'}>Choisir</Link>} />
                ))}
              </div>
            )}
          </div>
        </section>
      </main>

      <footer className="border-t border-cream-200 py-8">
        <div className="container flex flex-col md:flex-row items-center justify-between gap-3 text-sm text-brown-800/70">
          <Logo className="h-7" />
          <p>© {new Date().getFullYear()} Kaho — Auto-école indépendante</p>
        </div>
      </footer>
    </>
  );
}
