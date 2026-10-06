import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface AuthState {
  adminKey: string | null
  isAuthenticated: boolean
  isLoading: boolean
  setAdminKey: (key: string) => void
  logout: () => void
  checkAuth: () => Promise<void>
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      adminKey: null,
      isAuthenticated: false,
      isLoading: true,

      setAdminKey: (key: string) => {
        localStorage.setItem('admin_key', key)
        set({ adminKey: key, isAuthenticated: true, isLoading: false })
      },

      logout: () => {
        localStorage.removeItem('admin_key')
        set({ adminKey: null, isAuthenticated: false, isLoading: false })
      },

      checkAuth: async () => {
        const key = localStorage.getItem('admin_key')
        if (key) {
          set({ adminKey: key, isAuthenticated: true, isLoading: false })
        } else {
          set({ isLoading: false })
        }
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({ adminKey: state.adminKey }),
    }
  )
)