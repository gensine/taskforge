import { useEffect, useState } from 'react';
import { fetchWithAuth, API_BASE_URL } from '../api';

interface Metrics {
  active_workers: number;
  total_queues: number;
}

interface Job {
  id: string;
  type: string;
  status: string;
  priority: number;
}

export default function Dashboard() {
  const [metrics, setMetrics] = useState<Metrics | null>(null);
  const [jobs, setJobs] = useState<Job[]>([]);

  const fetchData = async () => {
    try {
      const [metricsRes, jobsRes] = await Promise.all([
        fetchWithAuth(`${API_BASE_URL}/api/v1/metrics/system-health`),
        fetchWithAuth(`${API_BASE_URL}/api/v1/metrics/recent-jobs`)
      ]);
      if (metricsRes.ok) setMetrics(await metricsRes.json());
      if (jobsRes.ok) setJobs(await jobsRes.json());
    } catch (e) {
      console.error('Fetch error:', e);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 2000);
    return () => clearInterval(interval);
  }, []);

  const getStatusStyle = (status: string) => {
    switch (status.toLowerCase()) {
      case 'completed': return 'bg-emerald-500/10 text-emerald-400';
      case 'running': case 'claimed': return 'bg-blue-500/10 text-blue-400';
      case 'failed': case 'dead_letter': return 'bg-rose-500/10 text-rose-400';
      default: return 'bg-amber-500/10 text-amber-400';
    }
  };

  return (
    <div className="space-y-8">
      <section>
        <h2 className="text-2xl font-medium mb-4 text-white">System Overview</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6 shadow-sm">
            <p className="text-sm text-zinc-400 font-medium">Active Workers</p>
            <p className="text-4xl font-light text-emerald-400 mt-2">
              {metrics ? metrics.active_workers : '...'}
            </p>
          </div>
          <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6 shadow-sm">
            <p className="text-sm text-zinc-400 font-medium">Total Queues</p>
            <p className="text-4xl font-light text-violet-400 mt-2">
              {metrics ? metrics.total_queues : '...'}
            </p>
          </div>
          <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6 shadow-sm">
            <p className="text-sm text-zinc-400 font-medium">Jobs Processed (24h)</p>
            <p className="text-4xl font-light text-blue-400 mt-2">
              {jobs.filter(j => j.status === 'completed').length}
            </p>
          </div>
        </div>
      </section>

      <section>
        <div className="flex justify-between items-end mb-4">
          <h2 className="text-2xl font-medium text-white">Recent Jobs</h2>
        </div>
        <div className="bg-zinc-900 border border-zinc-800 rounded-xl overflow-hidden">
          <table className="w-full text-left text-sm">
            <thead className="bg-zinc-800/50 text-zinc-400">
              <tr>
                <th className="px-6 py-3 font-medium">Job ID</th>
                <th className="px-6 py-3 font-medium">Type</th>
                <th className="px-6 py-3 font-medium">Status</th>
                <th className="px-6 py-3 font-medium">Priority</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-800">
              {jobs.map((job) => (
                <tr key={job.id} className="hover:bg-zinc-800/20 transition-colors">
                  <td className="px-6 py-4 font-mono text-xs text-zinc-500">{job.id.substring(0, 8)}...</td>
                  <td className="px-6 py-4">{job.type}</td>
                  <td className="px-6 py-4">
                    <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${getStatusStyle(job.status)}`}>
                      {job.status.charAt(0).toUpperCase() + job.status.slice(1)}
                    </span>
                  </td>
                  <td className="px-6 py-4">
                    {job.priority > 5 ? 'High' : job.priority === 0 ? 'Normal' : 'Low'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
