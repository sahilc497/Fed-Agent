import React, { createContext, useContext, useState, useEffect } from 'react';
import { useAuth } from './AuthContext';

export type DepartmentTheme = 'admin' | 'sales' | 'hr' | 'finance' | 'operations';

export interface ThemeMeta {
  id: DepartmentTheme;
  name: string;
  departmentName: string;
  primaryColor: string;
  badgeLabel: string;
  description: string;
  accentGradient: string;
  iconName: string;
}

export const THEME_REGISTRY: Record<DepartmentTheme, ThemeMeta> = {
  admin: {
    id: 'admin',
    name: 'Executive Admin',
    departmentName: 'Enterprise Administration & Governance',
    primaryColor: '#6366f1',
    badgeLabel: 'Royal Indigo',
    description: 'Executive cross-mesh oversight and security policy administration',
    accentGradient: 'linear-gradient(135deg, #6366f1 0%, #4f46e5 100%)',
    iconName: 'ShieldCheck'
  },
  sales: {
    id: 'sales',
    name: 'Sales Agent',
    departmentName: 'Commercial Growth & Revenue Pipeline',
    primaryColor: '#2563eb',
    badgeLabel: 'Cobalt Blue',
    description: 'Enterprise opportunities, BANT qualification, and deal closing',
    accentGradient: 'linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%)',
    iconName: 'TrendingUp'
  },
  hr: {
    id: 'hr',
    name: 'HR Agent',
    departmentName: 'Human Resources & Talent Management',
    primaryColor: '#059669',
    badgeLabel: 'Emerald Mint',
    description: 'Workforce records, leave policies, and organizational growth',
    accentGradient: 'linear-gradient(135deg, #059669 0%, #047857 100%)',
    iconName: 'Users'
  },
  finance: {
    id: 'finance',
    name: 'Finance Agent',
    departmentName: 'Financial Control, Treasury & Invoicing',
    primaryColor: '#d97706',
    badgeLabel: 'Amber Gold',
    description: 'Corporate invoices, wire authorizations, and capital allocation',
    accentGradient: 'linear-gradient(135deg, #d97706 0%, #b45309 100%)',
    iconName: 'CreditCard'
  },
  operations: {
    id: 'operations',
    name: 'Operations Agent',
    departmentName: 'Supply Chain, Warehouse & Logistics',
    primaryColor: '#ea580c',
    badgeLabel: 'Industrial Tangerine',
    description: 'Warehouse SKUs, purchase orders, and fulfillment pipelines',
    accentGradient: 'linear-gradient(135deg, #ea580c 0%, #c2410c 100%)',
    iconName: 'Package'
  }
};

interface ThemeContextType {
  theme: DepartmentTheme;
  themeMeta: ThemeMeta;
  setTheme: (theme: DepartmentTheme) => void;
  resetToUserDefault: () => void;
  isCustomPreview: boolean;
  availableThemes: ThemeMeta[];
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

export const ThemeProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user } = useAuth();

  const getDefaultThemeForUser = (): DepartmentTheme => {
    if (!user) return 'admin';
    if (user.role === 'admin') return 'admin';
    switch (user.department_id) {
      case 1: return 'sales';
      case 2: return 'hr';
      case 3: return 'finance';
      case 4: return 'operations';
      default: return 'sales';
    }
  };

  const [activeTheme, setActiveTheme] = useState<DepartmentTheme>(getDefaultThemeForUser);
  const [customOverride, setCustomOverride] = useState<DepartmentTheme | null>(null);

  // Synchronize when authenticated user changes
  useEffect(() => {
    const defaultTheme = getDefaultThemeForUser();
    if (user?.role === 'admin') {
      // Check for saved preview preference in session
      const saved = sessionStorage.getItem('mesh_admin_theme_preview') as DepartmentTheme | null;
      if (saved && THEME_REGISTRY[saved]) {
        setActiveTheme(saved);
        setCustomOverride(saved);
        return;
      }
    }
    setActiveTheme(defaultTheme);
    setCustomOverride(null);
  }, [user?.id, user?.department_id, user?.role]);

  // Apply data-theme attribute on root and class on body for instant CSS styling
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', activeTheme);
    document.body.className = `theme-${activeTheme}`;
  }, [activeTheme]);

  const setTheme = (theme: DepartmentTheme) => {
    if (THEME_REGISTRY[theme]) {
      setActiveTheme(theme);
      setCustomOverride(theme);
      if (user?.role === 'admin') {
        sessionStorage.setItem('mesh_admin_theme_preview', theme);
      }
    }
  };

  const resetToUserDefault = () => {
    const defaultTheme = getDefaultThemeForUser();
    setActiveTheme(defaultTheme);
    setCustomOverride(null);
    sessionStorage.removeItem('mesh_admin_theme_preview');
  };

  const isCustomPreview = Boolean(customOverride && customOverride !== getDefaultThemeForUser());

  return (
    <ThemeContext.Provider
      value={{
        theme: activeTheme,
        themeMeta: THEME_REGISTRY[activeTheme] || THEME_REGISTRY.admin,
        setTheme,
        resetToUserDefault,
        isCustomPreview,
        availableThemes: Object.values(THEME_REGISTRY)
      }}
    >
      {children}
    </ThemeContext.Provider>
  );
};

export const useTheme = () => {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
};
