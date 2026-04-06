import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { adminAPI } from '../../api';

export default function AdminDashboard() {
  const [stats, setStats] = useState(null);
  const [announcements, setAnnouncements] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([adminAPI.getDashboard(), adminAPI.getAnnouncements()])
      .then(([sRes, aRes]) => { setStats(sRes.data); setAnnouncements(aRes.data.slice(0, 5)); })
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="loading-center"><div className="spinner" /></div>;

  return (
    <div>
      <div className="page-header"><h2 className="page-title">Admin Dashboard</h2><p className="page-subtitle">System overview</p></div>

      <div className="stats-grid">
        {[
          { label: 'Total Students', value: stats?.total_students, icon: '🎓', color: 'var(--primary)', to: '/admin/students' },
          { label: 'Total Faculty', value: stats?.total_faculty, icon: '👨‍🏫', color: 'var(--secondary)', to: '/admin/faculty' },
          { label: 'Active Courses', value: stats?.total_courses, icon: '📚', color: '#0891b2', to: '/admin/courses' },
          { label: 'Pending Fees', value: stats?.pending_fee_payments, icon: '⚠️', color: 'var(--warning)', to: '/admin/fees' },
          { label: 'Fee Collected', value: `₹${Number(stats?.total_fee_collected || 0).toLocaleString('en-IN')}`, icon: '💰', color: 'var(--success)', to: '/admin/fees' },
        ].map(s => (
          <Link key={s.label} to={s.to} style={{ textDecoration: 'none' }}>
            <div className="stat-card" style={{ borderTop: `3px solid ${s.color}` }}>
              <div style={{ fontSize: '1.5rem' }}>{s.icon}</div>
              <div className="stat-label">{s.label}</div>
              <div className="stat-value" style={{ color: s.color }}>{s.value}</div>
            </div>
          </Link>
        ))}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '1.25rem' }}>
        <div className="card">
          <h3 style={{ marginBottom: '1rem', fontSize: '1rem' }}>⚡ Quick Actions</h3>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
            {[
              { to: '/admin/students', label: '➕ Add Student', color: 'var(--primary)' },
              { to: '/admin/faculty', label: '➕ Add Faculty', color: 'var(--secondary)' },
              { to: '/admin/courses', label: '📚 Manage Courses', color: '#0891b2' },
              { to: '/admin/fees', label: '💰 Fee Structures', color: 'var(--success)' },
              { to: '/admin/announcements', label: '📢 Post Announcement', color: 'var(--warning)' },
            ].map(q => (
              <Link key={q.to} to={q.to} className="btn btn-secondary" style={{ justifyContent: 'flex-start', fontSize: '0.875rem' }}>
                {q.label}
              </Link>
            ))}
          </div>
        </div>

        <div className="card">
          <h3 style={{ marginBottom: '1rem', fontSize: '1rem' }}>📢 Recent Announcements</h3>
          {announcements.length === 0 ? <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>No announcements yet.</p> : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              {announcements.map(a => (
                <div key={a.id} style={{ padding: '0.625rem', background: 'var(--bg)', borderRadius: 8, fontSize: '0.875rem', borderLeft: '3px solid var(--primary)' }}>
                  <div style={{ fontWeight: 600 }}>{a.title}</div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>
                    {a.target_audience} • {new Date(a.created_at).toLocaleDateString()}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
