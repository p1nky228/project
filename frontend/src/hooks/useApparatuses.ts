import { useQuery } from '@tanstack/react-query'
import api from '../api/axios'
import { queryKeys } from '../api/queryClient'
import type { Apparatus, ApparatusFilters } from '../api/types'

export function useApparatuses(filters: ApparatusFilters = {}) {
  return useQuery({
    queryKey: queryKeys.apparatuses.list(filters),
    queryFn: async () => {
      const params = new URLSearchParams()
      Object.entries(filters).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          if (Array.isArray(value)) {
            value.forEach((v) => params.append(key, v))
          } else {
            params.set(key, String(value))
          }
        }
      })
      const response = await api.get<{ items: Apparatus[]; total: number; page: number; page_size: number; pages: number }>(
        `/admin/apparatuses?${params.toString()}`
      )
      return response.data
    },
  })
}

export function useApparatus(id: string) {
  return useQuery({
    queryKey: queryKeys.apparatuses.detail(id),
    queryFn: async () => {
      const response = await api.get<Apparatus>(`/admin/apparatuses/${id}`)
      return response.data
    },
    enabled: !!id,
  })
}