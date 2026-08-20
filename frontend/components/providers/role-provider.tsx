'use client';

import * as React from 'react';
import { currentUser, users } from '@/lib/mock-data';
import type { Role, User } from '@/lib/types';

interface RoleContextValue {
  user: User;
  role: Role;
  switchRole: (role: Role) => void;
  users: User[];
}

const RoleContext = React.createContext<RoleContextValue | undefined>(undefined);

export function RoleProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = React.useState<User>(currentUser);

  const switchRole = React.useCallback((role: Role) => {
    const targetUser = users.find((u) => u.role === role && u.is_active) ?? currentUser;
    setUser(targetUser);
  }, []);

  return (
    <RoleContext.Provider value={{ user, role: user.role, switchRole, users }}>
      {children}
    </RoleContext.Provider>
  );
}

export function useRole() {
  const context = React.useContext(RoleContext);
  if (!context) {
    throw new Error('useRole must be used within RoleProvider');
  }
  return context;
}
