import { DragEvent, useMemo, useState } from 'react';
import { CalendarData } from '@/lib/admin';
import { Slot, frDate, hm } from '@/lib/types';

export type View = 'day' | 'week' | 'month';
const HOUR_START = 7, HOUR_END = 21, PX_PER_HOUR = 48;

const statusCls: Record<Slot['status'], string> = {
  BOOKED: 'bg-brown-700 text-cream-50 border-brown-800',
  AVAILABLE: 'bg-cream-200 text-brown-800 border-cream-300',
  CANCELLED: 'bg-cream-100 text-brown-800/50 border-cream-200 line-through',
  CANCELLED_LATE: 'bg-caramel/40 text-brown-900 border-caramel',
  NO_SHOW: 'bg-red-100 text-red-700 border-red-200',
};

// Date locale (pas d'UTC : lundi 00:00 à Paris serait sinon dimanche 22:00)
export function iso(d: Date) { return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`; }
export function addDays(d: Date, n: number) { const x = new Date(d); x.setDate(x.getDate() + n); return x; }
export function startOfWeek(d: Date) { const x = new Date(d); x.setDate(x.getDate() - ((x.getDay() + 6) % 7)); x.setHours(0, 0, 0, 0); return x; }
function minutes(t: string) { const [h, m] = t.split(':').map(Number); return h * 60 + m; }
function toTime(mins: number) { return `${String(Math.floor(mins / 60)).padStart(2, '0')}:${String(mins % 60).padStart(2, '0')}`; }

interface Props {
  view: View;
  anchor: Date;
  data: CalendarData;
  onMove: (slot: Slot, target: { date: string; start_time: string; instructor?: number }) => void;
  onSelect: (slot: Slot) => void;
  onPickDay: (d: Date) => void;
}

function SlotChip({ s, style, onSelect, compact }: { s: Slot; style?: React.CSSProperties; onSelect: (s: Slot) => void; compact?: boolean }) {
  const draggable = s.status === 'BOOKED' && !s.is_past;
  return (
    <button
      draggable={draggable}
      onDragStart={(e) => { e.dataTransfer.setData('text/plain', String(s.id)); e.dataTransfer.effectAllowed = 'move'; }}
      onClick={() => onSelect(s)}
      style={style}
      title={`${hm(s.start_time)}–${hm(s.end_time)} · ${s.student_name ?? 'libre'} · ${s.instructor_name} · ${s.meeting_point_name}`}
      className={`text-left rounded-lg border px-1.5 py-1 text-[11px] leading-tight overflow-hidden shadow-sm ${statusCls[s.status]} ${draggable ? 'cursor-grab active:cursor-grabbing' : 'cursor-pointer'}`}>
      <div className="font-semibold truncate">{hm(s.start_time)} {s.student_name ?? 'Libre'}</div>
      {!compact && <div className="truncate opacity-80">{s.instructor_name}</div>}
    </button>
  );
}

function TimeGrid({ columns, slots, unavail, onMove, onSelect, dayOf, instructorOf, availabilityOf }: {
  columns: { key: string; label: string; sub?: string }[];
  slots: Slot[];
  unavail: CalendarData['unavailabilities'];
  onMove: Props['onMove'];
  onSelect: Props['onSelect'];
  dayOf: (key: string) => string;
  instructorOf: (key: string) => number | undefined;
  availabilityOf: (key: string) => { start: number; end: number }[];
}) {
  const [hover, setHover] = useState<{ key: string; mins: number } | null>(null);
  const height = (HOUR_END - HOUR_START) * PX_PER_HOUR;
  const minsFromY = (e: DragEvent<HTMLDivElement>) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const raw = HOUR_START * 60 + ((e.clientY - rect.top) / PX_PER_HOUR) * 60;
    return Math.max(HOUR_START * 60, Math.min(HOUR_END * 60 - 15, Math.round(raw / 15) * 15));
  };
  return (
    <div className="card p-0 overflow-auto">
      <div className="grid" style={{ gridTemplateColumns: `56px repeat(${columns.length}, minmax(130px, 1fr))` }}>
        <div className="sticky top-0 z-10 bg-white border-b border-cream-200" />
        {columns.map((c) => (
          <div key={c.key} className="sticky top-0 z-10 bg-white border-b border-l border-cream-200 px-2 py-2 text-sm">
            <div className="font-semibold truncate">{c.label}</div>
            {c.sub && <div className="text-xs text-brown-800/60 truncate">{c.sub}</div>}
          </div>
        ))}
        <div className="relative" style={{ height }}>
          {Array.from({ length: HOUR_END - HOUR_START }, (_, i) => (
            <div key={i} className="absolute right-1 text-[10px] text-brown-800/50 -translate-y-1/2" style={{ top: i * PX_PER_HOUR }}>{HOUR_START + i}:00</div>
          ))}
        </div>
        {columns.map((c) => {
          const day = dayOf(c.key);
          const colSlots = slots.filter((s) => s.date === day && (instructorOf(c.key) === undefined || s.instructor === instructorOf(c.key)));
          const colUnavail = unavail.filter((u) => (instructorOf(c.key) === undefined || u.instructor === instructorOf(c.key)) && u.start.slice(0, 10) <= day && u.end.slice(0, 10) >= day);
          const avail = availabilityOf(c.key);
          return (
            <div key={c.key} className="relative border-l border-cream-200 bg-cream-50/40" style={{ height }}
              onDragOver={(e) => { e.preventDefault(); setHover({ key: c.key, mins: minsFromY(e) }); }}
              onDragLeave={() => setHover(null)}
              onDrop={(e) => {
                e.preventDefault();
                const id = Number(e.dataTransfer.getData('text/plain'));
                const s = slots.find((x) => x.id === id);
                setHover(null);
                if (s) onMove(s, { date: day, start_time: toTime(minsFromY(e)), instructor: instructorOf(c.key) });
              }}>
              {Array.from({ length: HOUR_END - HOUR_START }, (_, i) => <div key={i} className="absolute inset-x-0 border-t border-cream-200/70" style={{ top: i * PX_PER_HOUR }} />)}
              {avail.map((a, i) => <div key={i} className="absolute inset-x-0 bg-white" style={{ top: (a.start - HOUR_START * 60) / 60 * PX_PER_HOUR, height: (a.end - a.start) / 60 * PX_PER_HOUR }} />)}
              {colUnavail.map((u) => {
                const s = Math.max(HOUR_START * 60, u.start.slice(0, 10) < day ? HOUR_START * 60 : minutes(u.start.slice(11, 16)));
                const e = Math.min(HOUR_END * 60, u.end.slice(0, 10) > day ? HOUR_END * 60 : minutes(u.end.slice(11, 16)));
                return <div key={u.id} title={`Absence : ${u.reason || '—'}`} className="absolute inset-x-0.5 rounded bg-[repeating-linear-gradient(45deg,#EAE0D2_0_6px,#F5EFE6_6px_12px)] opacity-80 text-[10px] text-brown-800/60 px-1" style={{ top: (s - HOUR_START * 60) / 60 * PX_PER_HOUR, height: Math.max(12, (e - s) / 60 * PX_PER_HOUR) }}>{u.reason || 'Absence'}</div>;
              })}
              {colSlots.map((s) => {
                const top = (minutes(s.start_time) - HOUR_START * 60) / 60 * PX_PER_HOUR;
                const h = (minutes(s.end_time) - minutes(s.start_time)) / 60 * PX_PER_HOUR;
                return <SlotChip key={s.id} s={s} onSelect={onSelect} compact={h < 40} style={{ position: 'absolute', left: 3, right: 3, top, height: Math.max(22, h - 2) }} />;
              })}
              {hover?.key === c.key && <div className="absolute inset-x-1 border-t-2 border-brown-500 pointer-events-none" style={{ top: (hover.mins - HOUR_START * 60) / 60 * PX_PER_HOUR }}><span className="absolute -top-4 left-0 text-[10px] bg-brown-500 text-cream-50 rounded px-1">{toTime(hover.mins)}</span></div>}
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default function Calendar({ view, anchor, data, onMove, onSelect, onPickDay }: Props) {
  const availabilityFor = (instructor: number | undefined, dateStr: string) => {
    const wd = (new Date(dateStr + 'T00:00:00').getDay() + 6) % 7;
    return data.availabilities.filter((a) => a.weekday === wd && (instructor === undefined || a.instructor === instructor)).map((a) => ({ start: minutes(a.start_time), end: minutes(a.end_time) }));
  };

  if (view === 'day') {
    const day = iso(anchor);
    const cols = data.instructors.map((i) => ({ key: String(i.id), label: i.name, sub: i.is_bookable ? undefined : 'non réservable' }));
    return cols.length === 0 ? <p className="text-brown-800/60">Aucun moniteur actif.</p> : (
      <TimeGrid columns={cols} slots={data.slots} unavail={data.unavailabilities} onMove={onMove} onSelect={onSelect}
        dayOf={() => day} instructorOf={(k) => Number(k)} availabilityOf={(k) => availabilityFor(Number(k), day)} />
    );
  }

  if (view === 'week') {
    const start = startOfWeek(anchor);
    const cols = Array.from({ length: 7 }, (_, i) => { const d = addDays(start, i); return { key: iso(d), label: frDate(iso(d), { weekday: 'short', day: 'numeric' }), sub: frDate(iso(d), { month: 'short' }) }; });
    return (
      <TimeGrid columns={cols} slots={data.slots} unavail={data.unavailabilities} onMove={onMove} onSelect={onSelect}
        dayOf={(k) => k} instructorOf={() => undefined} availabilityOf={(k) => availabilityFor(undefined, k)} />
    );
  }

  // month
  const first = new Date(anchor.getFullYear(), anchor.getMonth(), 1);
  const gridStart = startOfWeek(first);
  const cells = Array.from({ length: 42 }, (_, i) => addDays(gridStart, i));
  const byDay = useMemo(() => { const m: Record<string, Slot[]> = {}; data.slots.forEach((s) => { (m[s.date] ||= []).push(s); }); return m; }, [data.slots]);
  const today = iso(new Date());
  return (
    <div className="card p-0 overflow-hidden">
      <div className="grid grid-cols-7 bg-cream-100 text-xs text-brown-800/70">
        {['Lun', 'Mar', 'Mer', 'Jeu', 'Ven', 'Sam', 'Dim'].map((d) => <div key={d} className="px-2 py-2 font-medium">{d}</div>)}
      </div>
      <div className="grid grid-cols-7">
        {cells.map((d) => {
          const k = iso(d);
          const list = (byDay[k] || []).filter((s) => s.status !== 'CANCELLED');
          const inMonth = d.getMonth() === anchor.getMonth();
          return (
            <div key={k} onClick={() => onPickDay(d)} className={`min-h-24 border-t border-l border-cream-200 p-1.5 cursor-pointer hover:bg-cream-50 ${inMonth ? '' : 'bg-cream-50/60 text-brown-800/40'}`}
              onDragOver={(e) => e.preventDefault()}
              onDrop={(e) => { e.preventDefault(); const s = data.slots.find((x) => x.id === Number(e.dataTransfer.getData('text/plain'))); if (s) onMove(s, { date: k, start_time: hm(s.start_time) }); }}>
              <div className={`text-xs mb-1 ${k === today ? 'inline-block bg-brown-700 text-cream-50 rounded-full px-1.5' : ''}`}>{d.getDate()}</div>
              <div className="space-y-0.5">
                {list.slice(0, 3).map((s) => <SlotChip key={s.id} s={s} onSelect={(x) => { onSelect(x); }} compact />)}
                {list.length > 3 && <div className="text-[10px] text-brown-800/60">+{list.length - 3} autres</div>}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
