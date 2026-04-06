/**
 * Student Dashboard — shows a summary of attendance, marks, fees, and announcements.
 */

import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { studentAPI } from '../../api';
import { useAuth } from '../../context/AuthContext';

function StatCard({ icon, label, value, sub, color = 'var(--primary)', to }) {
  const content = (
    <div className="stat-card" style={{ borderTop: `3px solid ${color}` }}>
      <div style={{ fontSize: '1.5rem', marginBottom: '0.5rem' }}>{icon}</div>
      <div className="stat-label">{label}</div>
      <div className="stat-value" style={{ color }}>{value}</div>
      {sub && <div className="stat-sub">{sub}</div>}
    </div>
  );
  return to ? <Link to={to} style={{ textDecoration: 'none' }}>{content}</Link> : content;
}

export default function StudentDashboard() {
  const { user } = useAuth();
  const [profile, setProfile] = useState(null);
  const [attendance, setAttendance] = useState([]);
  const [marks, setMarks] = useState(null);
  const [fees, setFees] = useState(null);
  const [announcements, setAnnouncements] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      studentAPI.getProfile(),
      studentAPI.getAttendance(),
      studentAPI.getMarks(),
      studentAPI.getFees(),
      studentAPI.getAnnouncements(),
    ]).then(([profileRes, attRes, marksRes, feesRes, annRes]) => {
      setProfile(profileRes.data);
      setAttendance(attRes.data);
      setMarks(marksRes.data);
      setFees(feesRes.data);
      setAnnouncements(annRes.data.slice(0, 3));
    }).catch(console.error).finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="loading-center"><div className="spinner" /></div>;

  // Calculate average attendance
  const avgAttendance = attendance.length
    ? Math.round(attendance.reduce((s, a) => s + a.percentage, 0) / attendance.length)
    : 0;
  const shortAttendanceCourses = attendance.filter(a => a.is_short_attendance).length;

  return (
    <div>
      <div className="page-header">
        <h2 className="page-title">Welcome back, {user?.name?.split(' ')[0]}! 👋</h2>
        <p className="page-subtitle">
          {profile?.branch} • Semester {profile?.semester} • Roll No: {profile?.roll_number}
        </p>
      </div>

      {/* Stats */}
      <div className="stats-grid">
        <StatCard icon="✅" label="Avg Attendance" value={`${avgAttendance}%`}
          sub={shortAttendanceCourses > 0 ? `⚠️ ${shortAttendanceCourses} course(s) below 75%` : 'All good!'}
          color={avgAttendance >= 75 ? 'var(--success)' : 'var(--danger)'} to="/student/attendance" />
        <StatCard icon="📊" label="CGPA" value={marks?.cgpa || '—'}
          sub={`${marks?.total_credits || 0} credits earned`} color="var(--secondary)" to="/student/marks" />
        <StatCard icon="📚" label="Enrolled Courses"
          value={attendance.length} sub="Active this semester" color="var(--primary)" to="/student/enrollments" />
        <StatCard icon="💳" label="Fee Status"
          value={fees?.is_paid ? 'PAID' : fees?.fee_structure ? 'DUE' : '—'}
          sub={fees?.fee_structure ? `₹${fees.fee_structure.total_fee}` : 'No dues'}
          color={fees?.is_paid ? 'var(--success)' : 'var(--danger)'} to="/student/fees" />
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.25rem' }}>
        {/* Attendance summary */}
        <div className="card">
          <h3 style={{ marginBottom: '1rem', fontSize: '1rem' }}>📋 Attendance Summary</h3>
          {attendance.length === 0 ? (
            <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>No courses enrolled yet.</p>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              {attendance.map(a => (
                <div key={a.course_id}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.25rem' }}>
                    <span style={{ fontSize: '0.875rem', fontWeight: 500 }}>{a.subject_code}</span>
                    <span style={{
                      fontSize: '0.8rem', fontWeight: 700,
                      color: a.percentage >= 75 ? 'var(--success)' : 'var(--danger)'
                    }}>{a.percentage}%</span>
                  </div>
                  <div style={{ background: 'var(--bg)', borderRadius: 99, height: 6 }}>
                    <div style={{
                      width: `${Math.min(a.percentage, 100)}%`, height: '100%', borderRadius: 99,
                      background: a.percentage >= 75 ? 'var(--success)' : 'var(--danger)',
                      transition: 'width 0.5s',
                    }} />
                  </div>
                  {a.is_short_attendance && (
                    <span style={{ fontSize: '0.75rem', color: 'var(--danger)' }}>⚠️ Below 75% — attendance shortage</span>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Announcements */}
        <div className="card">
          <h3 style={{ marginBottom: '1rem', fontSize: '1rem' }}>📢 Announcements</h3>
          {announcements.length === 0 ? (
            <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>No announcements right now.</p>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              {announcements.map(a => (
                <div key={a.id} style={{ padding: '0.75rem', background: 'var(--bg)', borderRadius: 8, borderLeft: '3px solid var(--primary)' }}>
                  <div style={{ fontWeight: 600, fontSize: '0.875rem' }}>{a.title}</div>
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
                    {a.description.slice(0, 80)}{a.description.length > 80 ? '...' : ''}
                  </div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
                    {new Date(a.created_at).toLocaleDateString()}
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
