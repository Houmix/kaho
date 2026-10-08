import { useCallback, useEffect, useState } from 'react';
import Link from 'next/link';
import api from '@/lib/api';
import { BACKOFFICE, useRequireAuth } from '@/hooks/useRequireAuth';
import AdminShell from '@/components/AdminShell';
import Calendar, { View, addDays, iso, startOfWeek } from '@/components/Calendar';
import { CalendarData } from '@/lib/admin';
import { Slot, apiError, frDate, hm } from '@/lib/types';

const STATUSES: { key: Slot['status']; label: string }[] = [
  { key: 'BOOKED', label: 'Confirmés' }, { key: 'CANCELLED', label: 'Annulés' }, { key: 'CANCELLED_LATE', label: 'Annul. tardives' }, { key: 'NO_SHOW', label: 'Absences' },
];

function rangeFor(view: View, anchor: Date): [string, string] {
  if (view === 'day') return [iso(anchor), iso(anchor)];
  if (view === 'week') { const s = startOfWeek(anchor); return [iso(s), iso(addDays(s, 6))]; }
  const first = new Date(anchor.getFullYear(), anchor.getMonth(), 1);
  const s = startOfWeek(first);
  return [iso(s), iso(addDays(s, 41))];
}

export default function AdminCalendar() {
  const ready = useRequireAuth(BACKOFFICE);
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

  const move = async (slot: Slot, target: { date: string; start_time: string; instructor?: number }, notify = true) => {
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

  const shift = (n: number) => setAnchor((a) => view === 'day' ? addDays(a, n) : view === 'week' ? addDays(a, 7 * n) : new Date(a.getFullYear(), a.getMonth() + n, 1));
  const title = view === 'day' ? frDate(iso(anchor), { weekday: 'long', day: 'numeric', month: 'long' })
    : view === 'week' ? `Semaine du ${frDate(iso(startOfWeek(anchor)), { day: 'numeric', month: 'long' })}`
    : anchor.toLocaleDateString('fr-FR', { month: 'long', year: 'numeric' });

  return (
    <AdminShell title="Planning global" wide>
      <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
        <div className="flex items-center gap-2">
          <button onClick={() => shift(-1)} className="btn-secondary !px-3 !py-1.5">←</button>
          <button onClick={() => setAnchor(new Date())} className="btn-secondary !py-1.5 text-sm">Aujourd'hui</button>
          <button onClick={() => shift(1)} className="btn-secondary !px-3 !py-1.5">→</button>
          <h1 className="text-2xl ml-2 capitalize">{title}</h1>
        </div>
        <div className="flex gap-1">
          {(['day', 'week', 'month'] as View[]).map((v) => <button key={v} onClick={() => setView(v)} className={`badge !px-4 !py-2 ${view === v ? 'bg-brown-700 text-cream-50' : 'bg-cream-100 text-brown-800'}`}>{v === 'day' ? 'Jour' : v === 'week' ? 'Semaine' : 'Mois'}</button>)}
          <Link href="/instructor/planning" className="badge !px-4 !py-2 bg-cream-100 text-brown-800">Liste</Link>
        </div>
      </div>

      <div className="flex flex-wrap gap-2 items-center mb-4 text-sm">
        <select value={instructor} onChange={(e) => setInstructor(e.target.value)} className="input-field sm:w-52 !py-1.5"><option value="">Tous les moniteurs</option>{data?.instructors.map((i) => <option key={i.id} value={i.id}>{i.name}</option>)}</select>
        <select value={point} onChange={(e) => setPoint(e.target.value)} className="input-field sm:w-52 !py-1.5"><option value="">Tous les lieux</option>{data?.meeting_points.map((m) => <option key={m.id} value={m.id}>{m.name}</option>)}</select>
        {STATUSES.map((s) => (
          <label key={s.key} className="flex items-center gap-1"><input type="checkbox" checked={statuses.includes(s.key)} onChange={(e) => setStatuses(e.target.checked ? [...statuses, s.key] : statuses.filter((x) => x !== s.key))} className="accent-brown-700" />{s.label}</label>
        ))}
        <span className="text-brown-800/50 ml-auto hidden md:inline">Glissez un créneau confirmé pour le déplacer{view === 'day' ? ' ou le réattribuer à un autre moniteur' : ''}.</span>
      </div>

      {msg && <div className={`rounded-xl px-4 py-3 mb-4 text-sm ${msg.ok ? 'border border-brown-300 bg-brown-50' : 'border border-red-200 bg-red-50 text-red-700'}`}>{msg.text}</div>}

      <div className="grid lg:grid-cols-[1fr_300px] gap-4">
        {!data ? <p className="text-brown-500">Chargement…</p> : (
          <Calendar view={view} anchor={anchor} data={data} onMove={(s, t) => move(s, t)} onSelect={(s) => { setSelected(s); setReassign(String(s.instructor)); }} onPickDay={(d) => { setAnchor(d); setView('day'); }} />
        )}
        <aside className="card h-fit lg:sticky lg:top-20">
          {!selected ? <p className="text-sm text-brown-800/60">Cliquez sur un créneau pour le détailler.</p> : (
            <div className="text-sm space-y-2">
              <div className="flex justify-between items-start"><h2 className="text-lg font-semibold">{selected.student_name ?? 'Créneau libre'}</h2><button onClick={() => setSelected(null)} className="text-brown-800/50">✕</button></div>
              <p>{frDate(selected.date)} · {hm(selected.start_time)}–{hm(selected.end_time)}</p>
              <p className="text-brown-800/70">{selected.instructor_name} · {selected.meeting_point_name}</p>
              <p><span className="badge bg-cream-200 text-brown-800">{selected.status_display}</span>{selected.has_lesson && <span className="badge bg-brown-700 text-cream-50 ml-1">bilan saisi</span>}</p>
              {selected.student && <Link href={`/admin/students/${selected.student}`} className="text-brown-700 hover:underline">Fiche élève →</Link>}
              {selected.status === 'BOOKED' && !selected.is_past && data && (
                <div className="pt-3 border-t border-cream-200 space-y-2">
                  <label className="block"><span className="text-brown-800/70">Réattribuer à</span>
                    <select value={reassign} onChange={(e) => setReassign(e.target.value)} className="input-field !py-1.5 mt-1">{data.instructors.map((i) => <option key={i.id} value={i.id}>{i.name}</option>)}</select></label>
                  <button disabled={Number(reassign) === selected.instructor} onClick={() => move(selected, { date: selected.date, start_time: hm(selected.start_time), instructor: Number(reassign) })} className="btn-primary !py-1.5 w-full disabled:opacity-40">Réattribuer et prévenir l'élève</button>
                  <button onClick={() => { if (confirm('Annuler ce créneau (sans frais pour l’élève) ?')) api.post(`/slots/${selected.id}/cancel/`).then(() => { setSelected(null); load(); setMsg({ ok: true, text: 'Créneau annulé.' }); }).catch((err) => setMsg({ ok: false, text: apiError(err, 'Annulation impossible.') })); }} className="btn-outline !py-1.5 w-full text-red-700 border-red-300">Annuler le créneau</button>
                </div>
              )}
            </div>
          )}
        </aside>
      </div>
    </AdminShell>
  );
}
