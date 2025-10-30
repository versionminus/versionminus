import React from 'react';
import { UseversionminusReturn, getVersion } from '@versionminus/sdk';
import { Icon } from './Icon';

const SYSBAR_ICON_SIZE = 16;
const sdkVersion = getVersion();

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
      <div className="sysbar-left">
        <img src="/logo.png" alt="versionminus logo" className="sysbar-logo" />
        <span className="sysbar-email">
          {displayEmail || (loadingUser ? 'loading…' : '—')}
        </span>
      </div>
      <div className="sysbar-actions">
        {onLogout && (
          <button
            type="button"
            className="sysbar-button"
            title="Sign out"
            aria-label="Sign out"
            onClick={onLogout}
          >
            <Icon name="logout" size={SYSBAR_ICON_SIZE} />
          </button>
        )}
        <button
          type="button"
          className="sysbar-button"
          title="Toggle chat panel"
          aria-label={showThreads ? 'Hide chat panel' : 'Show chat panel'}
          aria-pressed={showThreads}
          data-active={showThreads}
          onClick={onToggleThreads}
        >
          <Icon name="chat" size={SYSBAR_ICON_SIZE} />
        </button>
        <button
          type="button"
          className="sysbar-button"
          title="Toggle notes panel"
          aria-label={showNotes ? 'Hide notes panel' : 'Show notes panel'}
          aria-pressed={showNotes}
          data-active={showNotes}
          onClick={onToggleNotes}
        >
          <Icon name="file" size={SYSBAR_ICON_SIZE} />
        </button>
        <button
          type="button"
          className="sysbar-button"
          title="Schedule (coming soon)"
          aria-label="Schedule (coming soon)"
          disabled
        >
          <Icon name="calendar" size={SYSBAR_ICON_SIZE} />
        </button>
        <button
          type="button"
          className="sysbar-button"
          title="Finances (coming soon)"
          aria-label="Finances (coming soon)"
          disabled
        >
          <Icon name="money" size={SYSBAR_ICON_SIZE} />
        </button>
        <div className="sysbar-version">v{sdkVersion}</div>
      </div>
    </div>
  );
}
