import React, { useState, useEffect } from 'react';
import { api } from '../../services/api';
import { PhoneForwarded, Clock, MessageSquare, X, Bot, User } from 'lucide-react';

export function CallHistoryTab() {
  const [calls, setCalls] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedSessionId, setSelectedSessionId] = useState(null);
  const [transcript, setTranscript] = useState([]);
  const [transcriptLoading, setTranscriptLoading] = useState(false);

  useEffect(() => {
    async function fetchCalls() {
      try {
        setLoading(true);
        const data = await api.getCalls();
        setCalls(data);
      } catch (err) {
        console.error('Failed to fetch call history:', err);
      } finally {
        setLoading(false);
      }
    }
    fetchCalls();
  }, []);

  async function openTranscript(sessionId) {
    try {
      setSelectedSessionId(sessionId);
      setTranscriptLoading(true);
      const data = await api.getTranscript(sessionId);
      setTranscript(data);
    } catch (err) {
      console.error('Failed to load transcript:', err);
    } finally {
      setTranscriptLoading(false);
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold text-white">Call History</h2>
        <p className="text-xs text-slate-400">Previous conversational sessions, durations & transcript audits</p>
      </div>

      {loading ? (
        <div className="p-12 text-center text-slate-500 text-sm">Loading call history...</div>
      ) : (
        <div className="rounded-2xl bg-slate-900/60 border border-slate-800/80 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-slate-800 text-slate-400 uppercase tracking-wider text-[10px] bg-slate-950/40">
                  <th className="py-3 px-4 font-semibold">Session ID</th>
                  <th className="py-3 px-4 font-semibold">Started At</th>
                  <th className="py-3 px-4 font-semibold">Duration</th>
                  <th className="py-3 px-4 font-semibold">Status</th>
                  <th className="py-3 px-4 font-semibold">Messages</th>
                  <th className="py-3 px-4 font-semibold text-right">Transcript</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {calls.map((call) => (
                  <tr key={call.id} className="hover:bg-slate-800/30 transition-colors">
                    <td className="py-3 px-4 font-mono font-medium text-blue-400">{call.session_id}</td>
                    <td className="py-3 px-4 text-slate-300">
                      {new Date(call.started_at).toLocaleString()}
                    </td>
                    <td className="py-3 px-4 font-mono text-slate-300">
                      {call.duration_seconds ? `${call.duration_seconds}s` : 'Active'}
                    </td>
                    <td className="py-3 px-4">
                      <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-slate-800 text-slate-300 border border-slate-700">
                        {call.status}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-slate-400">{call.messages_count} messages</td>
                    <td className="py-3 px-4 text-right">
                      <button
                        onClick={() => openTranscript(call.session_id)}
                        className="px-2.5 py-1 rounded-lg text-[11px] font-semibold text-blue-400 hover:bg-blue-500/10 border border-blue-500/20 transition-colors"
                      >
                        View Transcript
                      </button>
                    </td>
                  </tr>
                ))}
                {calls.length === 0 && (
                  <tr>
                    <td colSpan="6" className="py-8 text-center text-slate-500">
                      No call sessions recorded yet. Try a voice call above!
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Transcript Modal */}
      {selectedSessionId && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm">
          <div className="w-full max-w-lg rounded-2xl bg-slate-950 border border-slate-800 p-5 space-y-4 shadow-2xl flex flex-col max-h-[80vh]">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <div className="flex items-center space-x-2">
                <MessageSquare className="w-5 h-5 text-blue-400" />
                <h3 className="text-sm font-bold text-white">Transcript: {selectedSessionId}</h3>
              </div>
              <button
                onClick={() => setSelectedSessionId(null)}
                className="p-1 rounded-lg text-slate-400 hover:text-white"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="flex-1 overflow-y-auto space-y-3 pr-2">
              {transcriptLoading ? (
                <div className="py-8 text-center text-slate-500 text-xs">Loading transcript...</div>
              ) : transcript.length > 0 ? (
                transcript.map((msg, i) => (
                  <div
                    key={i}
                    className={`p-3 rounded-xl text-xs space-y-1 ${
                      msg.speaker === 'AI' ? 'bg-slate-900 border border-slate-800' : 'bg-blue-950/40 border border-blue-800/40'
                    }`}
                  >
                    <div className="flex items-center justify-between text-[10px] text-slate-400">
                      <span className="font-semibold text-slate-200">{msg.speaker}</span>
                      <span>{new Date(msg.timestamp).toLocaleTimeString()}</span>
                    </div>
                    <p className="text-slate-300">{msg.message}</p>
                  </div>
                ))
              ) : (
                <div className="py-8 text-center text-slate-500 text-xs">No messages recorded for this session.</div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
