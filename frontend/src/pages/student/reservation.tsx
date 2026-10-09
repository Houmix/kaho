import { useCallback, useEffect, useState } from 'react';
import api from '@/lib/api';
import { useRequireAuth } from '@/hooks/useRequireAuth';
import AppShell from '@/components/AppShell';
import { FreeWindow, MeetingPoint, Slot, StudentProfile, apiError, frDate, hm } from '@/lib/types';

function isoDaysFromNow(n: number) {
  const d = new Date();
  d.setDate(d.getDate() + n);
  return d.toISOString().slice(0, 10);
}

export default function Reservation() {
  const ready = useRequireAuth('STUDENT');
  const [date, setDate] = useState(isoDaysFromNow(2));
  const [windows, setWindows] = useState<FreeWindow[]>([]);
  const [loadingWindows, setLoadingWindows] = useState(false);
  const [points, setPoints] = useState<MeetingPoint[]>([]);
  const [pointId, setPointId] = useState<number | null>(null);
  const [profile, setProfile] = useState<StudentProfile | null>(null);
  const [mine, setMine] = useState<Slot[]>([]);
  const [selected, setSelected] = useState<FreeWindow | null>(null);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<{ kind: 'ok' | 'err'; text: string } | null>(null);

  const refresh = useCallback(async () => {
    const [p, s] = await Promise.all([api.get('/student-profiles/my_profile/'), api.get('/slots/')]);
    setProfile(p.data);
    const today = isoDaysFromNow(0);
    setMine((s.data.results ?? s.data).filter((x: Slot) => x.status === 'BOOKED' && x.date >= today));
  }, []);

  useEffect(() => {
    if (!ready) return;
    api.get('/meeting-points/').then((r) => {
      setPoints(r.data);
      if (r.data.length) setPointId(r.data[0].id);
    });
    refresh();
  }, [ready, refresh]);

  useEffect(() => {
    if (!ready) return;
    setSelected(null);
    setLoadingWindows(true);
    api.get('/slots/free/', { params: { date } })
      .then((r) => setWindows(r.data))
      .finally(() => setLoadingWindows(false));
  }, [ready, date]);

  const book = async () => {
    if (!selected) return;
    setBusy(true); setMessage(null);
    try {
      await api.post('/slots/book/', {
        instructor: selected.instructor_id, meeting_point: pointId || null,
        date: selected.date, start_time: selected.start_time, end_time: selected.end_time,
      });
      setMessage({ kind: 'ok', text: `Leçon réservée le ${frDate(selected.date)} à ${selected.start_time} avec ${selected.instructor_name}. Un email de confirmation vous a été envoyé.` });
      setSelected(null);
      await refresh();
      const r = await api.get('/slots/free/', { params: { date } });
      setWindows(r.data);
    } catch (err) {
      setMessage({ kind: 'err', text: apiError(err, 'Réservation impossible.') });
    } finally { setBusy(false); }
  };

  const cancel = async (slot: Slot) => {
    if (!confirm(`Annuler la leçon du ${frDate(slot.date)} à ${hm(slot.start_time)} ?`)) return;
    setMessage(null);
    try {
      await api.post(`/slots/${slot.id}/cancel/`);
      setMessage({ kind: 'ok', text: 'Leçon annulée.' });
      await refresh();
    } catch (err) {
      setMessage({ kind: 'err', text: apiError(err, 'Annulation impossible.') });
    }
  };

  const days = Array.from({ length: 14 }, (_, i) => isoDaysFromNow(i + 1));

  return (
    <AppShell title="Réserver une leçon">
      <div className="flex flex-wrap items-end justify-between gap-3 mb-6">
        <h1 className="text-3xl">Réserver une leçon</h1>
        {profile && (
          <p className="text-brown-800/70">
            Réservable : <strong className="text-brown-900">{profile.bookable_hours.toFixed(1)} h</strong>
            <span className="text-sm"> ({profile.remaining_hours.toFixed(1)} h restantes, {profile.reserved_hours.toFixed(1)} h déjà réservées)</span>
          </p>
        )}
      </div>

      {message && (
        <div className={`rounded-xl px-4 py-3 mb-6 text-sm ${message.kind === 'ok' ? 'border border-brown-300 bg-brown-50 text-brown-900' : 'border border-red-200 bg-red-50 text-red-700'}`}>
          {message.text}
        </div>
      )}

      <section className="card mb-6">
        <h2 className="text-xl mb-3">1. Choisissez un jour</h2>
        <div className="flex gap-2 overflow-x-auto pb-2 -mx-1 px-1">
          {days.map((d) => (
            <button key={d} onClick={() => setDate(d)}
              className={`shrink-0 px-3 py-2 rounded-xl text-sm border ${d === date ? 'bg-brown-700 text-cream-50 border-brown-700' : 'bg-white border-cream-300 text-brown-800 hover:border-brown-300'}`}>
              {frDate(d, { weekday: 'short', day: 'numeric', month: 'short' })}
            </button>
          ))}
        </div>
        <input type="date" value={date} min={isoDaysFromNow(1)} onChange={(e) => setDate(e.target.value)} className="input-field mt-3 sm:w-56" />
      </section>

      <section className="card mb-6">
        <h2 className="text-xl mb-3">2. Choisissez un créneau — {frDate(date)}</h2>
        {loadingWindows ? (
          <p className="text-brown-800/60">Recherche des disponibilités…</p>
        ) : windows.length === 0 ? (
          <p className="text-brown-800/60">Aucun créneau disponible ce jour-là. Essayez un autre jour.</p>
        ) : (
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-2">
            {windows.map((w) => {
              const active = selected === w;
              return (
                <button key={`${w.instructor_id}-${w.start_time}`} onClick={() => { setSelected(w); if (w.meeting_point) setPointId(w.meeting_point); }}
                  className={`text-left rounded-xl border px-3 py-2 ${active ? 'bg-brown-700 text-cream-50 border-brown-700' : 'bg-white border-cream-300 hover:border-brown-300'}`}>
                  <div className="font-semibold">{w.start_time} – {w.end_time}</div>
                  <div className={`text-xs ${active ? 'text-cream-200' : 'text-brown-800/60'}`}>{w.instructor_name}{w.meeting_point_name && ` · ${w.meeting_point_name}`}</div>
                </button>
              );
            })}
          </div>
        )}
      </section>

      <section className="card mb-10">
        <h2 className="text-xl mb-3">3. Point de rendez-vous</h2>
        {selected?.meeting_point_name && <p className="text-sm text-brown-800/70 mb-2">Lieu de prise en charge prévu par {selected.instructor_name} : <strong>{selected.meeting_point_name}</strong>{selected.meeting_point_address && ` — ${selected.meeting_point_address}`}</p>}
        {points.length === 0 ? (
          <p className="text-brown-800/60">Lieu à convenir avec votre moniteur : il vous contactera pour fixer le point de rendez-vous.</p>
        ) : (
          <select value={pointId ?? ''} onChange={(e) => setPointId(e.target.value ? Number(e.target.value) : null)} className="input-field sm:w-96">
            {points.map((p) => <option key={p.id} value={p.id}>{p.name} — {p.address}</option>)}
            <option value="">Lieu à convenir avec le moniteur</option>
          </select>
        )}
        <button onClick={book} disabled={!selected || busy} className="btn-primary mt-4 w-full sm:w-auto disabled:opacity-50">
          {busy ? 'Réservation…' : selected ? `Réserver ${selected.start_time} avec ${selected.instructor_name}` : 'Sélectionnez un créneau'}
        </button>
      </section>

      <h2 className="text-2xl mb-3">Mes prochaines leçons</h2>
      {mine.length === 0 ? (
        <p className="text-brown-800/60">Aucune leçon à venir.</p>
      ) : (
        <ul className="space-y-2">
          {mine.map((s) => (
            <li key={s.id} className="card py-3 flex flex-wrap items-center justify-between gap-2">
              <div>
                <div className="font-semibold">{frDate(s.date)} · {hm(s.start_time)} – {hm(s.end_time)}</div>
                <div className="text-sm text-brown-800/70">{s.instructor_name} · {s.meeting_point_name}</div>
              </div>
              <button onClick={() => cancel(s)} className="btn-outline !py-1.5 text-sm">Annuler</button>
            </li>
          ))}
        </ul>
      )}
      <p className="text-xs text-brown-800/50 mt-3">Annulation gratuite jusqu'à 48 h avant la leçon.</p>
    </AppShell>
  );
}
