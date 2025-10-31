import React from 'react';
import {
  VscAdd,
  VscClose,
  VscTrash,
  VscEdit,
  VscCheck,
  VscRefresh,
  VscSave,
  VscChevronLeft,
  VscChevronRight,
  VscCommentDiscussion,
  VscNotebook,
  VscArrowUp,
  VscListUnordered
} from 'react-icons/vsc';
import {
  FiLogOut, FiMessageCircle, FiFileText, FiCalendar, FiDollarSign, FiFeather, FiAperture
} from 'react-icons/fi';

export type IconName =
  | 'plus'
  | 'x'
  | 'trash'
  | 'edit'
  | 'check'
  | 'refresh'
  | 'save'
  | 'chevron-left'
  | 'chevron-right'
  | 'threads'
  | 'note'
  | 'send'
  | 'sources'
  | 'logout'
  | 'chat'
  | 'file'
  | 'calendar'
  | 'money'
  | 'think'
  | 'thought'
  | 'time'
  | 'identity';

// Single source of truth for sizing all icon-only buttons.
export const ICON_SIZE = 14; // px

const iconMap: Record<IconName, React.ComponentType<{ size?: number }>> = {
  plus: VscAdd,
  x: VscClose,
  trash: VscTrash,
  edit: VscEdit,
  check: VscCheck,
  refresh: VscRefresh,
  save: VscSave,
  'chevron-left': VscChevronLeft,
  'chevron-right': VscChevronRight,
  threads: VscCommentDiscussion,
  note: VscNotebook,
  send: VscArrowUp,
  sources: VscListUnordered,
  logout: FiLogOut,
  chat: FiMessageCircle,
  file: FiFileText,
  calendar: FiCalendar,
  money: FiDollarSign,
  think: FiMessageCircle,
  thought: FiFeather,
  time: FiCalendar,
  identity: FiAperture
};

interface Props { name: IconName; size?: number; }

export function Icon({ name, size = ICON_SIZE }: Props) {
  const C = iconMap[name];
  return <C size={size} />;
}
