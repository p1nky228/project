import { useQuery } from '@tanstack/react-query'
import api from '../api/axios'
import { queryKeys } from '../api/queryClient'
import type { DashboardStats } from '../api/types'

export function useStats() {
  return useQuery({
    queryKey: queryKeys.stats.dashboard(),
    queryFn: async () => {
      const response = await api.get<DashboardStats>('/admin/stats')
      return response.data
    },
    refetchInterval: 1000 * 60 * 5,
  })
}