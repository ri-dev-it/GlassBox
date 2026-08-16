import { Outlet } from 'react-router-dom';
import { Bell, Menu } from 'lucide-react';
import { useState } from 'react';
import { useAuth } from '../hooks/useAuth';
import AppSidebar from '../components/common/AppSidebar';

export default function MainLayout() {
  const { user } = useAuth();
  const [open, setOpen] = useState(false);
  return (
    <div className="min-h-screen bg-[#f5f7fb]">
      <AppSidebar open={open} onClose={() => setOpen(false)} />
      <main className={user ? 'lg:pl-72' : ''}>
        {user && <header className="flex h-16 items-center justify-between border-b border-slate-200 bg-white px-4 sm:px-7"><button onClick={() => setOpen(true)} className="rounded-md p-2 text-slate-600 hover:bg-slate-100 lg:hidden" aria-label="Open navigation"><Menu size={20} /></button><div className="hidden sm:block"><p className="text-sm font-medium text-slate-800">Indian Explainable AI Loan Credit System</p><p className="text-xs text-slate-500">{new Intl.DateTimeFormat('en-IN', { dateStyle: 'full' }).format(new Date())}</p></div><button aria-label="Notifications" className="relative rounded-full p-2 text-slate-600 hover:bg-slate-100"><Bell size={20} /><span className="absolute right-2 top-2 h-2 w-2 rounded-full bg-sky-500" /></button></header>}
      <div className="mx-auto max-w-7xl px-4 py-6 sm:px-7 sm:py-8">
        <Outlet />
      </div></main>
    </div>
  );
}
