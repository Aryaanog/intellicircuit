import React from 'react';

export default function TabButton({ label, active, onClick }) {
  return (
    <button
      onClick={onClick}
      className={`text-xs font-medium tracking-wider px-5 py-2.5 rounded-xl transition-all duration-300 capitalize cursor-pointer relative ${
        active ? 'text-white font-semibold' : 'text-slate-500 hover:text-slate-300'
      }`}
    >
      <span className="relative z-10">{label}</span>
      {active && (
        <div className="absolute inset-0 bg-slate-800/80 rounded-xl border border-slate-700/30 layout-id-line" />
      )}
    </button>
  );
}