import Link from 'next/link';

export default function Logo({ className = 'h-9' }: { className?: string }) {
  return (
    <Link href="/" aria-label="Kaho — accueil" className="inline-flex items-center">
      <img src="/logo.svg" alt="Kaho" className={`${className} w-auto`} />
    </Link>
  );
}
