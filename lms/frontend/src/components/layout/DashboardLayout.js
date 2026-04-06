/**
 * DashboardLayout — shared layout for student, faculty and admin.
 * Contains a collapsible sidebar and a top header.
 */

import React, { useState } from 'react';
import { Outlet, NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import toast from 'react-hot-toast';

// Nav items per role
const NAV = {
  STUDENT: [
    { to: '/student', label: 'Dashboard', icon: '🏠', end: true },
    { to: '/student/enrollments', label: 'My Courses', icon: '📚' },
    { to: '/student/attendance', label: 'Attendance', icon: '✅' },
    { to: '/student/marks', label: 'Marks & Grades', icon: '📊' },
    { to: '/student/fees', label: 'Fee Payment', icon: '💳' },
    { to: '/student/profile', label: 'My Profile', icon: '👤' },
  ],
  FACULTY: [
    { to: '/faculty', label: 'Dashboard', icon: '🏠', end: true },
    { to: '/faculty/attendance', label: 'Mark Attendance', icon: '✅' },
    { to: '/faculty/marks', label: 'Enter Marks', icon: '📊' },
  ],
  ADMIN: [
    { to: '/admin', label: 'Dashboard', icon: '🏠', end: true },
    { to: '/admin/students', label: 'Students', icon: '🎓' },
    { to: '/admin/faculty', label: 'Faculty', icon: '👨‍🏫' },
    { to: '/admin/courses', label: 'Courses', icon: '📚' },
    { to: '/admin/fees', label: 'Fee Management', icon: '💰' },
    { to: '/admin/announcements', label: 'Announcements', icon: '📢' },
  ],
};

const ROLE_COLORS = {
  STUDENT: '#2563eb',
  FACULTY: '#7c3aed',
  ADMIN: '#059669',
};

export default function DashboardLayout({ role }) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [sidebarOpen, setSidebarOpen] = useState(true);

  const handleLogout = () => {
    logout();
    toast.success('Logged out successfully');
    navigate('/login');
  };

  const navItems = NAV[role] || [];
  const accentColor = ROLE_COLORS[role] || '#2563eb';

  return (
    <div style={{ display: 'flex', minHeight: '100vh', background: 'var(--bg)' }}>
      {/* ─── Sidebar ─── */}
      <aside style={{
        width: sidebarOpen ? 'var(--sidebar-width)' : '64px',
        background: '#fff',
        borderRight: '1px solid var(--border)',
        display: 'flex',
        flexDirection: 'column',
        transition: 'width 0.2s ease',
        overflow: 'hidden',
        flexShrink: 0,
        position: 'sticky',
        top: 0,
        height: '100vh',
      }}>
        {/* Logo */}
        <div style={{ padding: '1.25rem 1rem', borderBottom: '1px solid var(--border)', display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <div style={{ width: 36, height: 36, borderRadius: 8, background: accentColor, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'white', fontWeight: 800, fontSize: '1rem', flexShrink: 0 }}>
            L
          </div>
          {sidebarOpen && (
            <div>
              <div style={{ fontFamily: 'Sora, sans-serif', fontWeight: 700, fontSize: '0.9rem' }}>Landmine Soft</div>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>{role}</div>
            </div>
          )}
        </div>

        {/* Nav links */}
        <nav style={{ flex: 1, padding: '0.75rem 0.5rem', overflowY: 'auto' }}>
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              style={({ isActive }) => ({
                display: 'flex',
                alignItems: 'center',
                gap: '0.75rem',
                padding: '0.625rem 0.75rem',
                borderRadius: 8,
                textDecoration: 'none',
                fontSize: '0.875rem',
                fontWeight: isActive ? 600 : 400,
                color: isActive ? accentColor : 'var(--text)',
                background: isActive ? (role === 'STUDENT' ? 'var(--primary-light)' : role === 'FACULTY' ? '#f5f3ff' : '#d1fae5') : 'transparent',
                marginBottom: '2px',
                whiteSpace: 'nowrap',
                transition: 'all 0.1s',
              })}
            >
              <span style={{ fontSize: '1.1rem', flexShrink: 0 }}>{item.icon}</span>
              {sidebarOpen && item.label}
            </NavLink>
          ))}
        </nav>

        {/* User info at bottom */}
        <div style={{ padding: '0.75rem', borderTop: '1px solid var(--border)' }}>
          {sidebarOpen && (
            <div style={{ padding: '0.75rem', background: 'var(--bg)', borderRadius: 8, marginBottom: '0.5rem' }}>
              <div style={{ fontSize: '0.875rem', fontWeight: 600, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{user?.name}</div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{user?.email}</div>
            </div>
          )}
          <button onClick={handleLogout} className="btn btn-secondary btn-full btn-sm">
            🚪 {sidebarOpen && 'Logout'}
          </button>
        </div>
      </aside>

      {/* ─── Main area ─── */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', minWidth: 0 }}>
        {/* Header */}
        <header style={{
          height: 'var(--header-height)',
          background: '#fff',
          borderBottom: '1px solid var(--border)',
          display: 'flex',
          alignItems: 'center',
          padding: '0 1.5rem',
          gap: '1rem',
          position: 'sticky',
          top: 0,
          zIndex: 100,
        }}>
          <button
            onClick={() => setSidebarOpen(v => !v)}
            style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: '1.25rem', padding: '4px', borderRadius: 6 }}
          >
            ☰
          </button>
          <div style={{ flex: 1 }} />
          <span style={{ fontSize: '0.875rem', color: 'var(--text-muted)' }}>
            Welcome back, <strong>{user?.name?.split(' ')[0]}</strong>
          </span>
          <div style={{
            width: 36, height: 36, borderRadius: '50%',
            background: accentColor, color: 'white',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontWeight: 700, fontSize: '0.9rem',
          }}>
            {user?.name?.[0]?.toUpperCase()}
          </div>
        </header>

        {/* Page content */}
        <main style={{ flex: 1, padding: '1.5rem', overflowY: 'auto' }}>
          <Outlet />
        </main>
      </div>
    </div>
  );
}
