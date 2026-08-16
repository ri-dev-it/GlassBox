import { Routes, Route } from 'react-router-dom';
import MainLayout from '../layouts/MainLayout';
import ProtectedRoute from '../components/common/ProtectedRoute';
import Landing from '../pages/Landing/Landing';
import Login from '../pages/Login/Login';
import GoogleCallback from '../pages/Login/GoogleCallback';
import Register from '../pages/Register/Register';
import Application from '../pages/Application/Application';
import Results from '../pages/Results/Results';
import History from '../pages/History/History';
import Profile from '../pages/Profile/Profile';
import Admin from '../pages/Admin/Admin';
import Status from '../pages/Status/Status';
import Insights from '../pages/Insights/Insights';
import Settings from '../pages/Settings/Settings';
import About from '../pages/About/About';
import Placeholder from '../pages/Placeholder/Placeholder';

export default function AppRoutes() {
  return (
    <Routes>
      <Route element={<MainLayout />}>
        <Route path="/" element={<Landing />} />
        <Route path="/login" element={<Login />} />
        <Route path="/auth/google/callback" element={<GoogleCallback />} />
        <Route path="/register" element={<Register />} />
        <Route path="/apply" element={<ProtectedRoute><Application /></ProtectedRoute>} />
        <Route path="/results/:id" element={<ProtectedRoute><Results /></ProtectedRoute>} />
        <Route path="/history" element={<ProtectedRoute><History /></ProtectedRoute>} />
        <Route path="/profile" element={<ProtectedRoute><Profile /></ProtectedRoute>} />
        <Route path="/status" element={<ProtectedRoute><Status /></ProtectedRoute>} />
        <Route path="/insights" element={<ProtectedRoute><Insights /></ProtectedRoute>} />
        <Route path="/settings" element={<ProtectedRoute><Settings /></ProtectedRoute>} />
        <Route path="/about" element={<ProtectedRoute><About /></ProtectedRoute>} />
        <Route path="/analytics" element={<ProtectedRoute><Placeholder title="Credit Analytics" description="Credit analytics will use recorded applications and the real model metadata." /></ProtectedRoute>} />
        <Route path="/risk-analysis" element={<ProtectedRoute><Placeholder title="Risk Analysis" description="Risk analysis will summarize the AI-derived risk levels from stored applications." /></ProtectedRoute>} />
        <Route path="/reports" element={<ProtectedRoute><Placeholder title="Reports" description="Reports are available from each completed assessment to ensure they contain real prediction and explanation data." /></ProtectedRoute>} />
        <Route
          path="/admin"
          element={
            <ProtectedRoute allowedRoles={['admin', 'loan_officer']}>
              <Admin />
            </ProtectedRoute>
          }
        />
      </Route>
    </Routes>
  );
}
