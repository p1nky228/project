import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import api from '../api/axios'
import { queryKeys } from '../api/queryClient'
import type { Task, TaskFilters, AcceptTaskRequest, RejectTaskRequest, TaskDetailResponse } from '../api/types'

export function useTasks(filters: TaskFilters = {}) {
  return useQuery({
    queryKey: queryKeys.tasks.list(filters),
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
      const response = await api.get<{ items: Task[]; total: number; page: number; page_size: number; pages: number }>(
        `/admin/tasks?${params.toString()}`
      )
      return response.data
    },
  })
}

export function useTask(id: string) {
  return useQuery({
    queryKey: queryKeys.tasks.detail(id),
    queryFn: async () => {
      const response = await api.get<TaskDetailResponse>(`/admin/tasks/${id}`)
      return response.data
    },
    enabled: !!id,
  })
}

export function useAcceptTask() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: AcceptTaskRequest }) => {
      const response = await api.post(`/admin/tasks/${id}/accept`, data)
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.tasks.all })
      queryClient.invalidateQueries({ queryKey: queryKeys.stats.all })
    },
  })
}

export function useRejectTask() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: RejectTaskRequest }) => {
      const response = await api.post(`/admin/tasks/${id}/reject`, data)
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.tasks.all })
      queryClient.invalidateQueries({ queryKey: queryKeys.stats.all })
    },
  })
}