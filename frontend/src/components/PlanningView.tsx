import { useCallback, useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import api from '@/lib/api';
import { useAuth } from '@/hooks/useAuth';
import { STAFF_ROLES, useRequireAuth } from '@/hooks/useRequireAuth';
import AppShell from '@/components/AppShell';
import BackLink, { studentHref } from '@/components/BackLink';
import Calendar, { View, addDays, iso, startOfWeek } from '@/components/Calendar';
import { CalendarData } from '@/lib/admin';
import { Slot, apiError, frDate, hm } from '@/lib/types';

const STATUSES: { key: Slot['status']; label: string }[] = [
  { key: 'BOOKED', label: 'Confirmés' }, { key: 'CANCELLED', label: 'Annulés' }, { key: 'CANCELLED_LATE', label: 'Annul. tardives' }, { key: 'NO_SHOW', label: 'Absences' },
];

const statusCls: Record<Slot['status'], string> = {
  BOOKED: 'bg-brown-700 text-cream-50',
  AVAILABLE: 'bg-cream-200 text-brown-800',
  CANCELLED: 'bg-cream-100 text-brown-800/60',
  CANCELLED_LATE: 'bg-caramel/40 text-brown-900',
  NO_SHOW: 'bg-red-100 text-red-700',
};

function rangeFor(view: View, anchor: Date): [string, string] {
  if (view === 'day') return [iso(anchor), iso(anchor)];
  if (view === 'week') { const s = startOfWeek(anchor); return [iso(s), iso(addDays(s, 6))]; }
  const first = new Date(anchor.getFullYear(), anchor.getMonth(), 1);
  const s = startOfWeek(first);
  return [iso(s), iso(addDays(s, 41))];
}

/**
 * Planning unique de l'école : calendrier interactif (jour / semaine / mois) en haut, liste chronologique détaillée en dessous.
 * Même page quel que soit le point d'entrée ; le back-office voit tous les moniteurs, un moniteur voit le sien.
 */
export default function PlanningView() {
  const ready = useRequireAuth(STAFF_ROLES);
  const { user } = useAuth();
  const isBackoffice = user?.role === 'SUPERVISOR' || user?.role === 'ADMIN' || user?.role === 'OWNER';
  const [view, setView] = useState<View>('week');
  const [anchor, setAnchor] = useState(() => new Date());
  const [data, setData] = useState<CalendarData | null>(null);
  const [instructor, setInstructor] = useState('');
  const [point, setPoint] = useState('');
  const [statuses, setStatuses] = useState<Slot['status'][]>(['BOOKED', 'CANCELLED_LATE', 'NO_SHOW']);
  const [selected, setSelected] = useState<Slot | null>(null);
  const [msg, setMsg] = useState<{ ok: boolean; text: string } | null>(null);
  const [reassign, setReassign] = useState('');

  const load = useCallback(() => {
    const [start, end] = rangeFor(view, anchor);
    return api.get('/admin/calendar/', { params: { start, end, instructor: instructor || undefined, meeting_point: point || undefined, status: statuses.join(',') || undefined } }).then((r) => setData(r.data));
  }, [view, anchor, instructor, point, statuses]);
  useEffect(() => { if (ready) load(); }, [ready, load]);

  const run = async (fn: () => Promise<unknown>, okText?: string) => {
    setMsg(null);
    try { await fn(); await load(); setSelected(null); if (okText) setMsg({ ok: true, text: okText }); }
    catch (err) { setMsg({ ok: false, text: apiError(err, 'Action impossible.') }); }
  };

  const move = async (slot: Slot, target: { date: string; start_time: string; instructor?: number }, notify = true) => {
    if (!isBackoffice) return;
    setMsg(null);
    const sameSpot = target.date === slot.date && target.start_time === hm(slot.start_time) && (target.instructor === undefined || target.instructor === slot.instructor);
    if (sameSpot) return;
    try {
      const r = await api.post(`/admin/slots/${slot.id}/move/`, { ...target, notify });
      await load();
      setSelected(r.data);
      setReassign(String(r.data.instructor));
      setMsg({ ok: true, text: `Créneau déplacé au ${frDate(r.data.date, { weekday: 'short', day: 'numeric', month: 'short' })} ${hm(r.data.start_time)} avec ${r.data.instructor_name}.${r.data.warning ? ' ' + r.data.warning : ''}${notify && slot.student ? ' L’élève a été prévenu.' : ''}` });
    } catch (err) { setMsg({ ok: false, text: apiError(err, 'Déplacement impossible.') }); }
  };

  const cancel = (s: Slot) => {
    if (!confirm(`Annuler le créneau du ${frDate(s.date)} à ${hm(s.start_time)} (sans frais pour l'élève) ?`)) return;
    const reason = prompt('Motif de l’annulation (facultatif) :') ?? '';
    run(() => api.post(`/slots/${s.id}/cancel/`, { reason }), 'Créneau annulé.');
  };
  const noShow = (s: Slot) => { if (confirm(`Marquer ${s.student_name} absent le ${frDate(s.date)} à ${hm(s.start_time)} ? L'heure sera décomptée.`)) run(() => api.post(`/slots/${s.id}/no_show/`)); };
  const refund = (s: Slot) => { const note = prompt('Justificatif de la dérogation (ex : certificat médical du …) :'); if (note) run(() => api.post(`/slots/${s.id}/refund/`, { note }), 'Dérogation enregistrée.'); };
  const opensAt = (s: Slot) => new Date(s.assessment_opens_at).toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' });

  const shift = (n: number) => setAnchor((a) => view === 'day' ? addDays(a, n) : view === 'week' ? addDays(a, 7 * n) : new Date(a.getFullYear(), a.getMonth() + n, 1));
  const title = view === 'day' ? frDate(iso(anchor), { weekday: 'long', day: 'numeric', month: 'long' })
    : view === 'week' ? `Semaine du ${frDate(iso(startOfWeek(anchor)), { day: 'numeric', month: 'long' })}`
    : anchor.toLocaleDateString('fr-FR', { month: 'long', year: 'numeric' });

  // Liste : uniquement la période affichée par le calendrier
  const [rangeStart, rangeEnd] = rangeFor(view, anchor);
  const listed = useMemo(() => (data?.slots ?? [])
    .filter((s) => s.date >= rangeStart && s.date <= rangeEnd && (view !== 'month' || s.date.slice(0, 7) === iso(anchor).slice(0, 7)))
    .sort((a, b) => (a.date + a.start_time).localeCompare(b.date + b.start_time)), [data, rangeStart, rangeEnd, view, anchor]);

  return (
    <AppShell title="Planning">
      {isBackoffice && <BackLink fallbackHref="/admin" fallbackLabel="← Retour au tableau de bord" />}
      <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
        <div className="flex items-center gap-2">
          <button onClick={() => shift(-1)} className="btn-secondary !px-3 !py-1.5" aria-label="Précédent">←</button>
          <button onClick={() => setAnchor(new Date())} className="btn-secondary !py-1.5 text-sm">Aujourd'hui</button>
          <button onClick={() => shift(1)} className="btn-secondary !px-3 !py-1.5" aria-label="Suivant">→</button>
          <h1 className="text-2xl ml-2 capitalize">{title}</h1>
        </div>
        <div className="flex gap-1">
          {(['day', 'week', 'month'] as View[]).map((v) => <button key={v} onClick={() => setView(v)} className={`badge !px-4 !py-2 ${view === v ? 'bg-brown-700 text-cream-50' : 'bg-cream-100 text-brown-800'}`}>{v === 'day' ? 'Jour' : v === 'week' ? 'Semaine' : 'Mois'}</button>)}
        </div>
      </div>

      <div className="flex flex-wrap gap-2 items-center mb-4 text-sm">
        {isBackoffice && <select value={instructor} onChange={(e) => setInstructor(e.target.value)} className="input-field sm:w-52 !py-1.5"><option value="">Tous les moniteurs</option>{data?.instructors.map((i) => <option key={i.id} value={i.id}>{i.name}</option>)}</select>}
        <select value={point} onChange={(e) => setPoint(e.target.value)} className="input-field sm:w-52 !py-1.5"><option value="">Tous les lieux</option>{data?.meeting_points.map((m) => <option key={m.id} value={m.id}>{m.name}</option>)}</select>
        {STATUSES.map((s) => (
          <label key={s.key} className="flex items-center gap-1"><input type="checkbox" checked={statuses.includes(s.key)} onChange={(e) => setStatuses(e.target.checked ? [...statuses, s.key] : statuses.filter((x) => x !== s.key))} className="accent-brown-700" />{s.label}</label>
        ))}
        {isBackoffice && <span className="text-brown-800/50 ml-auto hidden md:inline">Glissez un créneau confirmé pour le déplacer{view === 'day' ? ' ou le réattribuer à un autre moniteur' : ''}.</span>}
      </div>

      {msg && <div className={`rounded-xl px-4 py-3 mb-4 text-sm ${msg.ok ? 'border border-brown-300 bg-brown-50' : 'border border-red-200 bg-red-50 text-red-700'}`}>{msg.text}</div>}

      <div className="grid lg:grid-cols-[1fr_300px] gap-4">
        {!data ? <p className="text-brown-500">Chargement…</p> : (
          <Calendar view={view} anchor={anchor} data={data} readOnly={!isBackoffice} onMove={(s, t) => move(s, t)}
            onSelect={(s) => { setSelected(s); setReassign(String(s.instructor)); }} onPickDay={(d) => { setAnchor(d); setView('day'); }} />
        )}
        <aside className="card h-fit lg:sticky lg:top-20">
          {!selected ? <p className="text-sm text-brown-800/60">Cliquez sur un créneau pour le détailler.</p> : (
            <div className="text-sm space-y-2">
              <div className="flex justify-between items-start">
                <h2 className="text-lg font-semibold">{selected.student ? <Link href={studentHref(selected.student)} className="hover:underline">{selected.student_name}</Link> : 'Créneau libre'}</h2>
                <button onClick={() => setSelected(null)} className="text-brown-800/50" aria-label="Fermer">✕</button>
              </div>
              <p>{frDate(selected.date)} · {hm(selected.start_time)}–{hm(selected.end_time)}</p>
              <p className="text-brown-800/70">{selected.instructor_name} · {selected.meeting_point_name}</p>
              <p><span className="badge bg-cream-200 text-brown-800">{selected.status_display}</span>{selected.has_lesson && <span className="badge bg-brown-700 text-cream-50 ml-1">bilan saisi</span>}</p>
              {selected.cancel_reason && <p className="text-brown-800/70">Motif : {selected.cancel_reason}</p>}
              {Number(selected.cancellation_fee) > 0 && <p className="text-brown-800/70">Frais d'annulation : {Number(selected.cancellation_fee).toFixed(2)} €</p>}
              {selected.student && <Link href={studentHref(selected.student)} className="text-brown-700 hover:underline block">Fiche élève →</Link>}
              {selected.status === 'BOOKED' && !selected.is_past && isBackoffice && data && (
                <div className="pt-3 border-t border-cream-200 space-y-2">
                  <label className="block"><span className="text-brown-800/70">Réattribuer à</span>
                    <select value={reassign} onChange={(e) => setReassign(e.target.value)} className="input-field !py-1.5 mt-1">{data.instructors.map((i) => <option key={i.id} value={i.id}>{i.name}</option>)}</select></label>
                  <button disabled={Number(reassign) === selected.instructor} onClick={() => move(selected, { date: selected.date, start_time: hm(selected.start_time), instructor: Number(reassign) })} className="btn-primary !py-1.5 w-full disabled:opacity-40">Réattribuer et prévenir l'élève</button>
                </div>
              )}
              {selected.status === 'BOOKED' && !selected.is_past && (
                <button onClick={() => cancel(selected)} className="btn-outline !py-1.5 w-full text-red-700 border-red-300">Annuler le créneau</button>
              )}
            </div>
          )}
        </aside>
      </div>

      <section className="mt-8">
        <h2 className="text-xl mb-3">Leçons de la période <span className="text-sm text-brown-800/60 font-normal">({listed.length})</span></h2>
        <div className="card p-0 overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-cream-100 text-brown-800/70">
              <tr>
                <th className="text-left py-3 px-4 font-medium">Date</th>
                <th className="text-left py-3 px-4 font-medium">Heure</th>
                <th className="text-left py-3 px-4 font-medium">Lieu de RDV</th>
                {isBackoffice && <th className="text-left py-3 px-4 font-medium">Moniteur</th>}
                <th className="text-left py-3 px-4 font-medium">Élève</th>
                <th className="text-left py-3 px-4 font-medium">Statut</th>
                <th className="text-left py-3 px-4 font-medium">Actions</th>
              </tr>
            </thead>
            <tbody>
              {!data ? <tr><td colSpan={7} className="text-center py-8 text-brown-800/60">Chargement…</td></tr>
                : listed.length === 0 ? <tr><td colSpan={7} className="text-center py-8 text-brown-800/60">Aucun créneau sur cette période</td></tr>
                : listed.map((s) => (
                <tr key={s.id} className={`border-t border-cream-200 hover:bg-cream-50 ${selected?.id === s.id ? 'bg-cream-50' : ''}`}>
                  <td className="py-3 px-4 whitespace-nowrap">{frDate(s.date, { weekday: 'short', day: 'numeric', month: 'short' })}</td>
                  <td className="py-3 px-4 whitespace-nowrap">{hm(s.start_time)} – {hm(s.end_time)}</td>
                  <td className="py-3 px-4">{s.meeting_point_name}</td>
                  {isBackoffice && <td className="py-3 px-4">{s.instructor_name}</td>}
                  <td className="py-3 px-4">
                    {s.student && s.student_name
                      ? <Link href={studentHref(s.student)} className="font-medium text-brown-700 hover:underline" title="Ouvrir la fiche élève">{s.student_name}</Link>
                      : '—'}
                  </td>
                  <td className="py-3 px-4">
                    <span className={`badge ${statusCls[s.status]}`}>{s.status_display}</span>
                    {s.hours_refunded && <span className="badge bg-cream-200 text-brown-800 ml-1" title={s.refund_note}>re-crédité</span>}
                    {Number(s.cancellation_fee) > 0 && <span className="badge bg-caramel/40 text-brown-900 ml-1">frais {Number(s.cancellation_fee).toFixed(0)} €</span>}
                    {s.cancel_reason && <div className="text-xs text-brown-800/60 mt-1 max-w-[16rem] truncate" title={s.cancel_reason}>Motif : {s.cancel_reason}</div>}
                  </td>
                  <td className="py-3 px-4 whitespace-nowrap space-x-2">
                    {s.status === 'BOOKED' && s.is_past && !s.has_lesson && <>
                      {s.can_assess
                        ? <Link href={`/instructor/lesson/${s.id}?from=planning`} className="text-brown-700 font-medium hover:underline">Bilan</Link>
                        : <span className="text-brown-800/50" title="Le bilan s'ouvre dans les 10 dernières minutes de la leçon">🔒 Bilan dès {opensAt(s)}</span>}
                      <button onClick={() => noShow(s)} className="text-red-700 hover:underline">Absent</button>
                    </>}
                    {s.has_lesson && <Link href={`/instructor/lesson/${s.id}?from=planning`} className="text-brown-700 hover:underline">Voir le bilan</Link>}
                    {s.status === 'BOOKED' && !s.is_past && <button onClick={() => cancel(s)} className="text-brown-800/60 hover:underline">Annuler</button>}
                    {isBackoffice && ((s.hours_debited && !s.hours_refunded) || Number(s.cancellation_fee) > 0) && <button onClick={() => refund(s)} className="text-brown-700 hover:underline">Re-créditer</button>}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </AppShell>
  );
}
