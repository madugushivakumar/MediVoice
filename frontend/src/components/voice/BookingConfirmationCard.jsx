import React from 'react';
import { CheckCircle2, Calendar, Clock, User, Phone, Stethoscope } from 'lucide-react';

export function BookingConfirmationCard({ confirmation }) {
  if (!confirmation) return null;

  return (
    <div className="p-4 rounded-2xl bg-gradient-to-b from-emerald-950/40 to-slate-900 border border-emerald-500/30 shadow-lg shadow-emerald-500/10">
      <div className="flex items-center space-x-2 text-emerald-400 mb-3">
        <CheckCircle2 className="w-5 h-5" />
        <span className="text-sm font-bold uppercase tracking-wider">
          Appointment Confirmed
        </span>
      </div>

      <div className="grid grid-cols-2 gap-3 text-xs">
        <div className="p-2.5 rounded-xl bg-slate-950/60 border border-slate-800">
          <span className="text-slate-400 block mb-0.5">Confirmation ID</span>
          <span className="font-mono font-semibold text-emerald-300">
            {confirmation.appointment_id}
          </span>
        </div>

        <div className="p-2.5 rounded-xl bg-slate-950/60 border border-slate-800">
          <span className="text-slate-400 block mb-0.5">Doctor</span>
          <span className="font-semibold text-slate-200">
            {confirmation.doctor_name}
          </span>
        </div>

        <div className="p-2.5 rounded-xl bg-slate-950/60 border border-slate-800">
          <span className="text-slate-400 block mb-0.5">Date & Time</span>
          <span className="font-semibold text-slate-200">
            {confirmation.appointment_date} at {confirmation.start_time}
          </span>
        </div>

        <div className="p-2.5 rounded-xl bg-slate-950/60 border border-slate-800">
          <span className="text-slate-400 block mb-0.5">Confirmed Phone</span>
          <span className="font-mono text-slate-300">
            {confirmation.patient_phone_masked || 'Confirmed'}
          </span>
        </div>
      </div>
    </div>
  );
}
