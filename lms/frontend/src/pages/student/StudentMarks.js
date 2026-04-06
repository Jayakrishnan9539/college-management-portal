import React, { useEffect, useState } from 'react';
import { studentAPI } from '../../api';

const GRADE_COLORS = { 'A+': 'badge-green', 'A': 'badge-green', 'B+': 'badge-blue', 'B': 'badge-blue', 'C': 'badge-yellow', 'D': 'badge-yellow', 'F': 'badge-red' };

export default function StudentMarks() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [semester, setSemester] = useState('');

  const load = (sem) => {
    setLoading(true);
    studentAPI.getMarks(sem ? { semester: sem } : {})
      .then(r => setData(r.data))
      .finally(() => setLoading(false));
  };

  useEffect(() => { load(''); }, []);

  if (loading) return <div className="loading-center"><div className="spinner" /></div>;

  return (
    <div>
      <div className="page-header">
        <h2 className="page-title">Marks & Grades</h2>
        <p className="page-subtitle">View your academic performance and CGPA</p>
      </div>

      <div className="stats-grid">
        <div className="stat-card" style={{ borderTop: '3px solid var(--secondary)' }}>
          <div className="stat-label">CGPA</div>
          <div className="stat-value" style={{ color: 'var(--secondary)' }}>{data?.cgpa || '—'}</div>
          <div className="stat-sub">Cumulative Grade Point Average</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Total Credits</div>
          <div className="stat-value">{data?.total_credits || 0}</div>
        </div>
        <div className="stat-card" style={{ borderTop: '3px solid var(--success)' }}>
          <div className="stat-label">Subjects Passed</div>
          <div className="stat-value" style={{ color: 'var(--success)' }}>
            {data?.marks?.filter(m => m.grade !== 'F').length || 0}
          </div>
        </div>
      </div>

      {/* Semester filter */}
      <div className="card" style={{ marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '1rem' }}>
        <label className="form-label" style={{ margin: 0 }}>Filter by Semester:</label>
        <select className="form-select" style={{ width: 'auto' }} value={semester} onChange={e => { setSemester(e.target.value); load(e.target.value); }}>
          <option value="">All Semesters</option>
          {[1,2,3,4,5,6,7,8].map(s => <option key={s} value={s}>Semester {s}</option>)}
        </select>
      </div>

      {!data?.marks?.length ? (
        <div className="card empty-state">
          <div style={{ fontSize: '2.5rem' }}>📊</div>
          <p>No marks available yet.</p>
        </div>
      ) : (
        <div className="table-wrapper">
          <table>
            <thead>
              <tr>
                <th>Subject Code</th>
                <th>Subject Name</th>
                <th>Theory ({' '}<span style={{ fontWeight: 400 }}>Max</span>)</th>
                <th>Practical ({' '}<span style={{ fontWeight: 400 }}>Max</span>)</th>
                <th>Total</th>
                <th>Grade</th>
                <th>Semester</th>
              </tr>
            </thead>
            <tbody>
              {data.marks.map(m => (
                <tr key={m.id}>
                  <td><strong>{m.subject_code}</strong></td>
                  <td>{m.subject_name}</td>
                  <td>{m.theory_marks} / {m.max_theory}</td>
                  <td>{m.practical_marks} / {m.max_practical}</td>
                  <td><strong>{m.total_marks}</strong></td>
                  <td><span className={`badge ${GRADE_COLORS[m.grade] || 'badge-gray'}`}>{m.grade}</span></td>
                  <td>Sem {m.semester}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
