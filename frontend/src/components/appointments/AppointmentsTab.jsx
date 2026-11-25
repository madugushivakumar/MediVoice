import React, { useState, useEffect } from 'react';
import { api } from '../../services/api';
import { Search, Filter, CalendarCheck2, XCircle, AlertCircle, RefreshCw } from 'lucide-react';

export function AppointmentsTab({ highlightedAppointmentId = null }) {
  const [appointments, setAppointments] = useState([]);
  const [statusFilter, setStatusFilter] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [loading, setLoading] = useState(true);
  const [cancellingId, setCancellingId] = useState(null);
  const [cancelPhoneInput, setCancelPhoneInput] = useState('');
  const [activeModalAppt, setActiveModalAppt] = useState(null);
  const [errorMsg, setErrorMsg] = useState(null);

  async function loadAppointments() {
    try {
      setLoading(true);
      setErrorMsg(null);
      const data = await api.getAppointments({ status: statusFilter || undefined });
      setAppointments(data);
    } catch (err) {
      setErrorMsg(err.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadAppointments();
  }, [statusFilter]);

  async function handleConfirmCancel() {
    if (!activeModalAppt || !cancelPhoneInput.trim()) return;
    try {
      await api.cancelAppointment(activeModalAppt.appointment_id, cancelPhoneInput.trim());
      setActiveModalAppt(null);
      setCancelPhoneInput('');
      await loadAppointments();
    } catch (err) {
      alert(`Cancellation failed: ${err.message}`);
    }
  }

  const filtered = appointments.filter((appt) => {
    const term = searchTerm.toLowerCase();
    return (
      appt.appointment_id.toLowerCase().includes(term) ||
      appt.doctor_name.toLowerCase().includes(term) ||
      appt.patient_phone.toLowerCase().includes(term) ||
      appt.appointment_date.toLowerCase().includes(term)
    );
  });

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-white">Appointments Management</h2>
          <p className="text-xs text-slate-400">Live booking records, status tracking & historical audit</p>
        </div>

        <div className="flex items-center space-x-3 w-full sm:w-auto">
          <button
            onClick={loadAppointments}
            className="p-2 rounded-xl bg-slate-900 border border-slate-800 text-slate-400 hover:text-white transition-colors"
            title="Refresh appointments"
          >
            <RefreshCw className="w-4 h-4" />
          </button>

          <input
            type="text"
            placeholder="Search by ID, doctor, phone..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full sm:w-60 px-3.5 py-2 rounded-xl bg-slate-900 border border-slate-800 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
          />

          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-3 py-2 rounded-xl bg-slate-900 border border-slate-800 text-xs text-slate-300 focus:outline-none focus:border-blue-500"
          >
            <option value="">All Statuses</option>
            <option value="Booked">Booked</option>
            <option value="Cancelled">Cancelled</option>
            <option value="Completed">Completed</option>
          </select>
        </div>
      </div>

      {errorMsg && (
        <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs">
          {errorMsg}
        </div>
      )}

      {loading ? (
        <div className="p-12 text-center text-slate-500 text-sm">Loading appointments...</div>
      ) : (
        <div className="rounded-2xl bg-slate-900/60 border border-slate-800/80 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-slate-800 text-slate-400 uppercase tracking-wider text-[10px] bg-slate-950/40">
                  <th className="py-3 px-4 font-semibold">Appointment ID</th>
                  <th className="py-3 px-4 font-semibold">Doctor</th>
                  <th className="py-3 px-4 font-semibold">Speciality</th>
                  <th className="py-3 px-4 font-semibold">Date & Time</th>
                  <th className="py-3 px-4 font-semibold">Patient Phone</th>
                  <th className="py-3 px-4 font-semibold">Status</th>
                  <th className="py-3 px-4 font-semibold text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {filtered.map((appt) => {
                  const isHighlighted = highlightedAppointmentId === appt.appointment_id;
                  return (
                    <tr
                      key={appt.id}
                      className={`transition-colors ${
                        isHighlighted ? 'bg-blue-600/20 border-l-4 border-blue-500' : 'hover:bg-slate-800/30'
                      }`}
                    >
                      <td className="py-3.5 px-4 font-mono font-medium text-blue-400">
                        {appt.appointment_id}
                      </td>
                      <td className="py-3.5 px-4 text-white font-medium">{appt.doctor_name}</td>
                      <td className="py-3.5 px-4 text-slate-300">{appt.doctor_speciality}</td>
                      <td className="py-3.5 px-4 text-slate-300">
                        {appt.appointment_date} at {appt.start_time}
                      </td>
                      <td className="py-3.5 px-4 font-mono text-slate-400">{appt.patient_phone}</td>
                      <td className="py-3.5 px-4">
                        <span
                          className={`px-2.5 py-1 rounded-full text-[10px] font-bold ${
                            appt.status === 'Booked'
                              ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                              : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                          }`}
                        >
                          {appt.status}
                        </span>
                      </td>
                      <td className="py-3.5 px-4 text-right">
                        {appt.status === 'Booked' && (
                          <button
                            onClick={() => setActiveModalAppt(appt)}
                            className="px-2.5 py-1 rounded-lg text-[11px] font-semibold text-rose-400 hover:bg-rose-500/10 border border-rose-500/20 transition-colors"
                          >
                            Cancel
                          </button>
                        )}
                      </td>
                    </tr>
                  );
                })}
                {filtered.length === 0 && (
                  <tr>
                    <td colSpan="7" className="py-8 text-center text-slate-500">
                      No appointments found.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Manual Cancellation Confirmation Modal */}
      {activeModalAppt && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm">
          <div className="w-full max-w-sm rounded-2xl bg-slate-950 border border-slate-800 p-5 space-y-4 shadow-2xl">
            <div className="flex items-center space-x-2 text-rose-400">
              <XCircle className="w-5 h-5" />
              <h3 className="text-sm font-bold text-white">Confirm Cancellation</h3>
            </div>
            <p className="text-xs text-slate-300">
              Are you sure you want to cancel appointment <strong>{activeModalAppt.appointment_id}</strong> with{' '}
              <strong>{activeModalAppt.doctor_name}</strong> on {activeModalAppt.appointment_date} at{' '}
              {activeModalAppt.start_time}?
            </p>
            <div className="space-y-1">
              <label className="text-[11px] font-medium text-slate-400">
                Confirm Spoken Phone Number (10-digits):
              </label>
              <input
                type="text"
                placeholder="e.g. 9876543210"
                value={cancelPhoneInput}
                onChange={(e) => setCancelPhoneInput(e.target.value)}
                className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-slate-800 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-rose-500"
              />
            </div>
            <div className="flex items-center justify-end space-x-2 pt-2">
              <button
                onClick={() => setActiveModalAppt(null)}
                className="px-3.5 py-1.5 rounded-xl bg-slate-900 hover:bg-slate-800 text-xs font-medium text-slate-300"
              >
                Keep Appointment
              </button>
              <button
                onClick={handleConfirmCancel}
                className="px-4 py-1.5 rounded-xl bg-rose-600 hover:bg-rose-500 text-xs font-semibold text-white"
              >
                Confirm Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
