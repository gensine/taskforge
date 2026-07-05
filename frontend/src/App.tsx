import React from 'react';
import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom';
import Dashboard from './pages/Dashboard';
import Queues from './pages/Queues';
import Workers from './pages/Workers';

function Layout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100 font-sans">
      <header className="border-b border-zinc-800 bg-zinc-900/50 backdrop-blur-md px-6 py-4 flex justify-between items-center">
        <h1 className="text-xl font-semibold tracking-tight text-white flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
          TaskForge
        </h1>
        <nav className="flex gap-4">
          <NavLink 
            to="/"
            className={({isActive}) => `text-sm transition-colors ${isActive ? 'text-emerald-400 font-medium' : 'text-zinc-400 hover:text-white'}`}>
            Dashboard
          </NavLink>
          <NavLink 
            to="/queues"
            className={({isActive}) => `text-sm transition-colors ${isActive ? 'text-emerald-400 font-medium' : 'text-zinc-400 hover:text-white'}`}>
            Queues
          </NavLink>
          <NavLink 
            to="/workers"
            className={({isActive}) => `text-sm transition-colors ${isActive ? 'text-emerald-400 font-medium' : 'text-zinc-400 hover:text-white'}`}>
            Workers
          </NavLink>
        </nav>
      </header>

      <main className="max-w-7xl mx-auto p-6 space-y-8">
        {children}
      </main>
    </div>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/queues" element={<Queues />} />
          <Route path="/workers" element={<Workers />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  );
}
