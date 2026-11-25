import React, { useState, useEffect } from 'react';
import { api } from '../../services/api';
import { Search, Filter, Stethoscope, Award, Clock, ArrowRight } from 'lucide-react';

export function DoctorsTab({ onSelectDoctor }) {
  const [doctors, setDoctors] = useState([]);
  const [specialities, setSpecialities] = useState([]);
  const [selectedSpeciality, setSelectedSpeciality] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        const [docsData, specsData] = await Promise.all([
          api.getDoctors(selectedSpeciality),
          api.getSpecialities()
        ]);
        setDoctors(docsData);
        setSpecialities(specsData);
      } catch (err) {
        console.error('Failed to load doctors:', err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, [selectedSpeciality]);

  const filteredDoctors = doctors.filter((doc) => {
    const matchesSearch =
      doc.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      doc.department.toLowerCase().includes(searchTerm.toLowerCase()) ||
      doc.speciality.toLowerCase().includes(searchTerm.toLowerCase());
    return matchesSearch;
  });

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-white">Doctors Directory</h2>
          <p className="text-xs text-slate-400">Our specialized medical practitioners and department heads</p>
        </div>

        {/* Filters */}
        <div className="flex items-center space-x-3 w-full sm:w-auto">
          <div className="relative flex-1 sm:w-64">
            <Search className="w-4 h-4 absolute left-3 top-3 text-slate-500" />
            <input
              type="text"
              placeholder="Search doctors or dept..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-9 pr-4 py-2 rounded-xl bg-slate-900 border border-slate-800 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
            />
          </div>

          <select
            value={selectedSpeciality}
            onChange={(e) => setSelectedSpeciality(e.target.value)}
            className="px-3 py-2 rounded-xl bg-slate-900 border border-slate-800 text-xs text-slate-300 focus:outline-none focus:border-blue-500"
          >
            <option value="">All Specialities</option>
            {specialities.map((spec) => (
              <option key={spec} value={spec}>
                {spec}
              </option>
            ))}
          </select>
        </div>
      </div>

      {loading ? (
        <div className="p-12 text-center text-slate-500 text-sm">Loading doctors...</div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredDoctors.map((doc) => (
            <div
              key={doc.id}
              className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800/80 hover:border-slate-700 transition-all flex flex-col justify-between"
            >
              <div>
                <div className="flex items-start justify-between">
                  <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-blue-600 to-cyan-500 flex items-center justify-center font-bold text-white text-base shadow-md">
                    {doc.name.split(' ').map((n) => n[0]).join('').slice(0, 2)}
                  </div>
                  <span className="px-2.5 py-1 rounded-full text-[11px] font-semibold bg-blue-500/10 text-blue-400 border border-blue-500/20">
                    {doc.speciality}
                  </span>
                </div>

                <h3 className="text-base font-bold text-white mt-3">{doc.name}</h3>
                <p className="text-xs text-slate-400 mt-0.5">{doc.qualification}</p>

                <div className="mt-4 pt-3 border-t border-slate-800/80 space-y-1.5 text-xs text-slate-300">
                  <div className="flex items-center space-x-2">
                    <Award className="w-3.5 h-3.5 text-slate-500" />
                    <span>{doc.experience_years} years of medical experience</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Stethoscope className="w-3.5 h-3.5 text-slate-500" />
                    <span className="text-slate-400">{doc.department}</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Clock className="w-3.5 h-3.5 text-slate-500" />
                    <span>{doc.consultation_duration} mins standard consultation</span>
                  </div>
                </div>
              </div>

              <div className="mt-5 pt-3 border-t border-slate-800/60 flex items-center justify-between">
                <span className="text-[11px] font-semibold text-emerald-400 flex items-center space-x-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
                  <span>Available for booking</span>
                </span>
                <button
                  onClick={() => onSelectDoctor && onSelectDoctor(doc.name)}
                  className="text-xs font-semibold text-blue-400 hover:text-blue-300 flex items-center space-x-1"
                >
                  <span>View Slots</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
