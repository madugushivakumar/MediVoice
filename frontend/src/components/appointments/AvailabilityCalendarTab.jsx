import React, { useState, useEffect } from 'react';
import { api } from '../../services/api';
import { Calendar, Clock, Filter, CheckCircle2, User, Sparkles } from 'lucide-react';

export function AvailabilityCalendarTab({ initialDoctor = '' }) {
  const [doctorName, setDoctorName] = useState(initialDoctor);
  const [speciality, setSpeciality] = useState('');
  const [date, setDate] = useState('tomorrow');
  const [availabilityData, setAvailabilityData] = useState(null);
  const [loading, setLoading] = useState(false);

  async function fetchSlots() {
    try {
      setLoading(true);
      const res = await api.getAvailability({
        doctor_name: doctorName || undefined,
        speciality: speciality || undefined,
        date: date || undefined
      });
      setAvailabilityData(res);
    } catch (err) {
      console.error('Failed to fetch availability:', err);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    fetchSlots();
  }, [doctorName, speciality, date]);

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-white">Availability Calendar</h2>
          <p className="text-xs text-slate-400">Real-time doctor appointment slots directly from SQLite database</p>
        </div>

        {/* Filters */}
        <div className="flex flex-wrap items-center gap-3 w-full sm:w-auto">
          <select
            value={date}
            onChange={(e) => setDate(e.target.value)}
            className="px-3 py-2 rounded-xl bg-slate-900 border border-slate-800 text-xs text-slate-300 focus:outline-none focus:border-blue-500"
          >
            <option value="today">Today</option>
            <option value="tomorrow">Tomorrow</option>
            <option value="day after tomorrow">Day After Tomorrow</option>
          </select>

          <input
            type="text"
            placeholder="Doctor name (e.g. Arjun)"
            value={doctorName}
            onChange={(e) => setDoctorName(e.target.value)}
            className="px-3.5 py-2 rounded-xl bg-slate-900 border border-slate-800 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
          />

          <select
            value={speciality}
            onChange={(e) => setSpeciality(e.target.value)}
            className="px-3 py-2 rounded-xl bg-slate-900 border border-slate-800 text-xs text-slate-300 focus:outline-none focus:border-blue-500"
          >
            <option value="">All Specialities</option>
            <option value="Cardiology">Cardiology</option>
            <option value="Dermatology">Dermatology</option>
            <option value="Neurology">Neurology</option>
            <option value="Orthopedics">Orthopedics</option>
            <option value="Pediatrics">Pediatrics</option>
            <option value="General Medicine">General Medicine</option>
            <option value="Gynecology">Gynecology</option>
            <option value="ENT">ENT</option>
          </select>
        </div>
      </div>

      {loading ? (
        <div className="p-12 text-center text-slate-500 text-sm">Checking available slots...</div>
      ) : availabilityData?.available_slots?.length > 0 ? (
        <div className="space-y-6">
          <div className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800 flex items-center justify-between text-xs">
            <span className="text-slate-300">
              Showing <strong>{availabilityData.available_slots.length}</strong> available slots for{' '}
              <strong className="text-blue-400">{availabilityData.date}</strong>
            </span>
            <span className="text-slate-500">Asia/Kolkata Clinic Hours</span>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-3">
            {availabilityData.available_slots.map((slot) => (
              <div
                key={slot.slot_id}
                className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800 hover:border-blue-500/40 transition-all text-left space-y-1.5"
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-white flex items-center space-x-1">
                    <Clock className="w-3 h-3 text-blue-400" />
                    <span>{slot.start_time}</span>
                  </span>
                  <span className="w-2 h-2 rounded-full bg-emerald-400"></span>
                </div>
                <p className="text-[11px] font-semibold text-slate-200 truncate">{slot.doctor_name}</p>
                <span className="text-[10px] text-slate-400 block truncate">{slot.speciality}</span>
              </div>
            ))}
          </div>
        </div>
      ) : (
        <div className="p-12 text-center text-slate-500 text-sm rounded-2xl bg-slate-900/40 border border-slate-800">
          No available slots found for the selected criteria. Try another date or doctor.
        </div>
      )}
    </div>
  );
}
