'use client';

import * as React from 'react';
import { useQuery } from '@tanstack/react-query';
import { apiFetch } from '@/lib/api';
import { authUtil, User } from '@/lib/auth';
import { ROLE_PERMISSIONS, Permission, hasPermission } from '@/lib/permissions';

interface AuthContextValue {
  user: User | null;
  role: string | null;
  permissions: Permission[];
  isAuthenticated: boolean;
  isLoading: boolean;
  hasPermission: (permission: Permission) => boolean;
  logout: () => void;
}

const AuthContext = React.createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [token, setToken] = React.useState<string | null>(null);
  const [isInitialized, setIsInitialized] = React.useState(false);

  React.useEffect(() => {
    setToken(authUtil.getToken());
    setIsInitialized(true);
  }, []);

  const { data: user, isLoading: isQueryLoading } = useQuery<User>({
    queryKey: ['auth', 'me'],
    queryFn: () => apiFetch('/api/v1/auth/me'),
    enabled: !!token,
    retry: false,
  });

  const permissions = user?.role ? ROLE_PERMISSIONS[user.role] || [] : [];
  const isAuthenticated = !!user;
  
  // App is loading if we haven't checked localStorage yet, OR if we have a token and are fetching the user profile
  const isLoading = !isInitialized || (!!token && isQueryLoading);

  const checkPermission = React.useCallback(
    (permission: Permission) => {
      return hasPermission(permissions, permission);
    },
    [permissions]
  );

  return (
    <AuthContext.Provider
      value={{
        user: user || null,
        role: user?.role || null,
        permissions,
        isAuthenticated,
        isLoading,
        hasPermission: checkPermission,
        logout: authUtil.logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = React.useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
}
