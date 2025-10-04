import React from 'react';
import { DEFAULT_USER_ID, UseLicodexReturn } from '@licodex/sdk';
import { Icon, ICON_SIZE } from './Icon';

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
      <div className="user-email">{user?.email || 'loading...'}</div>
      {user && user.id !== DEFAULT_USER_ID && (
        <div className="user-badge">custom</div>
      )}
      <div className="sysbar-spacer" />
      <button className={`btn outline small ${showThreads ? '' : 'inactive'}`} title="Toggle threads" onClick={onToggleThreads}>
        <Icon name="threads" size={ICON_SIZE} />
      </button>
      <button className={`btn outline small ${showNotes ? '' : 'inactive'}`} title="Toggle notes" onClick={onToggleNotes}>
        <Icon name="note" size={ICON_SIZE} />
      </button>
      <div className="version-text">v1.0.0</div>
    </div>
  );
}
