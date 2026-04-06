/**
 * App.js — Main router.
 * Routes are protected by role. Unauthenticated users are sent to /login.
 */

import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { AuthProvider, useAuth } from './context/AuthContext';

// Auth pages
import LoginPage from './pages/auth/LoginPage';
import RegisterPage from './pages/auth/RegisterPage';
import ForgotPasswordPage from './pages/auth/ForgotPasswordPage';
import ResetPasswordPage from './pages/auth/ResetPasswordPage';

// Student pages
import StudentDashboard from './pages/student/StudentDashboard';
import StudentAttendance from './pages/student/StudentAttendance';
import StudentMarks from './pages/student/StudentMarks';
import StudentFees from './pages/student/StudentFees';
import StudentEnrollments from './pages/student/StudentEnrollments';
import StudentProfile from './pages/student/StudentProfile';

// Faculty pages
import FacultyDashboard from './pages/faculty/FacultyDashboard';
import FacultyAttendance from './pages/faculty/FacultyAttendance';
import FacultyMarks from './pages/faculty/FacultyMarks';

// Admin pages
import AdminDashboard from './pages/admin/AdminDashboard';
import AdminStudents from './pages/admin/AdminStudents';
import AdminFaculty from './pages/admin/AdminFaculty';
import AdminCourses from './pages/admin/AdminCourses';
import AdminFees from './pages/admin/AdminFees';
import AdminAnnouncements from './pages/admin/AdminAnnouncements';

// Layout
import DashboardLayout from './components/layout/DashboardLayout';

// Protected route wrapper
function ProtectedRoute({ children, allowedRole }) {
  const { user, loading } = useAuth();
  if (loading) return <div className="loading-screen">Loading...</div>;
  if (!user) return <Navigate to="/login" replace />;
  if (allowedRole && user.role !== allowedRole) return <Navigate to="/login" replace />;
  return children;
}

function AppRoutes() {
  const { user } = useAuth();

  return (
    <Routes>
      {/* Public routes */}
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route path="/forgot-password" element={<ForgotPasswordPage />} />
      <Route path="/reset-password" element={<ResetPasswordPage />} />

      {/* Student routes */}
      <Route path="/student" element={
        <ProtectedRoute allowedRole="STUDENT">
          <DashboardLayout role="STUDENT" />
        </ProtectedRoute>
      }>
        <Route index element={<StudentDashboard />} />
        <Route path="attendance" element={<StudentAttendance />} />
        <Route path="marks" element={<StudentMarks />} />
        <Route path="fees" element={<StudentFees />} />
        <Route path="enrollments" element={<StudentEnrollments />} />
        <Route path="profile" element={<StudentProfile />} />
      </Route>

      {/* Faculty routes */}
      <Route path="/faculty" element={
        <ProtectedRoute allowedRole="FACULTY">
          <DashboardLayout role="FACULTY" />
        </ProtectedRoute>
      }>
        <Route index element={<FacultyDashboard />} />
        <Route path="attendance" element={<FacultyAttendance />} />
        <Route path="marks" element={<FacultyMarks />} />
      </Route>

      {/* Admin routes */}
      <Route path="/admin" element={
        <ProtectedRoute allowedRole="ADMIN">
          <DashboardLayout role="ADMIN" />
        </ProtectedRoute>
      }>
        <Route index element={<AdminDashboard />} />
        <Route path="students" element={<AdminStudents />} />
        <Route path="faculty" element={<AdminFaculty />} />
        <Route path="courses" element={<AdminCourses />} />
        <Route path="fees" element={<AdminFees />} />
        <Route path="announcements" element={<AdminAnnouncements />} />
      </Route>

      {/* Default redirect based on role */}
      <Route path="/" element={
        user ? (
          user.role === 'STUDENT' ? <Navigate to="/student" replace /> :
          user.role === 'FACULTY' ? <Navigate to="/faculty" replace /> :
          <Navigate to="/admin" replace />
        ) : (
          <Navigate to="/login" replace />
        )
      } />

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Toaster position="top-right" toastOptions={{ duration: 3000 }} />
        <AppRoutes />
      </BrowserRouter>
    </AuthProvider>
  );
}
