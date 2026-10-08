import type { NextApiRequest, NextApiResponse } from 'next';

// Appelé chaque matin par Vercel Cron (voir vercel.json). Relaie vers l'API Django avec le secret partagé.
export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  const secret = process.env.CRON_SECRET;
  if (!secret) return res.status(500).json({ error: 'CRON_SECRET manquant' });
  if (req.headers.authorization !== `Bearer ${secret}`) return res.status(401).json({ error: 'Non autorisé' });

  const api = (process.env.NEXT_PUBLIC_API_URL || '').replace(/\/$/, '');
  const r = await fetch(`${api}/internal/reminders/`, { method: 'POST', headers: { 'X-Cron-Secret': secret } });
  const body = await r.text();
  res.status(r.status).send(body);
}
