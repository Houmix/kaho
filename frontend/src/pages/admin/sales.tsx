import { useCallback, useEffect, useState } from 'react';
import Link from 'next/link';
import api from '@/lib/api';
import { useRequireAuth } from '@/hooks/useRequireAuth';
import AdminShell from '@/components/AdminShell';
import PdfLink from '@/components/PdfLink';
import { Invoice, Paginated, PayrollRow, SalesData, exportCsv } from '@/lib/admin';
import { formatPrice } from '@/lib/offers';
import { frDate, hm } from '@/lib/types';

type Tab = 'overview' | 'invoices' | 'payroll';
const statusCls: Record<Invoice['status'], string> = { ISSUED: 'bg-caramel text-brown-900', PAID: 'bg-brown-700 text-cream-50', CANCELLED: 'bg-cream-200 text-brown-800/60' };
const thisMonth = () => new Date().toISOString().slice(0, 7);

function InvoiceTable({ items }: { items: Invoice[] }) {
  return (
    <div className="card p-0 overflow-x-auto">
      <table className="w-full text-sm">
        <thead className="bg-cream-100 text-brown-800/70"><tr>
          <th className="text-left py-3 px-4 font-medium">N°</th><th className="text-left py-3 px-4 font-medium">Date</th><th className="text-left py-3 px-4 font-medium">Élève</th><th className="text-left py-3 px-4 font-medium">Désignation</th><th className="text-right py-3 px-4 font-medium">HT</th><th className="text-right py-3 px-4 font-medium">TTC</th><th className="text-left py-3 px-4 font-medium">Statut</th><th className="text-left py-3 px-4 font-medium">Échéance</th><th></th>
        </tr></thead>
        <tbody>
          {items.length === 0 ? <tr><td colSpan={9} className="py-10 text-center text-brown-800/60">Aucune facture</td></tr> : items.map((i) => (
            <tr key={i.id} className="border-t border-cream-200 hover:bg-cream-50">
              <td className="py-3 px-4 font-mono text-xs">{i.number}</td>
              <td className="py-3 px-4 whitespace-nowrap">{frDate(i.issued_at, { day: '2-digit', month: '2-digit', year: 'numeric' })}</td>
              <td className="py-3 px-4"><Link href={`/admin/students/${i.student}`} className="text-brown-700 hover:underline">{i.student_name}</Link></td>
              <td className="py-3 px-4">{i.label}</td>
              <td className="py-3 px-4 text-right">{formatPrice(i.amount_ht)}</td>
              <td className="py-3 px-4 text-right font-semibold">{formatPrice(i.amount_ttc)}</td>
              <td className="py-3 px-4"><span className={`badge ${statusCls[i.status]}`}>{i.status_display}</span>{i.is_overdue && <span className="badge bg-red-100 text-red-700 ml-1">en retard</span>}</td>
              <td className="py-3 px-4 whitespace-nowrap">{frDate(i.due_at, { day: '2-digit', month: '2-digit' })}</td>
              <td className="py-3 px-4 text-right whitespace-nowrap"><PdfLink invoiceId={i.id} number="" className="btn-secondary !py-1 text-xs" /></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default function AdminSales() {
  const ready = useRequireAuth('OWNER');
  const [tab, setTab] = useState<Tab>('overview');
  const [sales, setSales] = useState<SalesData | null>(null);
  const [invoices, setInvoices] = useState<Paginated<Invoice> | null>(null);
  const [filter, setFilter] = useState({ status: '', month: '', q: '' });
  const [payMonth, setPayMonth] = useState(thisMonth());
  const [payroll, setPayroll] = useState<{ month: string; rows: PayrollRow[]; total: number; total_hours: number } | null>(null);
  const [openRow, setOpenRow] = useState<number | null>(null);

  useEffect(() => { if (ready) api.get('/admin/sales/').then((r) => setSales(r.data)); }, [ready]);
  const loadInvoices = useCallback(() => api.get('/admin/invoices/', { params: { status: filter.status || undefined, month: filter.month || undefined, q: filter.q || undefined, page_size: 100 } }).then((r) => setInvoices(r.data)), [filter]);
  useEffect(() => { if (ready && tab === 'invoices') { const t = setTimeout(loadInvoices, 200); return () => clearTimeout(t); } }, [ready, tab, loadInvoices]);
  useEffect(() => { if (ready && tab === 'payroll') api.get('/admin/payroll/', { params: { month: payMonth } }).then((r) => setPayroll(r.data)); }, [ready, tab, payMonth]);

  const max = sales ? Math.max(1, ...sales.months.map((m) => m.revenue)) : 1;
  const csvInvoices = () => invoices && exportCsv('factures.csv', ['Numéro', 'Date', 'Élève', 'Email', 'Désignation', 'HT', 'TVA', 'TTC', 'Statut', 'Échéance', 'Payée le'],
    invoices.results.map((i) => [i.number, i.issued_at, i.student_name, i.student_email, i.label, i.amount_ht, i.amount_vat, i.amount_ttc, i.status_display, i.due_at, i.paid_at ? i.paid_at.slice(0, 10) : '']));
  const csvPayroll = () => payroll && exportCsv(`paie-${payroll.month}.csv`, ['Moniteur', 'Email', 'Taux horaire', 'Heures', 'Leçons', 'Absences élèves', 'Montant'],
    payroll.rows.map((r) => [r.name, r.email, r.hourly_rate, r.hours, r.lessons, r.no_shows, r.amount]));

  return (
    <AdminShell title="Ventes & factures" wide>
      <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
        <h1 className="text-3xl">Ventes & factures</h1>
        <div className="flex flex-wrap gap-1">
          {([['overview', 'Chiffre d’affaires'], ['invoices', 'Factures'], ['payroll', 'Paie des moniteurs']] as [Tab, string][]).map(([k, l]) => (
            <button key={k} onClick={() => setTab(k)} className={`badge !px-4 !py-2 ${tab === k ? 'bg-brown-700 text-cream-50' : 'bg-cream-100 text-brown-800'}`}>{l}</button>
          ))}
        </div>
      </div>

      {tab === 'overview' && (!sales ? <p className="text-brown-500">Chargement…</p> : (
        <>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 sm:gap-4 mb-6">
            <div className="card py-4"><p className="text-sm text-brown-800/70">Encaissé cette année</p><p className="text-3xl font-display">{formatPrice(sales.year_revenue)}</p></div>
            <div className="card py-4"><p className="text-sm text-brown-800/70">Ce mois</p><p className="text-3xl font-display">{formatPrice(sales.months[sales.months.length - 1].revenue)}</p><p className="text-xs text-brown-800/60">{sales.months[sales.months.length - 1].sales} vente(s)</p></div>
            <div className={`card py-4 ${sales.unpaid.count ? 'border-caramel bg-brown-50' : ''}`}><p className="text-sm text-brown-800/70">Impayés</p><p className="text-3xl font-display">{formatPrice(sales.unpaid.amount)}</p><p className="text-xs text-brown-800/60">{sales.unpaid.count} facture(s){sales.unpaid.overdue ? ` · ${sales.unpaid.overdue} en retard` : ''}</p></div>
          </div>
          <section className="card mb-6">
            <h2 className="text-xl mb-4">Chiffre d'affaires encaissé — 12 derniers mois</h2>
            <div className="flex items-end gap-2 h-44">
              {sales.months.map((m) => (
                <div key={m.month} className="flex-1 flex flex-col items-center justify-end gap-1 h-full" title={`${m.label} : ${formatPrice(m.revenue)} (${m.sales} vente(s))`}>
                  <span className="text-[10px] text-brown-800/70">{m.revenue ? formatPrice(m.revenue) : ''}</span>
                  <div className="w-full rounded-t-md bg-brown-700" style={{ height: `${Math.max(2, (m.revenue / max) * 100)}%` }} />
                  <span className="text-[10px] text-brown-800/60 capitalize">{m.label.slice(0, 3)}</span>
                </div>
              ))}
            </div>
          </section>
          <section>
            <h2 className="text-xl mb-3">Factures à régler</h2>
            {sales.unpaid.items.length === 0 ? <p className="text-brown-800/60">Aucun impayé 🎉</p> : <InvoiceTable items={sales.unpaid.items} />}
            <p className="text-xs text-brown-800/50 mt-2">Pour encaisser : fiche élève → « Valider le paiement » ; la facture passe en « Payée » automatiquement.</p>
          </section>
        </>
      ))}

      {tab === 'invoices' && (
        <>
          <div className="flex flex-wrap gap-2 items-center mb-4">
            <input value={filter.q} onChange={(e) => setFilter({ ...filter, q: e.target.value })} placeholder="N°, nom, email…" className="input-field sm:w-64 !py-2" />
            <input type="month" value={filter.month} onChange={(e) => setFilter({ ...filter, month: e.target.value })} className="input-field sm:w-44 !py-2" />
            <div className="flex flex-wrap gap-1">{[['', 'Toutes'], ['ISSUED', 'À régler'], ['PAID', 'Payées'], ['CANCELLED', 'Annulées']].map(([k, l]) => <button key={k} onClick={() => setFilter({ ...filter, status: k })} className={`badge !px-3 !py-1.5 ${filter.status === k ? 'bg-brown-700 text-cream-50' : 'bg-cream-100 text-brown-800'}`}>{l}</button>)}</div>
            <button onClick={csvInvoices} className="btn-secondary !py-2 ml-auto" disabled={!invoices?.results.length}>Exporter CSV</button>
          </div>
          {!invoices ? <p className="text-brown-500">Chargement…</p> : <InvoiceTable items={invoices.results} />}
          <p className="text-xs text-brown-800/50 mt-2">Les mentions légales (adresse, SIRET, TVA) se règlent dans les variables COMPANY_* du serveur.</p>
        </>
      )}

      {tab === 'payroll' && (
        <>
          <div className="flex flex-wrap gap-2 items-center mb-4">
            <input type="month" value={payMonth} onChange={(e) => setPayMonth(e.target.value)} className="input-field sm:w-44 !py-2" />
            {payroll && <span className="text-sm text-brown-800/70">{payroll.total_hours} h effectuées · total <strong className="text-brown-900">{formatPrice(payroll.total)}</strong></span>}
            <button onClick={csvPayroll} className="btn-secondary !py-2 ml-auto" disabled={!payroll?.rows.length}>Exporter CSV</button>
          </div>
          {!payroll ? <p className="text-brown-500">Chargement…</p> : (
            <div className="card p-0 overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-cream-100 text-brown-800/70"><tr><th className="text-left py-3 px-4 font-medium">Moniteur</th><th className="text-right py-3 px-4 font-medium">Taux</th><th className="text-right py-3 px-4 font-medium">Leçons</th><th className="text-right py-3 px-4 font-medium">Heures</th><th className="text-right py-3 px-4 font-medium">Absences élèves</th><th className="text-right py-3 px-4 font-medium">Montant</th><th></th></tr></thead>
                <tbody>
                  {payroll.rows.length === 0 ? <tr><td colSpan={7} className="py-10 text-center text-brown-800/60">Aucune leçon ce mois-ci</td></tr> : payroll.rows.map((r) => (
                    <>
                      <tr key={r.id} className="border-t border-cream-200">
                        <td className="py-3 px-4"><Link href={`/admin/instructors/${r.id}`} className="text-brown-700 hover:underline">{r.name}</Link></td>
                        <td className="py-3 px-4 text-right">{r.hourly_rate} €/h</td>
                        <td className="py-3 px-4 text-right">{r.lessons}</td>
                        <td className="py-3 px-4 text-right">{r.hours} h</td>
                        <td className="py-3 px-4 text-right">{r.no_shows}</td>
                        <td className="py-3 px-4 text-right font-semibold">{formatPrice(r.amount)}</td>
                        <td className="py-3 px-4 text-right"><button onClick={() => setOpenRow(openRow === r.id ? null : r.id)} className="text-brown-700 text-xs hover:underline">{openRow === r.id ? 'Masquer' : 'Détail'}</button></td>
                      </tr>
                      {openRow === r.id && (
                        <tr key={`${r.id}-d`} className="bg-cream-50"><td colSpan={7} className="px-4 py-2">
                          {r.details.length === 0 ? <span className="text-xs text-brown-800/60">Aucune leçon.</span> : (
                            <ul className="text-xs grid sm:grid-cols-2 gap-x-6">{r.details.map((d, i) => <li key={i} className="py-0.5">{frDate(d.date, { weekday: 'short', day: 'numeric', month: 'short' })} {hm(d.start_time)} · {d.hours} h · {d.student} · {d.place}</li>)}</ul>
                          )}
                        </td></tr>
                      )}
                    </>
                  ))}
                </tbody>
                {payroll.rows.length > 0 && <tfoot><tr className="border-t-2 border-brown-700 font-semibold"><td className="py-3 px-4">Total</td><td /><td className="py-3 px-4 text-right">{payroll.rows.reduce((s, r) => s + r.lessons, 0)}</td><td className="py-3 px-4 text-right">{payroll.total_hours} h</td><td /><td className="py-3 px-4 text-right">{formatPrice(payroll.total)}</td><td /></tr></tfoot>}
              </table>
            </div>
          )}
          <p className="text-xs text-brown-800/50 mt-2">Seules les leçons avec bilan saisi et élève présent sont comptées. Le taux horaire se règle sur la fiche du moniteur.</p>
        </>
      )}
    </AdminShell>
  );
}
