import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { facultyAPI } from '../../api';
import { useAuth } from '../../context/AuthContext';

export default function FacultyDashboard() {
  const { user } = useAuth();
  const [courses, setCourses] = useState([]);
  const [announcements, setAnnouncements] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([facultyAPI.getMyCourses(), facultyAPI.getAnnouncements()])
      .then(([cRes, aRes]) => { setCourses(cRes.data); setAnnouncements(aRes.data.slice(0, 4)); })
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="loading-center"><div className="spinner" /></div>;

  return (
    <div>
      <div className="page-header">
        <h2 className="page-title">Faculty Dashboard</h2>
        <p className="page-subtitle">Welcome, {user?.name}</p>
      </div>

      <div className="stats-grid">
        <div className="stat-card" style={{ borderTop: '3px solid var(--secondary)' }}>
          <div className="stat-label">Assigned Courses</div>
          <div className="stat-value" style={{ color: 'var(--secondary)' }}>{courses.length}</div>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '1.25rem' }}>
        <div className="card">
          <h3 style={{ marginBottom: '1rem', fontSize: '1rem' }}>📚 My Courses</h3>
          {courses.length === 0 ? (
            <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>No courses assigned yet.</p>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              {courses.map(c => (
                <div key={c.id} style={{ padding: '1rem', border: '1px solid var(--border)', borderRadius: 8, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div>
                    <div style={{ fontWeight: 700 }}>{c.subject_code} — {c.subject_name}</div>
                    <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>
                      Section {c.section} • Sem {c.semester} • {c.academic_year} • {c.total_classes} classes held
                    </div>
                  </div>
                  <div style={{ display: 'flex', gap: '0.5rem' }}>
                    <Link to={`/faculty/attendance?course=${c.id}`} className="btn btn-secondary btn-sm">Attendance</Link>
                    <Link to={`/faculty/marks?course=${c.id}`} className="btn btn-secondary btn-sm">Marks</Link>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="card">
          <h3 style={{ marginBottom: '1rem', fontSize: '1rem' }}>📢 Announcements</h3>
          {announcements.length === 0 ? <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>No announcements.</p> : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              {announcements.map(a => (
                <div key={a.id} style={{ padding: '0.75rem', background: 'var(--bg)', borderRadius: 8, fontSize: '0.875rem' }}>
                  <div style={{ fontWeight: 600 }}>{a.title}</div>
                  <div style={{ color: 'var(--text-muted)', fontSize: '0.8rem', marginTop: '0.25rem' }}>
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
