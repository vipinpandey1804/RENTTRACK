import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import axios from 'axios';
import type { User } from '@/types';

interface AuthState {
  accessToken: string | null;
  refreshToken: string | null;
  user: User | null;
  login: (email: string, password: string) => Promise<void>;
  signup: (data: SignupData) => Promise<void>;
  logout: () => Promise<void>;
  refresh: () => Promise<string | null>;
  fetchMe: () => Promise<void>;
  setUser: (user: User) => void;
}

interface SignupData {
  email: string;
  password: string;
  first_name: string;
  last_name?: string;
  org_name: string;
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
        set({ accessToken: data.access, refreshToken: data.refresh });
        // Fetch user profile after login
        try {
          const me = await axios.get(`${API}/auth/me/`, {
            headers: { Authorization: `Bearer ${data.access}` },
          });
          set({ user: me.data });
        } catch {
          // Non-fatal — user will be fetched on next page load
        }
      },

      signup: async (signupData) => {
        const { data } = await axios.post(`${API}/auth/signup/`, signupData);
        set({ accessToken: data.access, refreshToken: data.refresh, user: data.user });
      },

      logout: async () => {
        const refreshToken = get().refreshToken;
        const accessToken = get().accessToken;
        if (refreshToken && accessToken) {
          try {
            await axios.post(
              `${API}/auth/logout/`,
              { refresh: refreshToken },
              { headers: { Authorization: `Bearer ${accessToken}` } },
            );
          } catch {
            // Blacklist failure is non-fatal
          }
        }
        set({ accessToken: null, refreshToken: null, user: null });
      },

      refresh: async () => {
        const refreshToken = get().refreshToken;
        if (!refreshToken) return null;
        try {
          const { data } = await axios.post(`${API}/auth/refresh/`, { refresh: refreshToken });
          set({ accessToken: data.access });
          return data.access;
        } catch {
          set({ accessToken: null, refreshToken: null, user: null });
          return null;
        }
      },

      fetchMe: async () => {
        const token = get().accessToken;
        if (!token) return;
        try {
          const { data } = await axios.get(`${API}/auth/me/`, {
            headers: { Authorization: `Bearer ${token}` },
          });
          set({ user: data });
        } catch {
          // Ignore
        }
      },

      setUser: (user) => set({ user }),
    }),
    { name: 'renttrack-auth' },
  ),
);
