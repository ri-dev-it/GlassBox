import { BarChart3, Brain, CircleHelp, ClipboardCheck, FilePlus2, FileText, History, Home, LogOut, Settings, ShieldAlert, X } from 'lucide-react';
import { NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';

const navigation = [
  { group: 'Main', links: [{ to: '/', label: 'Dashboard', icon: Home }, { to: '/apply', label: 'New Application', icon: FilePlus2 }, { to: '/status', label: 'Application Status', icon: ClipboardCheck }, { to: '/history', label: 'Application History', icon: History }, { to: '/insights', label: 'AI Insights', icon: Brain }] },
  { group: 'Analytics', links: [{ to: '/analytics', label: 'Credit Analytics', icon: BarChart3 }, { to: '/risk-analysis', label: 'Risk Analysis', icon: ShieldAlert }, { to: '/reports', label: 'Reports', icon: FileText }] },
  { group: 'System', links: [{ to: '/settings', label: 'Settings', icon: Settings }, { to: '/about', label: 'Help & About', icon: CircleHelp }] },
];

export default function AppSidebar({ open, onClose }: { open: boolean; onClose: () => void }) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  if (!user) return null;
  return <>
    <div onClick={onClose} className={`fixed inset-0 z-30 bg-slate-950/40 lg:hidden ${open ? 'block' : 'hidden'}`} />
    <aside className={`fixed inset-y-0 left-0 z-40 flex w-72 -translate-x-full flex-col bg-[#081a35] px-4 py-5 text-slate-200 transition-transform lg:translate-x-0 ${open ? 'translate-x-0' : ''}`}>
      <button onClick={onClose} aria-label="Close navigation" className="absolute right-4 top-5 lg:hidden"><X size={20} /></button>
      <NavLink to="/" className="px-3"><p className="text-xl font-bold tracking-tight text-white">LOAN<span className="text-sky-400">AI</span></p><p className="mt-1 text-xs text-slate-400">Explainable Credit</p></NavLink>
      <nav className="mt-9 flex-1 space-y-6 overflow-y-auto">
        {navigation.map(({ group, links }) => <section key={group}><p className="px-3 pb-2 text-[11px] font-semibold uppercase tracking-widest text-slate-500">{group}</p><div className="space-y-1">{links.map(({ to, label, icon: Icon }) => <NavLink end={to === '/'} onClick={onClose} key={to} to={to} className={({ isActive }) => `flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm transition ${isActive ? 'bg-sky-500/15 text-white shadow-sm ring-1 ring-sky-400/30' : 'hover:bg-white/5 hover:text-white'}`}><Icon size={18} />{label}</NavLink>)}</div></section>)}
      </nav>
      <div className="border-t border-white/10 pt-4"><NavLink to="/settings" className="flex items-center gap-3 rounded-lg px-3 py-2 hover:bg-white/5"><div className="flex h-8 w-8 items-center justify-center rounded-full bg-sky-500 font-semibold text-white">{user.full_name.charAt(0).toUpperCase()}</div><div className="min-w-0"><p className="truncate text-sm font-medium text-white">{user.full_name}</p><p className="text-xs capitalize text-slate-400">{user.role.replace('_', ' ')}</p></div></NavLink><button onClick={() => { logout(); navigate('/login'); }} className="mt-3 flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm text-slate-300 hover:bg-red-500/10 hover:text-red-300"><LogOut size={18} />Logout</button></div>
    </aside>
  </>;
}
