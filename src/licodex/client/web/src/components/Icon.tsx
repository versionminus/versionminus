import React from 'react';
import {
  VscAdd, VscClose, VscTrash, VscEdit, VscCheck, VscRefresh, VscCommentDiscussion, VscNotebook, VscRocket
} from 'react-icons/vsc';

export type IconName = 'plus' | 'x' | 'trash' | 'edit' | 'check' | 'refresh' | 'threads' | 'note' | 'send';

const iconMap: Record<IconName, React.ComponentType<{ size?: number }>> = {
  plus: VscAdd,
  x: VscClose,
  trash: VscTrash,
  edit: VscEdit,
  check: VscCheck,
  refresh: VscRefresh,
  threads: VscCommentDiscussion,
  note: VscNotebook,
  send: VscRocket
};

interface Props { name: IconName; size?: number; }

export function Icon({ name, size = 16 }: Props) {
  const C = iconMap[name];
  return <C size={size} />;
}
