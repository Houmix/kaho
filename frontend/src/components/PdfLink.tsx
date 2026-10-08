import { useState } from 'react';
import api from '@/lib/api';

// Le PDF est servi par l'API avec le jeton JWT : on le récupère en blob puis on l'ouvre.
export default function PdfLink({ invoiceId, number, className = 'text-brown-700 hover:underline' }: { invoiceId: number; number: string; className?: string }) {
  const [busy, setBusy] = useState(false);
  const open = async () => {
    setBusy(true);
    try {
      const r = await api.get(`/invoices/${invoiceId}/pdf/`, { responseType: 'blob' });
      const url = URL.createObjectURL(r.data);
      const a = document.createElement('a');
      a.href = url;
      a.download = `facture-${number}.pdf`;
      a.target = '_blank';
      a.click();
      setTimeout(() => URL.revokeObjectURL(url), 10000);
    } finally { setBusy(false); }
  };
  return <button onClick={open} disabled={busy} className={className}>{busy ? '…' : `PDF ${number}`}</button>;
}
