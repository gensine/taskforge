import React, { useEffect, useState } from 'react';
import { fetchWithAuth, API_BASE_URL } from '../api';

interface Queue {
  id: string;
  name: string;
  priority: number;
  concurrency_limit: number;
  is_paused: boolean;
}

export default function Queues() {
  const [queues, setQueues] = useState<Queue[]>([]);

  const togglePause = async (queueId: string, isPaused: boolean) => {
    const action = isPaused ? 'resume' : 'pause';
    await fetchWithAuth(`${API_BASE_URL}/api/v1/metrics/queues/${queueId}/${action}`, { method: 'PATCH' });
    // force refresh instantly
    fetchWithAuth(`${API_BASE_URL}/api/v1/metrics/queues`)
      .then(res => res.json())
      .then(data => setQueues(data))
      .catch(console.error);
  };

  const deleteQueue = async (queueId: string) => {
    if (!confirm('Are you sure you want to delete this queue?')) return;
    await fetchWithAuth(`${API_BASE_URL}/api/v1/metrics/queues/${queueId}`, { method: 'DELETE' });
    // force refresh instantly
    fetchWithAuth(`${API_BASE_URL}/api/v1/metrics/queues`)
      .then(res => res.json())
      .then(data => setQueues(data))
      .catch(console.error);
  };

  useEffect(() => {
    const fetchQueues = () => {
      fetchWithAuth(`${API_BASE_URL}/api/v1/metrics/queues`)
        .then(res => res.json())
        .then(data => setQueues(data))
        .catch(console.error);
    };
    fetchQueues();
    const interval = setInterval(fetchQueues, 2000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="space-y-8">
      <h2 className="text-2xl font-medium mb-4 text-white">Queues Management</h2>
      <div className="bg-zinc-900 border border-zinc-800 rounded-xl overflow-hidden">
        <table className="w-full text-left text-sm">
          <thead className="bg-zinc-800/50 text-zinc-400">
            <tr>
              <th className="px-6 py-3 font-medium">Queue ID</th>
              <th className="px-6 py-3 font-medium">Name</th>
              <th className="px-6 py-3 font-medium">Priority</th>
              <th className="px-6 py-3 font-medium">Concurrency Limit</th>
              <th className="px-6 py-3 font-medium">Status</th>
              <th className="px-6 py-3 font-medium text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-zinc-800">
            {queues.map((q) => (
              <tr key={q.id} className="hover:bg-zinc-800/20 transition-colors">
                <td className="px-6 py-4 font-mono text-xs text-zinc-500">{q.id.split('-')[0]}...</td>
                <td className="px-6 py-4 text-zinc-200 font-medium">{q.name}</td>
                <td className="px-6 py-4">
                  <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-500/10 text-blue-400">
                    {q.priority}
                  </span>
                </td>
                <td className="px-6 py-4 text-zinc-400">{q.concurrency_limit}</td>
                <td className="px-6 py-4">
                  {q.is_paused ? (
                    <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-amber-500/10 text-amber-500">Paused</span>
                  ) : (
                    <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-500">Active</span>
                  )}
                </td>
                <td className="px-6 py-4 flex justify-end gap-2">
                  <button 
                    onClick={() => togglePause(q.id, q.is_paused)}
                    className="px-3 py-1 bg-zinc-800 hover:bg-zinc-700 text-white rounded-md text-xs transition-colors">
                    {q.is_paused ? 'Resume' : 'Pause'}
                  </button>
                  <button 
                    onClick={() => deleteQueue(q.id)}
                    className="px-3 py-1 bg-red-900/30 hover:bg-red-900/60 text-red-400 rounded-md text-xs transition-colors">
                    Delete
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
