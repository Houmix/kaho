import { useCallback, useEffect, useState } from 'react';
import api from '@/lib/api';
import { useAuth } from '@/hooks/useAuth';
import { useRequireAuth } from '@/hooks/useRequireAuth';
import AdminShell, { ROLE_LABELS } from '@/components/AdminShell';
import { TeamMember } from '@/lib/admin';
import { apiError, frDate } from '@/lib/types';

const ROLES: { key: TeamMember['role']; label: string; hint: string }[] = [
  { key: 'OWNER', label: 'Gérant (super admin)', hint: 'Accès total : trésorerie, paie, exports, gestion des comptes admin, paramètres avancés.' },
  { key: 'ADMIN', label: "Gestionnaire d'exploitation", hint: 'Élèves, moniteurs, planning, documents, inscriptions, encaissements par élève. Pas de vue trésorerie globale ni de paie.' },
  { key: 'SUPERVISOR', label: 'Superviseur / bénévole', hint: 'Mêmes écrans que le gestionnaire (suivi quotidien).' },
];

export default function AdminTeam() {
  const ready = useRequireAuth('OWNER');
  const { user } = useAuth();
  const [team, setTeam] = useState<TeamMember[] | null>(null);
  const [form, setForm] = useState({ first_name: '', last_name: '', email: '', role: 'ADMIN' as TeamMember['role'] });
  const [msg, setMsg] = useState<{ ok: boolean; text: string } | null>(null);
  const [busy, setBusy] = useState(false);

  const load = useCallback(() => api.get('/admin/team/').then((r) => setTeam(r.data)), []);
  useEffect(() => { if (ready) load(); }, [ready, load]);

  const act = async (fn: () => Promise<unknown>, okText: string) => {
    setMsg(null);
    try { await fn(); await load(); setMsg({ ok: true, text: okText }); }
    catch (err) { setMsg({ ok: false, text: apiError(err, 'Action impossible.') }); }
  };
  const invite = async (e: React.FormEvent) => {
    e.preventDefault(); setBusy(true);
    await act(() => api.post('/admin/team/', form), `Invitation envoyée à ${form.email}.`);
    setForm({ first_name: '', last_name: '', email: '', role: 'ADMIN' });
    setBusy(false);
  };

  return (
    <AdminShell title="Équipe admin">
      <h1 className="text-3xl mb-2">Équipe administrative</h1>
      <p className="text-brown-800/70 mb-6">Plusieurs comptes peuvent gérer l'école. Le gérant garde seul la main sur la trésorerie, la paie et les comptes.</p>
      {msg && <div className={`rounded-xl px-4 py-3 mb-6 text-sm ${msg.ok ? 'border border-brown-300 bg-brown-50' : 'border border-red-200 bg-red-50 text-red-700'}`}>{msg.text}</div>}

      <div className="grid lg:grid-cols-[1fr_360px] gap-6">
        <section className="card p-0 overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-cream-100 text-brown-800/70"><tr><th className="text-left py-3 px-4 font-medium">Compte</th><th className="text-left py-3 px-4 font-medium">Rôle</th><th className="text-left py-3 px-4 font-medium">Statut</th><th className="text-left py-3 px-4 font-medium">Dernière connexion</th><th></th></tr></thead>
            <tbody>
              {!team ? <tr><td colSpan={5} className="py-8 text-center text-brown-500">Chargement…</td></tr> : team.map((m) => {
                const self = m.id === user?.id;
                return (
                  <tr key={m.id} className={`border-t border-cream-200 ${!m.is_active ? 'opacity-60' : ''}`}>
                    <td className="py-3 px-4"><div className="font-medium">{m.full_name}{self && <span className="text-xs text-brown-800/50"> (vous)</span>}</div><div className="text-brown-800/60">{m.email}</div></td>
                    <td className="py-3 px-4">
                      <select value={m.role} disabled={self} onChange={(e) => act(() => api.patch(`/admin/team/${m.id}/`, { role: e.target.value }), 'Rôle modifié.')} className="input-field !py-1.5 text-sm">
                        {ROLES.map((r) => <option key={r.key} value={r.key}>{r.label}</option>)}
                      </select>
                    </td>
                    <td className="py-3 px-4">{!m.is_active ? <span className="badge bg-red-100 text-red-700">désactivé</span> : !m.has_password ? <span className="badge bg-caramel text-brown-900">invitation en attente</span> : <span className="badge bg-brown-700 text-cream-50">actif</span>}</td>
                    <td className="py-3 px-4 text-brown-800/70">{m.last_login ? frDate(m.last_login, { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' }) : '—'}</td>
                    <td className="py-3 px-4 text-right whitespace-nowrap space-x-3 text-xs">
                      {!m.has_password && m.is_active && <button onClick={() => act(() => api.post(`/admin/team/${m.id}/resend_invite/`), 'Invitation renvoyée.')} className="text-brown-700 hover:underline">Renvoyer l'invitation</button>}
                      {!self && (m.is_active
                        ? <button onClick={() => confirm(`Désactiver le compte de ${m.full_name} ?`) && act(() => api.patch(`/admin/team/${m.id}/`, { is_active: false }), 'Compte désactivé.')} className="text-red-700 hover:underline">Désactiver</button>
                        : <button onClick={() => act(() => api.patch(`/admin/team/${m.id}/`, { is_active: true }), 'Compte réactivé.')} className="text-brown-700 hover:underline">Réactiver</button>)}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </section>

        <div className="space-y-6">
          <form onSubmit={invite} className="card space-y-3">
            <h2 className="text-xl">Inviter un compte</h2>
            <p className="text-sm text-brown-800/60">Un email lui permet de créer son mot de passe (lien valable 72 h).</p>
            <div className="grid grid-cols-2 gap-2">
              <input required placeholder="Prénom" value={form.first_name} onChange={(e) => setForm({ ...form, first_name: e.target.value })} className="input-field" />
              <input required placeholder="Nom" value={form.last_name} onChange={(e) => setForm({ ...form, last_name: e.target.value })} className="input-field" />
            </div>
            <input required type="email" placeholder="Email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} className="input-field" />
            <select value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value as TeamMember['role'] })} className="input-field">{ROLES.map((r) => <option key={r.key} value={r.key}>{r.label}</option>)}</select>
            <button disabled={busy} className="btn-primary w-full">{busy ? 'Envoi…' : 'Créer et inviter'}</button>
          </form>
          <section className="card">
            <h2 className="text-xl mb-3">Grille des permissions</h2>
            <ul className="space-y-3 text-sm">{ROLES.map((r) => <li key={r.key}><strong>{r.label}</strong><p className="text-brown-800/70">{r.hint}</p></li>)}</ul>
            <p className="text-xs text-brown-800/50 mt-4">Chaque action d'un compte est tracée dans l'historique d'activité (auteur, date, détail). Votre rôle actuel : {ROLE_LABELS[user?.role ?? '']}.</p>
          </section>
        </div>
      </div>
    </AdminShell>
  );
}
