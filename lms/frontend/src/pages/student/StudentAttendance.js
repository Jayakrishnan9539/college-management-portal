import React, { useEffect, useState } from 'react';
import { studentAPI } from '../../api';

export default function StudentAttendance() {
  const [attendance, setAttendance] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    studentAPI.getAttendance().then(r => setAttendance(r.data)).finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="loading-center"><div className="spinner" /></div>;

  const overall = attendance.length
    ? Math.round(attendance.reduce((s, a) => s + a.percentage, 0) / attendance.length)
    : 0;

  return (
    <div>
      <div className="page-header">
        <h2 className="page-title">My Attendance</h2>
        <p className="page-subtitle">Track your class attendance across all courses</p>
      </div>

      <div className="stats-grid" style={{ marginBottom: '1.5rem' }}>
        <div className="stat-card" style={{ borderTop: `3px solid ${overall >= 75 ? 'var(--success)' : 'var(--danger)'}` }}>
          <div className="stat-label">Overall Average</div>
          <div className="stat-value" style={{ color: overall >= 75 ? 'var(--success)' : 'var(--danger)' }}>{overall}%</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Total Courses</div>
          <div className="stat-value">{attendance.length}</div>
        </div>
        <div className="stat-card" style={{ borderTop: '3px solid var(--danger)' }}>
          <div className="stat-label">Short Attendance</div>
          <div className="stat-value" style={{ color: 'var(--danger)' }}>
            {attendance.filter(a => a.is_short_attendance).length}
          </div>
          <div className="stat-sub">Below 75%</div>
        </div>
      </div>

      {attendance.length === 0 ? (
        <div className="card empty-state">
          <div style={{ fontSize: '2.5rem' }}>📋</div>
          <p>No attendance records found. Enroll in courses first.</p>
        </div>
      ) : (
        <div style={{ display: 'grid', gap: '1rem' }}>
          {attendance.map(a => (
            <div key={a.course_id} className="card">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '0.5rem' }}>
                <div>
                  <div style={{ fontWeight: 700, fontSize: '1rem' }}>{a.subject_code} — {a.subject_name}</div>
                  <div style={{ fontSize: '0.875rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
                    {a.attended} present / {a.absent} absent / {a.on_leave} on leave
                  </div>
                </div>
                <span className={`badge ${a.percentage >= 75 ? 'badge-green' : 'badge-red'}`} style={{ fontSize: '1rem', padding: '0.4rem 1rem' }}>
                  {a.percentage}%
                </span>
              </div>

              {/* Progress bar */}
              <div style={{ background: 'var(--bg)', borderRadius: 99, height: 10, margin: '1rem 0 0.5rem' }}>
                <div style={{
                  width: `${Math.min(a.percentage, 100)}%`,
                  height: '100%', borderRadius: 99,
                  background: a.percentage >= 75 ? 'var(--success)' : a.percentage >= 60 ? 'var(--warning)' : 'var(--danger)',
                  transition: 'width 0.5s',
                }} />
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                <span>Total Classes: {a.total_classes}</span>
                {a.is_short_attendance && (
                  <span style={{ color: 'var(--danger)', fontWeight: 600 }}>
                    ⚠️ Need {Math.ceil((0.75 * a.total_classes - a.attended) / 0.25)} more classes to reach 75%
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
