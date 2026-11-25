import React from 'react';
import {
  Users,
  CalendarDays,
  CalendarCheck2,
  PhoneCall,
  Activity,
  ArrowUpRight,
  Sparkles,
  CheckCircle2,
  Clock
} from 'lucide-react';

export function OverviewTab({ stats, recentAppointments = [], onOpenCall, onSelectTab }) {
  const statCards = [
    {
      title: 'Total Doctors',
      value: stats?.total_doctors ?? 8,
      subtext: '8 active specialities',
      icon: Users,
      color: 'from-blue-600 to-cyan-500',
      badge: 'Active'
    },
    {
      title: 'Available Slots',
      value: stats?.available_slots_count ?? 382,
      subtext: 'Across next 7 days',
      icon: CalendarDays,
      color: 'from-emerald-600 to-teal-500',
      badge: 'Live'
    },
    {
      title: "Today's Appointments",
      value: stats?.today_appointments_count ?? 0,
      subtext: 'Scheduled for today',
      icon: CalendarCheck2,
      color: 'from-indigo-600 to-blue-500',
      badge: 'Today'
    },
    {
      title: 'Total Bookings',
      value: stats?.total_appointments_count ?? 2,
      subtext: `${stats?.cancelled_appointments_count ?? 0} cancelled`,
      icon: Activity,
      color: 'from-purple-600 to-pink-500',
      badge: 'All-time'
    }
  ];

  return (
    <div className="space-y-6">
      
      {/* Hero Banner with Try Call */}
      <div className="relative overflow-hidden rounded-3xl bg-gradient-to-r from-blue-950/80 via-slate-900 to-cyan-950/60 border border-blue-500/20 p-8 shadow-2xl">
        <div className="relative z-10 max-w-2xl">
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-blue-500/10 border border-blue-500/20 text-xs font-semibold text-blue-400 mb-4">
            <Sparkles className="w-3.5 h-3.5" />
            <span>Voice-First Healthcare Scheduling</span>
          </div>
          <h2 className="text-3xl font-extrabold tracking-tight text-white sm:text-4xl">
            Book Doctor Appointments with Voice AI
          </h2>
          <p className="mt-3 text-sm text-slate-300 leading-relaxed">
            Experience the real-time voice receptionist powered by Pipecat, Google Gemini, and ElevenLabs. Check doctor availability, verify spoken phone numbers, and manage bookings seamlessly.
          </p>
          <div className="mt-6 flex items-center space-x-4">
            <button
              onClick={onOpenCall}
              className="flex items-center space-x-2.5 px-6 py-3 rounded-2xl bg-gradient-to-r from-blue-600 to-cyan-500 hover:from-blue-500 hover:to-cyan-400 text-white font-semibold text-sm shadow-xl shadow-blue-500/30 transition-all duration-200 active:scale-95"
            >
              <PhoneCall className="w-4 h-4" />
              <span>Launch Voice Call</span>
            </button>
            <button
              onClick={() => onSelectTab('availability')}
              className="px-5 py-3 rounded-2xl bg-slate-900/80 hover:bg-slate-800 border border-slate-700/80 text-sm font-medium text-slate-200 transition-colors"
            >
              Browse Available Slots
            </button>
          </div>
        </div>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {statCards.map((card, idx) => {
          const Icon = card.icon;
          return (
            <div
              key={idx}
              className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800/80 hover:border-slate-700 transition-all shadow-sm"
            >
              <div className="flex items-center justify-between">
                <div className={`w-10 h-10 rounded-xl bg-gradient-to-tr ${card.color} flex items-center justify-center text-white shadow-md`}>
                  <Icon className="w-5 h-5" />
                </div>
                <span className="text-[11px] font-bold px-2 py-0.5 rounded-full bg-slate-800 text-slate-300 border border-slate-700">
                  {card.badge}
                </span>
              </div>
              <div className="mt-4">
                <span className="text-2xl font-bold text-white tracking-tight">
                  {card.value}
                </span>
                <h4 className="text-xs font-medium text-slate-400 mt-0.5">
                  {card.title}
                </h4>
                <p className="text-[11px] text-slate-500 mt-1">
                  {card.subtext}
                </p>
              </div>
            </div>
          );
        })}
      </div>

      {/* Recent Appointments */}
      <div className="rounded-2xl bg-slate-900/60 border border-slate-800/80 p-5 shadow-sm">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-base font-bold text-white">Recent Appointments</h3>
            <p className="text-xs text-slate-400">Live booking activity synced from database</p>
          </div>
          <button
            onClick={() => onSelectTab('appointments')}
            className="text-xs font-semibold text-blue-400 hover:text-blue-300 flex items-center space-x-1"
          >
            <span>View All</span>
            <ArrowUpRight className="w-3.5 h-3.5" />
          </button>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-slate-800 text-slate-400 uppercase tracking-wider text-[10px]">
                <th className="pb-3 font-semibold">Appointment ID</th>
                <th className="pb-3 font-semibold">Doctor</th>
                <th className="pb-3 font-semibold">Speciality</th>
                <th className="pb-3 font-semibold">Date & Time</th>
                <th className="pb-3 font-semibold">Patient Phone</th>
                <th className="pb-3 font-semibold">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {recentAppointments.slice(0, 5).map((appt) => (
                <tr key={appt.id} className="hover:bg-slate-800/30 transition-colors">
                  <td className="py-3 font-mono text-blue-400 font-medium">{appt.appointment_id}</td>
                  <td className="py-3 text-white font-medium">{appt.doctor_name}</td>
                  <td className="py-3 text-slate-300">{appt.doctor_speciality}</td>
                  <td className="py-3 text-slate-300">{appt.appointment_date} at {appt.start_time}</td>
                  <td className="py-3 font-mono text-slate-400">{appt.patient_phone}</td>
                  <td className="py-3">
                    <span
                      className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                        appt.status === 'Booked'
                          ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                          : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                      }`}
                    >
                      {appt.status}
                    </span>
                  </td>
                </tr>
              ))}
              {recentAppointments.length === 0 && (
                <tr>
                  <td colSpan="6" className="py-6 text-center text-slate-500">
                    No appointments booked yet.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

    </div>
  );
}
