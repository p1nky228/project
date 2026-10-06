import { useQuery } from '@tanstack/react-query'
import api from '../api/axios'
import { queryKeys } from '../api/queryClient'
import type { Technician, TechnicianFilters } from '../api/types'

export function useTechnicians(filters: TechnicianFilters = {}) {
  return useQuery({
    queryKey: queryKeys.technicians.list(filters),
    queryFn: async () => {
      const params = new URLSearchParams()
      Object.entries(filters).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          params.set(key, String(value))
        }
      })
      const response = await api.get<{ items: Technician[]; total: number; page: number; page_size: number; pages: number }>(
        `/admin/technicians?${params.toString()}`
      )
      return response.data
    },
  })
}

export function useTechnician(id: string) {
  return useQuery({
    queryKey: queryKeys.technicians.detail(id),
    queryFn: async () => {
      const response = await api.get<Technician>(`/admin/technicians/${id}`)
      return response.data
    },
    enabled: !!id,
  })
}