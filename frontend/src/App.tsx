import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import { ThemeProvider } from './context/ThemeContext';
import { Layout } from './components/Layout';
import { Login } from './pages/Login';
import { Dashboard } from './pages/Dashboard';
import { Chat } from './pages/Chat';
import { DepartmentView } from './pages/DepartmentView';
import { Documents } from './pages/Documents';
import { Approvals } from './pages/Approvals';
import { AuditLogs } from './pages/AuditLogs';
import { UserAdmin } from './pages/UserAdmin';
import { Profile } from './pages/Profile';

const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div style={{
        height: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        backgroundColor: '#0f172a',
        color: '#ffffff',
        fontFamily: 'sans-serif'
      }}>
        <div>Loading Federated Agentic Mesh...</div>
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
};

export const App: React.FC = () => {
  return (
    <AuthProvider>
      <ThemeProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<Login />} />

            <Route
              path="/"
              element={
                <ProtectedRoute>
                  <Layout />
                </ProtectedRoute>
              }
            >
              <Route index element={<Dashboard />} />
              <Route path="chat" element={<Chat />} />
              <Route path="departments" element={<DepartmentView />} />
              <Route path="documents" element={<Documents />} />
              <Route path="approvals" element={<Approvals />} />
              <Route path="audit" element={<AuditLogs />} />
              <Route path="admin/users" element={<UserAdmin />} />
              <Route path="profile" element={<Profile />} />
            </Route>

            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </BrowserRouter>
      </ThemeProvider>
    </AuthProvider>
  );
};

export default App;
