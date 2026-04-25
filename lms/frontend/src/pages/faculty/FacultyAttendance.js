import React, { useEffect, useState } from 'react';
import toast from 'react-hot-toast';
import { facultyAPI } from '../../api';

export default function FacultyAttendance() {
  const [courses, setCourses] = useState([]);
  const [selectedCourse, setSelectedCourse] = useState('');
  const [date, setDate] = useState(new Date().toISOString().split('T')[0]);
  const [report, setReport] = useState(null);
  const [records, setRecords] = useState([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    facultyAPI.getMyCourses().then(r => { setCourses(r.data); if (r.data.length) setSelectedCourse(String(r.data[0].id)); }).finally(() => setLoading(false));
  }, []);

  const loadReport = async () => {
    if (!selectedCourse) return;
    try {
      const res = await facultyAPI.getCourseAttendance(selectedCourse, { date });
      setReport(res.data);
      // Build records with default PRESENT for all students in the course
      const uniqueStudents = [...new Map(res.data.records.map(r => [r.student, r])).values()];
      const existing = {};
      res.data.records.filter(r => r.class_date === date).forEach(r => { existing[r.student] = r.status; });
      setRecords(uniqueStudents.map(r => ({ student_id: r.student, name: r.student_name, roll: r.roll_number, status: existing[r.student] || 'PRESENT' })));
    } catch { toast.error('Failed to load attendance report.'); }
  };

  useEffect(() => { loadReport(); }, [selectedCourse]);

  const setStatus = (studentId, status) => {
    setRecords(prev => prev.map(r => r.student_id === studentId ? { ...r, status } : r));
  };

  const handleSubmit = async () => {
    if (!records.length) { toast.error('No students to mark attendance for.'); return; }
    setSubmitting(true);
    try {
      await facultyAPI.markAttendance({ course_id: Number(selectedCourse), class_date: date, records: records.map(r => ({ student_id: r.student_id, status: r.status })) });
      toast.success('Attendance marked successfully!');
      loadReport();
    } catch { toast.error('Failed to submit attendance.'); }
    finally { setSubmitting(false); }
  };

  if (loading) return <div className="loading-center"><div className="spinner" /></div>;

  const STATUS_COLORS = { PRESENT: 'badge-green', ABSENT: 'badge-red', LEAVE: 'badge-yellow' };

  return (
    <div>
      <div className="page-header"><h2 className="page-title">Mark Attendance</h2></div>

      <div className="card" style={{ marginBottom: '1.25rem', display: 'flex', gap: '1rem', flexWrap: 'wrap', alignItems: 'flex-end' }}>
        <div className="form-group" style={{ margin: 0 }}>
          <label className="form-label">Course</label>
          <select className="form-select" value={selectedCourse} onChange={e => setSelectedCourse(e.target.value)} style={{ minWidth: 260 }}>
            {courses.map(c => <option key={c.id} value={c.id}>{c.subject_code} — {c.subject_name} (Sec {c.section})</option>)}
          </select>
        </div>
        <div className="form-group" style={{ margin: 0 }}>
          <label className="form-label">Date</label>
          <input className="form-input" type="date" value={date} onChange={e => setDate(e.target.value)} style={{ width: 160 }} />
        </div>
        <button className="btn btn-secondary" onClick={loadReport}>Load Students</button>
      </div>

      {records.length === 0 ? (
        <div className="card empty-state"><div style={{ fontSize: '2.5rem' }}>👥</div><p>No enrolled students found for this course.</p></div>
      ) : (
        <div className="card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem', flexWrap: 'wrap', gap: '0.5rem' }}>
            <div>
              <strong>{records.length} students</strong>
              <span style={{ color: 'var(--text-muted)', fontSize: '0.875rem', marginLeft: '0.5rem' }}>— {date}</span>
            </div>
            <div style={{ display: 'flex', gap: '0.5rem' }}>
              <button className="btn btn-secondary btn-sm" onClick={() => setRecords(r => r.map(s => ({ ...s, status: 'PRESENT' })))}>All Present</button>
              <button className="btn btn-secondary btn-sm" onClick={() => setRecords(r => r.map(s => ({ ...s, status: 'ABSENT' })))}>All Absent</button>
            </div>
          </div>
          <div className="table-wrapper">
            <table>
              <thead><tr><th>Roll No</th><th>Name</th><th>Status</th></tr></thead>
              <tbody>
                {records.map(r => (
                  <tr key={r.student_id}>
                    <td><strong>{r.roll}</strong></td>
                    <td>{r.name}</td>
                    <td>
                      <div style={{ display: 'flex', gap: '0.5rem' }}>
                        {['PRESENT', 'ABSENT', 'LEAVE'].map(s => (
                          <button key={s} onClick={() => setStatus(r.student_id, s)}
                            className={`btn btn-sm ${r.status === s ? (s === 'PRESENT' ? 'btn-success' : s === 'ABSENT' ? 'btn-danger' : 'btn-secondary') : 'btn-secondary'}`}
                            style={{ opacity: r.status === s ? 1 : 0.5 }}>
                            {s === 'PRESENT' ? '✅' : s === 'ABSENT' ? '❌' : '🏖️'} {s}
                          </button>
                        ))}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div style={{ marginTop: '1rem', display: 'flex', justifyContent: 'flex-end' }}>
            <button className="btn btn-primary" onClick={handleSubmit} disabled={submitting}>
              {submitting ? 'Submitting...' : `Submit Attendance for ${date}`}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
