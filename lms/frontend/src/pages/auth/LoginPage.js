/**
 * LoginPage — single page with tabs for Student / Faculty / Admin login.
 */

import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';
import { authAPI } from '../../api';
import { useAuth } from '../../context/AuthContext';

const TABS = ['Student', 'Faculty', 'Admin'];
const LOGIN_FNS = {
  Student: authAPI.studentLogin,
  Faculty: authAPI.facultyLogin,
  Admin: authAPI.adminLogin,
};
const REDIRECT = {
  STUDENT: '/student',
  FACULTY: '/faculty',
  ADMIN: '/admin',
};

export default function LoginPage() {
  const [tab, setTab] = useState('Student');
  const [form, setForm] = useState({ email: '', password: '' });
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleChange = (e) => setForm(prev => ({ ...prev, [e.target.name]: e.target.value }));

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.email || !form.password) {
      toast.error('Please fill in all fields');
      return;
    }
    setLoading(true);
    try {
      const res = await LOGIN_FNS[tab](form);
      const data = res.data;
      login({ id: data.userId, name: data.name, email: data.email, role: data.role }, data.token, data.refresh);
      toast.success(`Welcome back, ${data.name}!`);
      navigate(REDIRECT[data.role] || '/');
    } catch (err) {
      const msg = err.response?.data?.non_field_errors?.[0]
        || err.response?.data?.detail
        || 'Invalid credentials. Please try again.';
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-card">
        <div className="auth-logo">
          <h1>🎓 LMS Portal</h1>
          <p>Landmine Soft College Management System</p>
        </div>

        {/* Role tabs */}
        <div className="auth-tabs">
          {TABS.map(t => (
            <button key={t} className={`auth-tab ${tab === t ? 'active' : ''}`} onClick={() => setTab(t)}>
              {t === 'Student' ? '🎓' : t === 'Faculty' ? '👨‍🏫' : '🔑'} {t}
            </button>
          ))}
        </div>

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label className="form-label">Email Address</label>
            <input
              className="form-input"
              type="email"
              name="email"
              placeholder={`${tab.toLowerCase()}@college.edu`}
              value={form.email}
              onChange={handleChange}
              autoComplete="email"
            />
          </div>
          <div className="form-group">
            <label className="form-label">Password</label>
            <input
              className="form-input"
              type="password"
              name="password"
              placeholder="••••••••"
              value={form.password}
              onChange={handleChange}
              autoComplete="current-password"
            />
          </div>

          <div style={{ textAlign: 'right', marginBottom: '1.25rem' }}>
            <Link to="/forgot-password" style={{ fontSize: '0.875rem', color: 'var(--primary)' }}>
              Forgot password?
            </Link>
          </div>

          <button className="btn btn-primary btn-full" type="submit" disabled={loading}>
            {loading ? <><span className="spinner" style={{ width: 16, height: 16 }} /> Logging in...</> : `Login as ${tab}`}
          </button>
        </form>

        {tab === 'Student' && (
          <p style={{ textAlign: 'center', marginTop: '1.25rem', fontSize: '0.875rem', color: 'var(--text-muted)' }}>
            New student?{' '}
            <Link to="/register" style={{ color: 'var(--primary)', fontWeight: 600 }}>Register here</Link>
          </p>
        )}
      </div>
    </div>
  );
}
