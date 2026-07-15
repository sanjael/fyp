import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Login from './pages/Login';
import Register from './pages/Register';
import SidebarLayout from './components/SidebarLayout';
import Dashboard from './pages/Dashboard';
import Query from './pages/Query';
import Documents from './pages/Documents';

// Simple auth wrapper
const ProtectedRoute = ({ children }: { children: React.ReactNode }) => {
  const token = localStorage.getItem('token');
  if (!token) {
    // For demo purposes, if there's no token, we still let them in to see the UI.
    // In production, uncomment the next line:
    // return <Navigate to="/login" replace />;
  }
  return <>{children}</>;
};

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        
        {/* Protected Routes wrapped in SidebarLayout */}
        <Route path="/" element={
          <ProtectedRoute>
            <SidebarLayout />
          </ProtectedRoute>
        }>
          <Route index element={<Dashboard />} />
          <Route path="query" element={<Query />} />
          <Route path="documents" element={<Documents />} />
          <Route path="settings" element={<Dashboard />} /> {/* Dummy mapping for now */}
        </Route>

        <Route path="*" element={<Navigate to="/" />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
