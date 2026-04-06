import React, { useEffect, useState } from 'react';
import toast from 'react-hot-toast';
import { facultyAPI } from '../../api';

export default function FacultyMarks() {
  const [courses, setCourses] = useState([]);
  const [selectedCourse, setSelectedCourse] = useState('');
  const [courseData, setCourseData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [marksInputs, setMarksInputs] = useState({});
  const [academicYear, setAcademicYear] = useState('2024-25');
  const [saving, setSaving] = useState(null);

  useEffect(() => {
    facultyAPI.getMyCourses().then(r => { setCourses(r.data); if (r.data.length) setSelectedCourse(String(r.data[0].id)); }).finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (!selectedCourse) return;
    facultyAPI.getCourseMarks(selectedCourse).then(r => {
      setCourseData(r.data);
      const inputs = {};
      r.data.results.forEach(s => {
        inputs[s.student_id] = { theory_marks: s.theory_marks || 0, practical_marks: s.practical_marks || 0 };
      });
      setMarksInputs(inputs);
    });
  }, [selectedCourse]);

  const handleSave = async (studentId) => {
    const input = marksInputs[studentId];
    if (!input) return;
    setSaving(studentId);
    try {
      await facultyAPI.enterMarks(selectedCourse, { student_id: studentId, theory_marks: Number(input.theory_marks), practical_marks: Number(input.practical_marks), academic_year: academicYear });
      toast.success('Marks saved!');
      facultyAPI.getCourseMarks(selectedCourse).then(r => setCourseData(r.data));
    } catch (err) { toast.error(err.response?.data?.error || 'Failed to save marks.'); }
    finally { setSaving(null); }
  };

  if (loading) return <div className="loading-center"><div className="spinner" /></div>;

  return (
    <div>
      <div className="page-header"><h2 className="page-title">Enter Marks</h2></div>
      <div className="card" style={{ marginBottom: '1.25rem', display: 'flex', gap: '1rem', flexWrap: 'wrap', alignItems: 'flex-end' }}>
        <div className="form-group" style={{ margin: 0 }}>
          <label className="form-label">Course</label>
          <select className="form-select" value={selectedCourse} onChange={e => setSelectedCourse(e.target.value)} style={{ minWidth: 260 }}>
            {courses.map(c => <option key={c.id} value={c.id}>{c.subject_code} — {c.subject_name} (Sec {c.section})</option>)}
          </select>
        </div>
        <div className="form-group" style={{ margin: 0 }}>
          <label className="form-label">Academic Year</label>
          <input className="form-input" value={academicYear} onChange={e => setAcademicYear(e.target.value)} style={{ width: 120 }} />
        </div>
      </div>

      {!courseData?.results?.length ? (
        <div className="card empty-state"><div style={{ fontSize: '2.5rem' }}>📊</div><p>No students enrolled in this course yet.</p></div>
      ) : (
        <div className="table-wrapper">
          <table>
            <thead>
              <tr><th>Roll No</th><th>Name</th><th>Theory (Max: ?)</th><th>Practical (Max: ?)</th><th>Grade</th><th>Action</th></tr>
            </thead>
            <tbody>
              {courseData.results.map(s => (
                <tr key={s.student_id}>
                  <td><strong>{s.roll_number}</strong></td>
                  <td>{s.student_name}</td>
                  <td>
                    <input type="number" min="0" value={marksInputs[s.student_id]?.theory_marks ?? s.theory_marks}
                      onChange={e => setMarksInputs(p => ({ ...p, [s.student_id]: { ...p[s.student_id], theory_marks: e.target.value } }))}
                      style={{ width: 80, padding: '0.35rem 0.5rem', border: '1.5px solid var(--border)', borderRadius: 6, fontSize: '0.875rem' }} />
                  </td>
                  <td>
                    <input type="number" min="0" value={marksInputs[s.student_id]?.practical_marks ?? s.practical_marks}
                      onChange={e => setMarksInputs(p => ({ ...p, [s.student_id]: { ...p[s.student_id], practical_marks: e.target.value } }))}
                      style={{ width: 80, padding: '0.35rem 0.5rem', border: '1.5px solid var(--border)', borderRadius: 6, fontSize: '0.875rem' }} />
                  </td>
                  <td><span className="badge badge-blue">{s.grade || '—'}</span></td>
                  <td>
                    <button className="btn btn-primary btn-sm" onClick={() => handleSave(s.student_id)} disabled={saving === s.student_id}>
                      {saving === s.student_id ? '...' : 'Save'}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
