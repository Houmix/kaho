import { Html, Head, Main, NextScript } from 'next/document';

export default function Document() {
  return (
    <Html lang="fr">
      <Head>
        <meta charSet="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
        <link rel="manifest" href="/manifest.json" />
        <link rel="apple-touch-icon" href="/icons/icon-192x192.png" />
        <meta name="theme-color" content="#3b82f6" />
        <meta name="description" content="Plateforme d'auto-école pour monitrice indépendante" />
      </Head>
      <body>
        <Main />
        <NextScript />
      </body>
    </Html>
  );
}
