import React from 'react';
import {
  LayoutDashboard,
  Mic2,
  Users,
  CalendarDays,
  CalendarCheck2,
  PhoneForwarded,
  FileText,
  Sliders,
  ChevronRight
} from 'lucide-react';

export function Sidebar({ currentTab, setCurrentTab }) {
  const navItems = [
    { id: 'overview', label: 'Overview', icon: LayoutDashboard },
    { id: 'voice', label: 'Voice Assistant', icon: Mic2, badge: 'Live' },
    { id: 'doctors', label: 'Doctors', icon: Users },
    { id: 'availability', label: 'Availability', icon: CalendarDays },
    { id: 'appointments', label: 'Appointments', icon: CalendarCheck2 },
    { id: 'calls', label: 'Call History', icon: PhoneForwarded },
    { id: 'logs', label: 'Activity Logs', icon: FileText },
    { id: 'settings', label: 'Settings', icon: Sliders }
  ];

  return (
    <aside className="w-64 border-r border-slate-800/80 bg-slate-950/60 p-4 flex flex-col justify-between shrink-0 hidden md:flex">
      <div className="space-y-6">
        <div>
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-500 px-3">
            Navigation
          </span>
          <nav className="mt-2 space-y-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = currentTab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => setCurrentTab(item.id)}
                  className={`w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl text-sm font-medium transition-all duration-150 ${
                    isActive
                      ? 'bg-blue-600/15 text-blue-400 border border-blue-500/30 shadow-sm'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/60'
                  }`}
                >
                  <div className="flex items-center space-x-3">
                    <Icon className={`w-4 h-4 ${isActive ? 'text-blue-400' : 'text-slate-400'}`} />
                    <span>{item.label}</span>
                  </div>
                  {item.badge && (
                    <span className="px-1.5 py-0.5 text-[10px] font-bold rounded bg-blue-500/20 text-blue-400 uppercase tracking-wider">
                      {item.badge}
                    </span>
                  )}
                  {isActive && !item.badge && (
                    <ChevronRight className="w-3.5 h-3.5 text-blue-400" />
                  )}
                </button>
              );
            })}
          </nav>
        </div>
      </div>

      {/* Clinic Info Footer */}
      <div className="p-3.5 rounded-xl bg-slate-900/70 border border-slate-800/80">
        <div className="flex items-center space-x-2.5">
          <div className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse"></div>
          <span className="text-xs font-semibold text-slate-300">MediVoice Clinic</span>
        </div>
        <p className="text-[11px] text-slate-500 mt-1">
          Asia/Kolkata (IST) Demo System
        </p>
      </div>
    </aside>
  );
}
