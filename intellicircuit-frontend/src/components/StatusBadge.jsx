import React from 'react';

export default function StatusBadge({ type, label }) {
  const styles = {
    MCU: 'text-sky-400 bg-sky-500/10 border-sky-500/20',
    'SUB-CIRCUIT': 'text-amber-400 bg-amber-500/10 border-amber-500/20',
    PERIPHERAL: 'text-purple-400 bg-purple-500/10 border-purple-500/20',
  };

  return (
    <span className={`px-2.5 py-0.5 rounded border text-[10px] font-mono uppercase tracking-wider ${styles[type] || 'text-slate-400 bg-slate-500/10'}`}>
      {label}
    </span>
  );
}