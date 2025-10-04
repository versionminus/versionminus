import React from 'react';

export type IconName =
  | 'plus'
  | 'x'
  | 'trash'
  | 'edit'
  | 'check'
  | 'refresh'
  | 'threads'
  | 'note'
  | 'send';

interface Props { name: IconName; size?: number; }

export function Icon({ name, size = 16 }: Props) {
  const p = { stroke: 'currentColor', strokeWidth: 2, strokeLinecap: 'round', strokeLinejoin: 'round', fill: 'none' } as const;
  switch (name) {
    case 'plus':
      return (<svg width={size} height={size} viewBox="0 0 16 16" {...p}><path d="M8 3v10M3 8h10" /></svg>);
    case 'x':
      return (<svg width={size} height={size} viewBox="0 0 16 16" {...p}><path d="M4 4l8 8M12 4l-8 8" /></svg>);
    case 'trash':
      return (<svg width={size} height={size} viewBox="0 0 16 16" {...p}><path d="M3 6h10M6 6v6m4-6v6M5 4h6l1 2H4l1-2zm1 0V3h4v1" /></svg>);
    case 'edit':
      return (<svg width={size} height={size} viewBox="0 0 16 16" {...p}><path d="M3 11l7.5-7.5 2 2L5 13H3v-2z" /></svg>);
    case 'check':
      return (<svg width={size} height={size} viewBox="0 0 16 16" {...p}><path d="M3 8l3 3 7-7" /></svg>);
    case 'refresh':
      return (<svg width={size} height={size} viewBox="0 0 16 16" {...p}><path d="M3 8a5 5 0 0 1 8.5-3.5L13 2v4H9l1.8-1.8A3.5 3.5 0 0 0 3 8m8 3a5 5 0 0 1-8.5 3.5L3 14v-4h4l-1.8 1.8A3.5 3.5 0 0 0 11 11" /></svg>);
    case 'threads':
      return (<svg width={size} height={size} viewBox="0 0 16 16" {...p}><path d="M4 5h8M4 8h8M4 11h8" /></svg>);
    case 'note':
      return (<svg width={size} height={size} viewBox="0 0 16 16" {...p}><path d="M5 2h6a2 2 0 0 1 2 2v6l-4 4H5a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2zm4 11l4-4H9v4z" /></svg>);
    case 'send':
      return (<svg width={size} height={size} viewBox="0 0 16 16" {...p}><path d="M3 13l10-5L3 3v4l6 1-6 1v4z" /></svg>);
    default:
      return null;
  }
}
