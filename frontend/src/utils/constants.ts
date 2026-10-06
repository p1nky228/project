export const TASK_STATUS_OPTIONS = [
  { value: 'pending', label: 'Pending' },
  { value: 'assigned', label: 'Assigned' },
  { value: 'in_progress', label: 'In Progress' },
  { value: 'completed', label: 'Completed' },
  { value: 'cancelled', label: 'Cancelled' },
  { value: 'rejected', label: 'Rejected' },
] as const

export const TASK_TYPE_OPTIONS = [
  { value: 'maintenance', label: 'Maintenance' },
  { value: 'repair', label: 'Repair' },
  { value: 'restock', label: 'Restock' },
  { value: 'inspection', label: 'Inspection' },
  { value: 'emergency', label: 'Emergency' },
] as const

export const TASK_PRIORITY_OPTIONS = [
  { value: 'low', label: 'Low' },
  { value: 'medium', label: 'Medium' },
  { value: 'high', label: 'High' },
  { value: 'critical', label: 'Critical' },
] as const

export const APPARATUS_STATUS_OPTIONS = [
  { value: 'operational', label: 'Operational' },
  { value: 'maintenance', label: 'Maintenance' },
  { value: 'out_of_order', label: 'Out of Order' },
  { value: 'decommissioned', label: 'Decommissioned' },
] as const

export const STATUS_COLORS: Record<string, string> = {
  pending: 'gold',
  assigned: 'cyan',
  in_progress: 'blue',
  completed: 'success',
  cancelled: 'red',
  rejected: 'red',
  operational: 'success',
  maintenance: 'blue',
  out_of_order: 'red',
  decommissioned: 'default',
}

export const PRIORITY_COLORS: Record<string, string> = {
  low: 'green',
  medium: 'gold',
  high: 'orange',
  critical: 'red',
}

export const MAP_STATUS_ICONS: Record<string, string> = {
  operational: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-green.png',
  maintenance: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-blue.png',
  out_of_order: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png',
  decommissioned: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-grey.png',
}

export const DEFAULT_MAP_CENTER = [55.7558, 37.6173] as [number, number]
export const DEFAULT_MAP_ZOOM = 10

export const PAGE_SIZE_OPTIONS = [10, 20, 50, 100]

export const DATE_FORMAT = 'dd.MM.yyyy'
export const DATETIME_FORMAT = 'dd.MM.yyyy HH:mm'