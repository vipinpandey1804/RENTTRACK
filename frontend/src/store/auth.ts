import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import axios from 'axios';

interface AuthState {
  accessToken: string | null;
  refreshToken: string | null;
  user: { id: string; email: string } | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  refresh: () => Promise<string | null>;
}

const API = import.meta.env.VITE_API_URL || '/api/v1';

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      accessToken: null,
      refreshToken: null,
      user: null,

      login: async (email, password) => {
        const { data } = await axios.post(`${API}/auth/login/`, { email, password });
        set({
          accessToken: data.access,
          refreshToken: data.refresh,
        });
      },

      logout: () => {
        set({ accessToken: null, refreshToken: null, user: null });
      },

      refresh: async () => {
        const refreshToken = get().refreshToken;
        if (!refreshToken) return null;
        try {
          const { data } = await axios.post(`${API}/auth/refresh/`, {
            refresh: refreshToken,
          });
          set({ accessToken: data.access });
          return data.access;
        } catch {
          set({ accessToken: null, refreshToken: null });
          return null;
        }
      },
    }),
    { name: 'renttrack-auth' },
  ),
);
