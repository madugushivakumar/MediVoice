import React, { useState, useEffect, useCallback } from 'react';
import { Header } from './components/layout/Header';
import { Sidebar } from './components/layout/Sidebar';
import { OverviewTab } from './components/dashboard/OverviewTab';
import { VoiceAssistantTab } from './components/voice/VoiceAssistantTab';
import { DoctorsTab } from './components/doctors/DoctorsTab';
import { AvailabilityCalendarTab } from './components/appointments/AvailabilityCalendarTab';
import { AppointmentsTab } from './components/appointments/AppointmentsTab';
import { CallHistoryTab } from './components/calls/CallHistoryTab';
import { ActivityLogsTab } from './components/calls/ActivityLogsTab';
import { SettingsTab } from './components/settings/SettingsTab';
import { PhoneCallModal } from './components/voice/PhoneCallModal';
import { useVoiceCall } from './hooks/useVoiceCall';
import { useLiveEvents } from './hooks/useLiveEvents';
import { api } from './services/api';

export function App() {
  const [currentTab, setCurrentTab] = useState('overview');
  const [isCallModalOpen, setIsCallModalOpen] = useState(false);
  const [stats, setStats] = useState(null);
  const [recentAppointments, setRecentAppointments] = useState([]);
  const [selectedDoctorFilter, setSelectedDoctorFilter] = useState('');
  const [highlightedAppointmentId, setHighlightedAppointmentId] = useState(null);

  // Hook for real-time voice call session
  const voice = useVoiceCall();

  // Load dashboard stats & recent appointments
  const refreshDashboardData = useCallback(async () => {
    try {
      const [statsData, apptsData] = await Promise.all([
        api.getStats(),
        api.getAppointments()
      ]);
      setStats(statsData);
      setRecentAppointments(apptsData);
    } catch (e) {
      console.warn('Dashboard fetch error:', e);
    }
  }, []);

  useEffect(() => {
    refreshDashboardData();
  }, [refreshDashboardData]);

  // Real-time live event subscriber from backend WebSocket
  useLiveEvents(
    useCallback(
      (event) => {
        if (event.type === 'APPOINTMENT_BOOKED') {
          refreshDashboardData();
          if (event.data?.appointment_id) {
            setHighlightedAppointmentId(event.data.appointment_id);
          }
        } else if (event.type === 'APPOINTMENT_CANCELLED') {
          refreshDashboardData();
          if (event.data?.appointment_id) {
            setHighlightedAppointmentId(event.data.appointment_id);
          }
        }
      },
      [refreshDashboardData]
    )
  );

  const handleOpenCall = () => {
    setIsCallModalOpen(true);
    if (voice.callState === 'IDLE' || voice.callState === 'ENDED') {
      voice.startCall();
    }
  };

  const handleSelectDoctorForSlots = (doctorName) => {
    setSelectedDoctorFilter(doctorName);
    setCurrentTab('availability');
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      {/* Top Navigation Header */}
      <Header onOpenCall={handleOpenCall} activeCallsCount={stats?.active_calls_count || 0} />

      <div className="flex-1 flex overflow-hidden">
        {/* Navigation Sidebar */}
        <Sidebar currentTab={currentTab} setCurrentTab={setCurrentTab} />

        {/* Main Content Area */}
        <main className="flex-1 overflow-y-auto p-4 sm:p-6 lg:p-8 max-w-7xl mx-auto w-full">
          {currentTab === 'overview' && (
            <OverviewTab
              stats={stats}
              recentAppointments={recentAppointments}
              onOpenCall={handleOpenCall}
              onSelectTab={setCurrentTab}
            />
          )}

          {currentTab === 'voice' && <VoiceAssistantTab onOpenCall={handleOpenCall} />}

          {currentTab === 'doctors' && (
            <DoctorsTab onSelectDoctor={handleSelectDoctorForSlots} />
          )}

          {currentTab === 'availability' && (
            <AvailabilityCalendarTab initialDoctor={selectedDoctorFilter} />
          )}

          {currentTab === 'appointments' && (
            <AppointmentsTab highlightedAppointmentId={highlightedAppointmentId} />
          )}

          {currentTab === 'calls' && <CallHistoryTab />}

          {currentTab === 'logs' && <ActivityLogsTab />}

          {currentTab === 'settings' && <SettingsTab />}
        </main>
      </div>

      {/* Real-Time Phone Call Interface Modal */}
      <PhoneCallModal
        isOpen={isCallModalOpen}
        onClose={() => setIsCallModalOpen(false)}
        callState={voice.callState}
        pipelineMode={voice.pipelineMode}
        callDuration={voice.callDuration}
        isMuted={voice.isMuted}
        transcript={voice.transcript}
        audioLevel={voice.audioLevel}
        errorMessage={voice.errorMessage}
        bookingConfirmation={voice.bookingConfirmation}
        lastToolExecution={voice.lastToolExecution}
        onStartCall={voice.startCall}
        onEndCall={voice.endCall}
        onToggleMute={voice.toggleMute}
        onSendSpokenInput={voice.sendSpokenInput}
      />
    </div>
  );
}

export default App;
