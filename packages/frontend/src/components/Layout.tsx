/**
 * Main Layout Component
 */

import { Link, Outlet, useNavigate } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';

export function Layout() {
  const { user, isAuthenticated, logout } = useAuthStore();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            {/* Logo */}
            <Link to="/" className="flex items-center space-x-2">
              <img src="/lighthouse-logo.png" alt="Lighthouse" className="h-16 w-auto object-contain" />
              <span className="text-2xl font-bold text-gray-900">Lighthouse</span>
            </Link>

            {/* Navigation */}
            <nav className="flex items-center space-x-4">
              {isAuthenticated && user ? (
                <>
                  <Link
                    to="/timeline"
                    className="text-gray-700 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium"
                  >
                    タイムライン
                  </Link>
                  <Link
                    to="/create"
                    className="text-gray-700 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium"
                  >
                    投稿
                  </Link>
                  <Link
                    to={`/profile/${user.username}`}
                    className="text-gray-700 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium"
                  >
                    プロフィール
                  </Link>
                  <button
                    onClick={handleLogout}
                    className="text-gray-700 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium"
                  >
                    ログアウト
                  </button>
                  <div className="flex items-center space-x-2 pl-4 border-l border-gray-300">
                    <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center text-white font-semibold">
                      {user.display_name?.charAt(0).toUpperCase() || 'U'}
                    </div>
                    <span className="text-sm font-medium text-gray-700">{user.username}</span>
                  </div>
                </>
              ) : (
                <>
                  <Link
                    to="/login"
                    className="text-gray-700 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium"
                  >
                    ログイン
                  </Link>
                  <Link
                    to="/register"
                    className="bg-blue-600 text-white hover:bg-blue-700 px-4 py-2 rounded-md text-sm font-medium"
                  >
                    新規登録
                  </Link>
                </>
              )}
            </nav>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Outlet />
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 mt-auto">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <p className="text-center text-sm text-gray-500">
            © 2026 Lighthouse - Knowledge Archive for Humanity
          </p>
        </div>
      </footer>
    </div>
  );
}
