import { apiFetch } from './api';
import { Permission, PERMISSIONS } from './permissions';

export interface User {
  id: string;
  email: string;
  name: string;
  role: string;
  company_id: string;
  is_active: boolean;
}

export interface AuthSession {
  user: User;
  token: string;
}

export const authUtil = {
  getToken: () => {
    if (typeof window === 'undefined') return null;
    return localStorage.getItem('siteSyncToken');
  },
  
  setToken: (token: string) => {
    if (typeof window === 'undefined') return;
    localStorage.setItem('siteSyncToken', token);
  },
  
  clearToken: () => {
    if (typeof window === 'undefined') return;
    localStorage.removeItem('siteSyncToken');
  },

  logout: () => {
    authUtil.clearToken();
    if (typeof window !== 'undefined') {
      window.location.href = '/login';
    }
  }
};
