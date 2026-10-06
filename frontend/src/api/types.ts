export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
  pages: number
}

export interface Task {
  id: string
  apparatus_id: string
  technician_id: string | null
  type: TaskType
  status: TaskStatus
  priority: TaskPriority
  title: string
  description: string | null
  scheduled_at: string
  started_at: string | null
  completed_at: string | null
  created_at: string
  updated_at: string
  apparatus?: Apparatus
  technician?: Technician
  photos?: TaskPhoto[]
}

export type TaskType = 'maintenance' | 'repair' | 'restock' | 'inspection' | 'emergency'
export type TaskStatus = 'pending' | 'assigned' | 'in_progress' | 'completed' | 'cancelled' | 'rejected'
export type TaskPriority = 'low' | 'medium' | 'high' | 'critical'

export interface TaskPhoto {
  id: string
  task_id: string
  url: string
  caption: string | null
  uploaded_at: string
  uploaded_by: string
}

export interface Technician {
  id: string
  email: string
  full_name: string
  phone: string | null
  avatar_url: string | null
  rating: number
  completed_tasks: number
  active_tasks: number
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface Apparatus {
  id: string
  serial_number: string
  model: string
  location_lat: number
  location_lng: number
  address: string
  status: ApparatusStatus
  last_maintenance_at: string | null
  next_maintenance_at: string | null
  created_at: string
  updated_at: string
}

export type ApparatusStatus = 'operational' | 'maintenance' | 'out_of_order' | 'decommissioned'

export interface DashboardStats {
  total_tasks: number
  pending_tasks: number
  in_progress_tasks: number
  completed_today: number
  total_technicians: number
  active_technicians: number
  total_apparatuses: number
  operational_apparatuses: number
  maintenance_apparatuses: number
  out_of_order_apparatuses: number
  avg_completion_time_hours: number
  avg_technician_rating: number
}

export interface TaskFilters {
  page?: number
  page_size?: number
  status?: TaskStatus[]
  type?: TaskType[]
  priority?: TaskPriority[]
  technician_id?: string
  apparatus_id?: string
  date_from?: string
  date_to?: string
  search?: string
}

export interface TechnicianFilters {
  page?: number
  page_size?: number
  is_active?: boolean
  search?: string
  min_rating?: number
}

export interface ApparatusFilters {
  page?: number
  page_size?: number
  status?: ApparatusStatus[]
  search?: string
  needs_maintenance?: boolean
}

export interface AcceptTaskRequest {
  technician_id: string
  estimated_duration_minutes?: number
}

export interface RejectTaskRequest {
  reason: string
}

export interface TaskDetailResponse {
  task: Task
  photos: TaskPhoto[]
  presigned_urls: Record<string, string>
}