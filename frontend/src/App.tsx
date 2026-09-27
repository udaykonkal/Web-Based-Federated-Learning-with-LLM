import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { ProtectedRoute } from './components/ProtectedRoute';
import { AdminLayout } from './components/AdminLayout';
import { ClientLayout } from './components/ClientLayout';
import { LandingPage } from './pages/LandingPage';
import { AdminLogin } from './pages/admin/AdminLogin';
import { AdminDashboard } from './pages/admin/AdminDashboard';
import { AdminDatasets } from './pages/admin/AdminDatasets';
import { AdminModels } from './pages/admin/AdminModels';
import { AdminExperiments } from './pages/admin/AdminExperiments';
import { AdminMonitoring } from './pages/admin/AdminMonitoring';
import { AdminSecurity } from './pages/admin/AdminSecurity';
import { AdminCommunication } from './pages/admin/AdminCommunication';
import { AdminLLM } from './pages/admin/AdminLLM';
import { AdminAnalytics } from './pages/admin/AdminAnalytics';
import { ClientLogin } from './pages/client/ClientLogin';
import { ClientModels } from './pages/client/ClientModels';
import { ClientWorkspace } from './pages/client/ClientWorkspace';

export function App() {
  return (
    <AuthProvider>
      <Router>
        <Routes>
          {/* Public Routes */}
          <Route path="/" element={<LandingPage />} />
          <Route path="/admin/login" element={<AdminLogin />} />
          <Route path="/client/login" element={<ClientLogin />} />

          {/* Admin Coordinator Protected Routes */}
          <Route
            path="/admin"
            element={
              <ProtectedRoute allowedRole="admin">
                <AdminLayout />
              </ProtectedRoute>
            }
          >
            <Route index element={<Navigate to="/admin/dashboard" replace />} />
            <Route path="dashboard" element={<AdminDashboard />} />
            <Route path="clients" element={<AdminDashboard />} />
            <Route path="datasets" element={<AdminDatasets />} />
            <Route path="models" element={<AdminModels />} />
            <Route path="experiments" element={<AdminExperiments />} />
            <Route path="telemetry" element={<AdminMonitoring />} />
            <Route path="security" element={<AdminSecurity />} />
            <Route path="communication" element={<AdminCommunication />} />
            <Route path="analytics" element={<AdminAnalytics />} />
            <Route path="llm" element={<AdminLLM />} />
          </Route>

          {/* Client Node Protected Routes */}
          <Route
            path="/client"
            element={
              <ProtectedRoute allowedRole="client">
                <ClientLayout />
              </ProtectedRoute>
            }
          >
            <Route index element={<Navigate to="/client/models" replace />} />
            <Route path="models" element={<ClientModels />} />
            <Route path="models/:modelId" element={<ClientWorkspace />} />
            <Route path="profile" element={<ClientModels />} />
          </Route>

          {/* Fallback */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Router>
    </AuthProvider>
  );
}

export default App;
