import { useCallback, useEffect, useState } from 'react';
import api from '@/lib/api';
import { useRequireAuth } from '@/hooks/useRequireAuth';
import AppShell from '@/components/AppShell';
import { Availability, Unavailability, WEEKDAYS, apiError, hm } from '@/lib/types';

export default function AvailabilityPage() {
  const ready = useRequireAuth('INSTRUCTOR');
  const [avail, setAvail] = useState<Availability[]>([]);
  const [absences, setAbsences] = useState<Unavailability[]>([]);
  const [slot, setSlot] = useState({ weekday: 0, start_time: '09:00', end_time: '12:00' });
  const [absence, setAbsence] = useState({ start: '', end: '', reason: '' });
  const [error, setError] = useState('');

  const load = useCallback(async () => {
    const [a, u] = await Promise.all([api.get('/availabilities/'), api.get('/unavailabilities/')]);
    setAvail(a.data);
    setAbsences(u.data);
  }, []);

  useEffect(() => { if (ready) load(); }, [ready, load]);

  const addAvail = async (e: React.FormEvent) => {
    e.preventDefault(); setError('');
    try { await api.post('/availabilities/', slot); await load(); }
    catch (err) { setError(apiError(err, 'Impossible d’ajouter ce créneau.')); }
  };
  const addAbsence = async (e: React.FormEvent) => {
    e.preventDefault(); setError('');
    try { await api.post('/unavailabilities/', absence); setAbsence({ start: '', end: '', reason: '' }); await load(); }
    catch (err) { setError(apiError(err, 'Impossible d’ajouter cette absence.')); }
  };
  const remove = async (path: string) => { await api.delete(path); await load(); };

  const byDay = WEEKDAYS.map((name, i) => ({ name, items: avail.filter((a) => a.weekday === i) }));

  return (
    <AppShell title="Disponibilités">
      <h1 className="text-3xl mb-2">Mes disponibilités</h1>
      <p className="text-brown-800/70 mb-6">Les élèves ne peuvent réserver que dans ces plages, hors absences et hors créneaux déjà pris.</p>

      {error && <div className="rounded-xl border border-red-200 bg-red-50 text-red-700 px-4 py-3 mb-6 text-sm">{error}</div>}

      <div className="grid md:grid-cols-2 gap-6">
        <section className="card">
          <h2 className="text-xl mb-3">Horaires récurrents</h2>
          <form onSubmit={addAvail} className="grid grid-cols-3 gap-2 mb-4">
            <select value={slot.weekday} onChange={(e) => setSlot({ ...slot, weekday: Number(e.target.value) })} className="input-field col-span-3 sm:col-span-1">
              {WEEKDAYS.map((d, i) => <option key={i} value={i}>{d}</option>)}
            </select>
            <input type="time" value={slot.start_time} onChange={(e) => setSlot({ ...slot, start_time: e.target.value })} className="input-field" required />
            <input type="time" value={slot.end_time} onChange={(e) => setSlot({ ...slot, end_time: e.target.value })} className="input-field" required />
            <button type="submit" className="btn-primary col-span-3 sm:col-span-1">Ajouter</button>
          </form>
          <ul className="divide-y divide-cream-200">
            {byDay.map(({ name, items }) => (
              <li key={name} className="py-2 flex items-start gap-3">
                <span className="w-24 shrink-0 font-medium">{name}</span>
                <div className="flex flex-wrap gap-2 flex-1">
                  {items.length === 0 ? <span className="text-brown-800/40 text-sm">—</span> : items.map((a) => (
                    <span key={a.id} className="badge bg-cream-200 text-brown-800 inline-flex items-center gap-2">
                      {hm(a.start_time)}–{hm(a.end_time)}
                      <button onClick={() => remove(`/availabilities/${a.id}/`)} aria-label="Supprimer" className="text-brown-800/50 hover:text-red-600">×</button>
                    </span>
                  ))}
                </div>
              </li>
            ))}
          </ul>
        </section>

        <section className="card">
          <h2 className="text-xl mb-1">Absences & congés</h2>
          <p className="text-xs text-brown-800/60 mb-3">Chaque demande bloque immédiatement vos créneaux et est soumise à validation de l'école (vous êtes prévenu par email).</p>
          <form onSubmit={addAbsence} className="space-y-2 mb-4">
            <div className="grid grid-cols-2 gap-2">
              <label className="block"><span className="text-xs text-brown-800/70">Du</span>
                <input type="datetime-local" value={absence.start} onChange={(e) => setAbsence({ ...absence, start: e.target.value })} className="input-field" required /></label>
              <label className="block"><span className="text-xs text-brown-800/70">Au</span>
                <input type="datetime-local" value={absence.end} onChange={(e) => setAbsence({ ...absence, end: e.target.value })} className="input-field" required /></label>
            </div>
            <input placeholder="Motif (facultatif)" value={absence.reason} onChange={(e) => setAbsence({ ...absence, reason: e.target.value })} className="input-field" />
            <button type="submit" className="btn-primary w-full sm:w-auto">Ajouter l'absence</button>
          </form>
          {absences.length === 0 ? <p className="text-brown-800/60 text-sm">Aucune absence enregistrée.</p> : (
            <ul className="divide-y divide-cream-200">
              {absences.map((u) => (
                <li key={u.id} className="py-2 flex items-center justify-between gap-2 text-sm">
                  <span>
                    {new Date(u.start).toLocaleString('fr-FR', { dateStyle: 'short', timeStyle: 'short' })} → {new Date(u.end).toLocaleString('fr-FR', { dateStyle: 'short', timeStyle: 'short' })}
                    {u.reason && <span className="text-brown-800/60"> · {u.reason}</span>}
                    <span className={`badge ml-2 ${u.status === 'APPROVED' ? 'bg-brown-700 text-cream-50' : u.status === 'REJECTED' ? 'bg-red-100 text-red-700' : 'bg-caramel text-brown-900'}`}>{u.status_display}</span>
                    {u.status === 'REJECTED' && u.review_note && <span className="text-red-700 text-xs"> {u.review_note}</span>}
                  </span>
                  <button onClick={() => remove(`/unavailabilities/${u.id}/`)} className="text-brown-800/50 hover:text-red-600">Supprimer</button>
                </li>
              ))}
            </ul>
          )}
        </section>
      </div>
    </AppShell>
  );
}
