import React from 'react';
import { UseversionminusReturn } from '@versionminus/sdk';
import { Icon, ICON_SIZE } from './Icon';

interface Props {
  versionminus: UseversionminusReturn;
  showThreads: boolean;
  showNotes: boolean;
  onToggleThreads: () => void;
  onToggleNotes: () => void;
  onLogout?: () => void;
  userEmail?: string;
  loadingUser?: boolean;
}

export function SystemBar({
  versionminus,
  showThreads,
  showNotes,
  onToggleThreads,
  onToggleNotes,
  onLogout,
  userEmail,
  loadingUser,
}: Props) {
  const user = versionminus.currentUser;
  const displayEmail = user?.email || userEmail || '';
  return (
    <div className="sysbar">
      <div className="sysbar-title">versionminus</div>
      <div className="user-email">
        {displayEmail || (loadingUser ? 'loading…' : '—')}
      </div>
      <div className="sysbar-spacer" />
      {onLogout && (
        <button className="btn outline small" title="Sign out" onClick={onLogout}>
          Sign out
        </button>
      )}
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
