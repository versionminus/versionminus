import React from 'react';
import { DEFAULT_USER_ID, UseLicodexReturn } from '@licodex/sdk';

interface Props {
  licodex: UseLicodexReturn;
}

export function SystemBar({ licodex }: Props) {
  const user = licodex.currentUser;
  return (
    <div style={{
      height: 32,
      display: 'flex',
      alignItems: 'center',
      padding: '0 12px',
      gap: 12,
      background: 'var(--panel-bg, #111)',
      borderBottom: '1px solid var(--border)'
    }}>
      <div style={{ fontWeight: 500, fontSize: 13 }}>licodex</div>
      <div style={{ fontSize: 12, opacity: 0.8 }}> {user?.email || 'loading...'}</div>
      {user && user.id !== DEFAULT_USER_ID && (
        <div style={{ fontSize: 11, background: '#444', padding: '2px 6px', borderRadius: 4 }}>custom</div>
      )}
      <div style={{ marginLeft: 'auto', fontSize: 11, opacity: 0.5 }}>v1.0.0</div>
    </div>
  );
}
