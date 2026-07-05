import React, { useEffect, useState } from 'react';
import { fetchWithAuth, API_BASE_URL } from '../api';

interface Worker {
  id: string;
  hostname: string;
  status: string;
  last_heartbeat_at: string;
}

export default function Workers() {
  const [workers, setWorkers] = useState<Worker[]>([]);

  useEffect(() => {
    const fetchWorkers = () => {
      fetchWithAuth(`${API_BASE_URL}/api/v1/workers/`)
        .then(res => res.json())
        .then(data => setWorkers(data))
        .catch(console.error);
    };
    fetchWorkers();
    const interval = setInterval(fetchWorkers, 2000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="space-y-8">
      <h2 className="text-2xl font-medium mb-4 text-white">Active Workers</h2>
      <div className="bg-zinc-900 border border-zinc-800 rounded-xl overflow-hidden">
        <table className="w-full text-left text-sm">
          <thead className="bg-zinc-800/50 text-zinc-400">
            <tr>
              <th className="px-6 py-3 font-medium">Worker ID</th>
              <th className="px-6 py-3 font-medium">Hostname</th>
              <th className="px-6 py-3 font-medium">Status</th>
              <th className="px-6 py-3 font-medium">Last Heartbeat</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-zinc-800">
            {workers.map((w) => (
              <tr key={w.id} className="hover:bg-zinc-800/20 transition-colors">
                <td className="px-6 py-4 font-mono text-xs text-zinc-500">{w.id}</td>
                <td className="px-6 py-4 text-zinc-200">{w.hostname}</td>
                <td className="px-6 py-4">
                  <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-400">
                    {w.status}
                  </span>
                </td>
                <td className="px-6 py-4 text-zinc-400">{new Date(w.last_heartbeat_at).toLocaleString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
