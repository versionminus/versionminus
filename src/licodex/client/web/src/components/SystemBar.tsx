import React from 'react';
import { DEFAULT_USER_ID, UseLicodexReturn } from '@licodex/sdk';
import { Icon } from './Icon';

interface Props {
  licodex: UseLicodexReturn;
  showThreads: boolean;
  showNotes: boolean;
  onToggleThreads: () => void;
  onToggleNotes: () => void;
}

export function SystemBar({ licodex, showThreads, showNotes, onToggleThreads, onToggleNotes }: Props) {
  const user = licodex.currentUser;
  return (
    <div className="sysbar">
      <div className="sysbar-title">licodex</div>
      <div style={{ fontSize: 12, opacity: 0.8 }}> {user?.email || 'loading...'}</div>
      {user && user.id !== DEFAULT_USER_ID && (
        <div style={{ fontSize: 11, background: '#233028', padding: '2px 6px', borderRadius: 4, color: '#7ee787' }}>custom</div>
      )}
      <div className="sysbar-spacer" />
      <button className={`btn outline small ${showThreads ? '' : 'inactive'}`} title="Toggle threads" onClick={onToggleThreads}>
        <Icon name="threads" size={16} />
      </button>
      <button className={`btn outline small ${showNotes ? '' : 'inactive'}`} title="Toggle notes" onClick={onToggleNotes}>
        <Icon name="note" size={16} />
      </button>
      <div style={{ fontSize: 11, opacity: 0.5 }}>v1.0.0</div>
    </div>
  );
}
