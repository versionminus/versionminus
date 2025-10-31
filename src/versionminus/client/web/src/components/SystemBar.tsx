import React from 'react';
import { getVersion } from '@versionminus';
import { Icon } from './Icon';
import type { IconName } from './Icon';

const SYSBAR_ICON_SIZE = 16;
const sdkVersion = getVersion();

type ViewKey = 'think' | 'thought' | 'time' | 'money' | 'identity';

interface Props {
  activeView: ViewKey;
  onSelect: (view: ViewKey) => void;
  onLogout?: () => void;
  userEmail?: string;
  loadingUser?: boolean;
}

export function SystemBar({
  activeView,
  onSelect,
  onLogout,
  userEmail,
  loadingUser,
}: Props) {
  const displayEmail = userEmail || '';
  const controls: Array<{ key: ViewKey; label: string; icon: IconName; title: string }> = [
    { key: 'think', label: 'think', icon: 'think', title: 'Conversations' },
    { key: 'thought', label: 'thought', icon: 'thought', title: 'Notes' },
    { key: 'time', label: 'time', icon: 'time', title: 'Time' },
    { key: 'money', label: 'money', icon: 'money', title: 'Money' },
    { key: 'identity', label: 'identity', icon: 'identity', title: 'Identity graph' },
  ];

  return (
    <div className="sysbar">
      <div className="sysbar-left">
        <img src="/logo.png" alt="versionminus logo" className="sysbar-logo" />
        <span className="sysbar-email">
          {displayEmail || (loadingUser ? 'loading…' : '—')}
        </span>
      </div>
      <div className="sysbar-actions">
        {controls.map(control => (
          <button
            key={control.key}
            type="button"
            className="sysbar-button"
            title={control.title}
            aria-label={control.label}
            aria-pressed={activeView === control.key}
            data-active={activeView === control.key}
            onClick={() => onSelect(control.key)}
          >
            <Icon name={control.icon} size={SYSBAR_ICON_SIZE} />
          </button>
        ))}
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
        <div className="sysbar-version">v{sdkVersion}</div>
      </div>
    </div>
  );
}
