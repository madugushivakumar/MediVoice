const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

async function fetchJson(endpoint, options = {}) {
  const url = `${API_BASE}${endpoint}`;
  const response = await fetch(url, {
    headers: {
      'Content-Type': 'application/json',
      ...(options.headers || {})
    },
    ...options
  });
  if (!response.ok) {
    let errorDetail = 'API request failed';
    try {
      const err = await response.json();
      errorDetail = err.detail?.message || err.detail || JSON.stringify(err);
    } catch (e) {
      errorDetail = response.statusText;
    }
    throw new Error(errorDetail);
  }
  return response.json();
}

export const api = {
  // Health
  checkHealth: () => fetchJson('/api/health'),

  // Dashboard Stats
  getStats: () => fetchJson('/api/dashboard/stats'),

  // Doctors
  getDoctors: (speciality = '') => {
    const q = speciality ? `?speciality=${encodeURIComponent(speciality)}` : '';
    return fetchJson(`/api/doctors${q}`);
  },
  getDoctor: (id) => fetchJson(`/api/doctors/${id}`),
  getSpecialities: () => fetchJson('/api/specialities'),

  // Availability
  getAvailability: (params = {}) => {
    const query = new URLSearchParams();
    if (params.doctor_name) query.append('doctor_name', params.doctor_name);
    if (params.speciality) query.append('speciality', params.speciality);
    if (params.date) query.append('date', params.date);
    if (params.preferred_time) query.append('preferred_time', params.preferred_time);
    return fetchJson(`/api/availability?${query.toString()}`);
  },

  // Appointments
  getAppointments: (params = {}) => {
    const query = new URLSearchParams();
    if (params.phone) query.append('phone', params.phone);
    if (params.status) query.append('status', params.status);
    if (params.date) query.append('date', params.date);
    if (params.doctor_id) query.append('doctor_id', params.doctor_id);
    return fetchJson(`/api/appointments?${query.toString()}`);
  },
  createAppointment: (payload) =>
    fetchJson('/api/appointments', {
      method: 'POST',
      body: JSON.stringify(payload)
    }),
  cancelAppointment: (appointmentId, phone) =>
    fetchJson(`/api/appointments/${appointmentId}/cancel`, {
      method: 'POST',
      body: JSON.stringify({ phone })
    }),

  // Calls & Transcripts
  getCalls: () => fetchJson('/api/calls'),
  getTranscript: (sessionId) => fetchJson(`/api/calls/${sessionId}/transcript`),
  getActivityLogs: (limit = 50) => fetchJson(`/api/activity-logs?limit=${limit}`),
  startCall: () => fetchJson('/api/calls/start', { method: 'POST' }),
  endCall: (sessionId) => fetchJson(`/api/calls/${sessionId}/end`, { method: 'POST' })
};
