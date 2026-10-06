import { formatDistanceToNow, format, parseISO } from 'date-fns'
import { ru } from 'date-fns/locale'

export function formatRelativeTime(dateString: string): string {
  try {
    const date = parseISO(dateString)
    return formatDistanceToNow(date, { addSuffix: true, locale: ru })
  } catch {
    return dateString
  }
}

export function formatDate(dateString: string): string {
  try {
    const date = parseISO(dateString)
    return format(date, 'dd.MM.yyyy', { locale: ru })
  } catch {
    return dateString
  }
}

export function formatDateTime(dateString: string): string {
  try {
    const date = parseISO(dateString)
    return format(date, 'dd.MM.yyyy HH:mm', { locale: ru })
  } catch {
    return dateString
  }
}

export function formatTaskStatus(status: string): string {
  const statusMap: Record<string, string> = {
    pending: 'Pending',
    assigned: 'Assigned',
    in_progress: 'In Progress',
    completed: 'Completed',
    cancelled: 'Cancelled',
    rejected: 'Rejected',
  }
  return statusMap[status] || status
}

export function formatTaskType(type: string): string {
  const typeMap: Record<string, string> = {
    maintenance: 'Maintenance',
    repair: 'Repair',
    restock: 'Restock',
    inspection: 'Inspection',
    emergency: 'Emergency',
  }
  return typeMap[type] || type
}

export function formatTaskPriority(priority: string): string {
  const priorityMap: Record<string, string> = {
    low: 'Low',
    medium: 'Medium',
    high: 'High',
    critical: 'Critical',
  }
  return priorityMap[priority] || priority
}

export function formatApparatusStatus(status: string): string {
  const statusMap: Record<string, string> = {
    operational: 'Operational',
    maintenance: 'Maintenance',
    out_of_order: 'Out of Order',
    decommissioned: 'Decommissioned',
  }
  return statusMap[status] || status
}

export function truncate(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text
  return text.slice(0, maxLength - 3) + '...'
}

export function getInitials(name: string): string {
  return name
    .split(' ')
    .map((part) => part[0])
    .join('')
    .toUpperCase()
    .slice(0, 2)
}