import Link from 'next/link';

/** Logo officiel (marque + nom). `className` règle la hauteur ; `wordmark={false}` pour la marque seule. */
export default function Logo({ className = 'h-9', wordmark = true, light = false }: { className?: string; wordmark?: boolean; light?: boolean }) {
  return (
    <Link href="/" aria-label="Kaho — accueil" className="inline-flex items-center gap-2">
      <img src="/logo.png" alt="Kaho" className={`${className} w-auto`} />
      {wordmark && <span className={`font-display text-xl leading-none ${light ? 'text-cream-50' : 'text-brown-900'}`}>Kaho</span>}
    </Link>
  );
}
