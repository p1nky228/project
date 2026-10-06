import { QueryClient } from '@tanstack/react-query'

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5,
      gcTime: 1000 * 60 * 30,
      retry: (failureCount, error: any) => {
        if (error?.response?.status === 401 || error?.response?.status === 403) {
          return false
        }
        return failureCount < 3
      },
      refetchOnWindowFocus: false,
    },
    mutations: {
      retry: 0,
    },
  },
})

export const queryKeys = {
  tasks: {
    all: ['tasks'] as const,
    lists: () => [...queryKeys.tasks.all, 'list'] as const,
    list: (filters: Record<string, any>) => [...queryKeys.tasks.lists(), filters] as const,
    details: () => [...queryKeys.tasks.all, 'detail'] as const,
    detail: (id: string) => [...queryKeys.tasks.details(), id] as const,
  },
  technicians: {
    all: ['technicians'] as const,
    lists: () => [...queryKeys.technicians.all, 'list'] as const,
    list: (filters: Record<string, any>) => [...queryKeys.technicians.lists(), filters] as const,
    details: () => [...queryKeys.technicians.all, 'detail'] as const,
    detail: (id: string) => [...queryKeys.technicians.details(), id] as const,
  },
  apparatuses: {
    all: ['apparatuses'] as const,
    lists: () => [...queryKeys.apparatuses.all, 'list'] as const,
    list: (filters: Record<string, any>) => [...queryKeys.apparatuses.lists(), filters] as const,
    details: () => [...queryKeys.apparatuses.all, 'detail'] as const,
    detail: (id: string) => [...queryKeys.apparatuses.details(), id] as const,
  },
  stats: {
    all: ['stats'] as const,
    dashboard: () => [...queryKeys.stats.all, 'dashboard'] as const,
  },
} as const