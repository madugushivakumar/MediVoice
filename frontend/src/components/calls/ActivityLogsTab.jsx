import React, { useState, useEffect } from 'react';
import { api } from '../../services/api';
import { FileText, Terminal, CheckCircle, XCircle, RefreshCw } from 'lucide-react';

export function ActivityLogsTab() {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);

  async function fetchLogs() {
    try {
      setLoading(true);
      const data = await api.getActivityLogs(50);
      setLogs(data);
    } catch (err) {
      console.error('Failed to fetch activity logs:', err);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    fetchLogs();
  }, []);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-white">System Activity Logs</h2>
          <p className="text-xs text-slate-400">Audit trail of function calls, parameters (masked) & backend results</p>
        </div>
        <button
          onClick={fetchLogs}
          className="p-2 rounded-xl bg-slate-900 border border-slate-800 text-slate-400 hover:text-white transition-colors"
          title="Refresh logs"
        >
          <RefreshCw className="w-4 h-4" />
        </button>
      </div>

      {loading ? (
        <div className="p-12 text-center text-slate-500 text-sm">Loading activity logs...</div>
      ) : (
        <div className="space-y-3">
          {logs.map((log) => {
            const isSuccess = log.status === 'success';
            return (
              <div
                key={log.id}
                className="p-4 rounded-xl bg-slate-900/60 border border-slate-800/80 font-mono text-xs space-y-2"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-blue-500/15 text-blue-400 border border-blue-500/30">
                      {log.tool_name}
                    </span>
                    <span className="text-slate-400 text-[11px]">{log.session_id}</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <span
                      className={`flex items-center space-x-1 text-[10px] font-bold px-2 py-0.5 rounded-full ${
                        isSuccess
                          ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                          : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                      }`}
                    >
                      {isSuccess ? <CheckCircle className="w-3 h-3" /> : <XCircle className="w-3 h-3" />}
                      <span>{log.status}</span>
                    </span>
                    <span className="text-slate-500 text-[10px]">
                      {new Date(log.created_at).toLocaleTimeString()}
                    </span>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-2 pt-1 text-[11px]">
                  <div className="p-2.5 rounded-lg bg-slate-950/80 border border-slate-800 overflow-x-auto text-slate-300">
                    <span className="text-[10px] text-slate-500 uppercase block mb-1">Arguments:</span>
                    <pre className="whitespace-pre-wrap">{log.arguments}</pre>
                  </div>
                  <div className="p-2.5 rounded-lg bg-slate-950/80 border border-slate-800 overflow-x-auto text-slate-300">
                    <span className="text-[10px] text-slate-500 uppercase block mb-1">Result:</span>
                    <pre className="whitespace-pre-wrap">{log.result}</pre>
                  </div>
                </div>
              </div>
            );
          })}
          {logs.length === 0 && (
            <div className="p-12 text-center text-slate-500 text-sm rounded-2xl bg-slate-900/40 border border-slate-800">
              No activity logs recorded yet. Tool executions will be logged here in real-time.
            </div>
          )}
        </div>
      )}
    </div>
  );
}
