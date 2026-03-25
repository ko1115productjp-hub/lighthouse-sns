/**
 * Main App Component with Routing
 */

import { useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { useAuthStore } from './store/authStore';
import { Layout } from './components/Layout';
import { Login } from './pages/Login';
import { Register } from './pages/Register';
import { Timeline } from './pages/Timeline';
import { CreateOutput } from './pages/CreateOutput';
import { EditOutput } from './pages/EditOutput';
import { OutputDetail } from './pages/OutputDetail';
import { UserProfile } from './pages/UserProfile';
import { EditProfile } from './pages/EditProfile';
import { OAuthCallback } from './pages/OAuthCallback';

// Protected Route Component
function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading } = useAuthStore();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return isAuthenticated ? <>{children}</> : <Navigate to="/login" replace />;
}

// Home/Landing Page
function Home() {
  const { isAuthenticated } = useAuthStore();

  if (isAuthenticated) {
    return <Navigate to="/timeline" replace />;
  }

  return (
    <div className="min-h-[calc(100vh-16rem)] flex items-center justify-center">
      <div className="max-w-4xl mx-auto text-center">
        <h1 className="text-5xl font-bold text-gray-900 mb-6">SNS Platform</h1>
        <p className="text-xl text-gray-600 mb-8">
          Academic citation-based social network for scholarly discussions
        </p>
        <div className="flex justify-center space-x-4">
          <a
            href="/register"
            className="bg-blue-600 text-white px-8 py-3 rounded-lg font-semibold hover:bg-blue-700 transition"
          >
            Get Started
          </a>
          <a
            href="/login"
            className="bg-white text-blue-600 border-2 border-blue-600 px-8 py-3 rounded-lg font-semibold hover:bg-blue-50 transition"
          >
            Sign In
          </a>
        </div>

        {/* Features */}
        <div className="mt-16 grid grid-cols-1 md:grid-cols-3 gap-8">
          <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
            <div className="text-3xl mb-4">📚</div>
            <h3 className="text-lg font-semibold mb-2">Academic Citations</h3>
            <p className="text-gray-600 text-sm">
              Reference and cite other works with structured citation types
            </p>
          </div>
          <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
            <div className="text-3xl mb-4">🔗</div>
            <h3 className="text-lg font-semibold mb-2">Immutable History</h3>
            <p className="text-gray-600 text-sm">
              Every edit is tracked with cryptographic hash chains
            </p>
          </div>
          <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
            <div className="text-3xl mb-4">✨</div>
            <h3 className="text-lg font-semibold mb-2">AI Moderation</h3>
            <p className="text-gray-600 text-sm">
              Novelty-based classification for quality content discovery
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

function App() {
  const { checkAuth } = useAuthStore();

  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Home />} />
          <Route path="login" element={<Login />} />
          <Route path="register" element={<Register />} />
          <Route path="auth/callback" element={<OAuthCallback />} />
          <Route
            path="timeline"
            element={
              <ProtectedRoute>
                <Timeline />
              </ProtectedRoute>
            }
          />
          <Route
            path="create"
            element={
              <ProtectedRoute>
                <CreateOutput />
              </ProtectedRoute>
            }
          />
          <Route
            path="output/:id"
            element={
              <ProtectedRoute>
                <OutputDetail />
              </ProtectedRoute>
            }
          />
          <Route
            path="output/:id/edit"
            element={
              <ProtectedRoute>
                <EditOutput />
              </ProtectedRoute>
            }
          />
          <Route
            path="profile/:username"
            element={
              <ProtectedRoute>
                <UserProfile />
              </ProtectedRoute>
            }
          />
          <Route
            path="settings/profile"
            element={
              <ProtectedRoute>
                <EditProfile />
              </ProtectedRoute>
            }
          />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
