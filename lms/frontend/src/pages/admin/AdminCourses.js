import React, { useEffect, useState } from 'react';
import toast from 'react-hot-toast';
import { adminAPI } from '../../api';

export default function AdminCourses() {
  const [subjects, setSubjects] = useState([]);
  const [courses, setCourses] = useState([]);
  const [faculty, setFaculty] = useState([]);
  const [tab, setTab] = useState('courses');
  const [loading, setLoading] = useState(true);

  // Modals
  const [subjectModal, setSubjectModal] = useState(false);
  const [courseModal, setCourseModal] = useState(false);

  const [subjectForm, setSubjectForm] = useState({
    subject_code: '', subject_name: '', branch: 'CSE',
    semester: 1, credits: 3, theory_marks: 100, practical_marks: 50,
  });
  const [courseForm, setCourseForm] = useState({
    subject: '', faculty: '', semester: 1, section: 'A', academic_year: '2024-25', total_classes: 0,
  });
  const [saving, setSaving] = useState(false);

  const load = () => {
    setLoading(true);
    Promise.all([adminAPI.getSubjects(), adminAPI.getCourses(), adminAPI.getFaculty()])
      .then(([sRes, cRes, fRes]) => {
        setSubjects(sRes.data);
        setCourses(cRes.data);
        setFaculty(fRes.data.faculty);
      })
      .finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, []);

  const handleAddSubject = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      await adminAPI.createSubject({ ...subjectForm, semester: Number(subjectForm.semester), credits: Number(subjectForm.credits) });
      toast.success('Subject created!');
      setSubjectModal(false);
      setSubjectForm({ subject_code: '', subject_name: '', branch: 'CSE', semester: 1, credits: 3, theory_marks: 100, practical_marks: 50 });
      load();
    } catch (err) {
      toast.error(err.response?.data?.subject_code?.[0] || 'Failed to create subject.');
    } finally { setSaving(false); }
  };

  const handleAddCourse = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      await adminAPI.createCourse({
        ...courseForm,
        subject: Number(courseForm.subject),
        faculty: Number(courseForm.faculty),
        semester: Number(courseForm.semester),
      });
      toast.success('Course created!');
      setCourseModal(false);
      load();
    } catch (err) {
      toast.error(err.response?.data?.non_field_errors?.[0] || 'Failed to create course.');
    } finally { setSaving(false); }
  };

  if (loading) return <div className="loading-center"><div className="spinner" /></div>;

  return (
    <div>
      <div className="page-header"><h2 className="page-title">Courses & Subjects</h2></div>

      {/* Tabs */}
      <div className="auth-tabs" style={{ maxWidth: 300, marginBottom: '1.25rem' }}>
        <button className={`auth-tab ${tab === 'courses' ? 'active' : ''}`} onClick={() => setTab('courses')}>Courses</button>
        <button className={`auth-tab ${tab === 'subjects' ? 'active' : ''}`} onClick={() => setTab('subjects')}>Subjects</button>
      </div>

      {tab === 'subjects' && (
        <>
          <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: '1rem' }}>
            <button className="btn btn-primary" onClick={() => setSubjectModal(true)}>+ Add Subject</button>
          </div>
          <div className="table-wrapper">
            <table>
              <thead><tr><th>Code</th><th>Name</th><th>Branch</th><th>Semester</th><th>Credits</th><th>Theory</th><th>Practical</th></tr></thead>
              <tbody>
                {subjects.length === 0
                  ? <tr><td colSpan={7} style={{ textAlign: 'center', color: 'var(--text-muted)', padding: '2rem' }}>No subjects yet.</td></tr>
                  : subjects.map(s => (
                    <tr key={s.id}>
                      <td><strong>{s.subject_code}</strong></td>
                      <td>{s.subject_name}</td>
                      <td><span className="badge badge-blue">{s.branch}</span></td>
                      <td>Sem {s.semester}</td>
                      <td>{s.credits}</td>
                      <td>{s.theory_marks}</td>
                      <td>{s.practical_marks}</td>
                    </tr>
                  ))}
              </tbody>
            </table>
          </div>
        </>
      )}

      {tab === 'courses' && (
        <>
          <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: '1rem' }}>
            <button className="btn btn-primary" onClick={() => setCourseModal(true)}>+ Assign Course</button>
          </div>
          <div className="table-wrapper">
            <table>
              <thead><tr><th>Subject</th><th>Faculty</th><th>Section</th><th>Semester</th><th>Academic Year</th><th>Classes</th></tr></thead>
              <tbody>
                {courses.length === 0
                  ? <tr><td colSpan={6} style={{ textAlign: 'center', color: 'var(--text-muted)', padding: '2rem' }}>No courses yet. Assign a faculty to a subject to create a course.</td></tr>
                  : courses.map(c => (
                    <tr key={c.id}>
                      <td><strong>{c.subject_code}</strong> — {c.subject_name}</td>
                      <td>{c.faculty_name}</td>
                      <td>Section {c.section}</td>
                      <td>Sem {c.semester}</td>
                      <td>{c.academic_year}</td>
                      <td>{c.total_classes}</td>
                    </tr>
                  ))}
              </tbody>
            </table>
          </div>
        </>
      )}

      {/* Add Subject Modal */}
      {subjectModal && (
        <div className="modal-overlay" onClick={() => setSubjectModal(false)}>
          <div className="modal" style={{ maxWidth: 520 }} onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <span className="modal-title">Add Subject</span>
              <button className="modal-close" onClick={() => setSubjectModal(false)}>×</button>
            </div>
            <form onSubmit={handleAddSubject}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0 1rem' }}>
                <div className="form-group">
                  <label className="form-label">Subject Code</label>
                  <input className="form-input" placeholder="CS201" value={subjectForm.subject_code} onChange={e => setSubjectForm(p => ({ ...p, subject_code: e.target.value }))} required />
                </div>
                <div className="form-group">
                  <label className="form-label">Subject Name</label>
                  <input className="form-input" placeholder="Data Structures" value={subjectForm.subject_name} onChange={e => setSubjectForm(p => ({ ...p, subject_name: e.target.value }))} required />
                </div>
                <div className="form-group">
                  <label className="form-label">Branch</label>
                  <select className="form-select" value={subjectForm.branch} onChange={e => setSubjectForm(p => ({ ...p, branch: e.target.value }))}>
                    {['CSE','ECE','ME','CE','EE'].map(b => <option key={b}>{b}</option>)}
                  </select>
                </div>
                <div className="form-group">
                  <label className="form-label">Semester</label>
                  <select className="form-select" value={subjectForm.semester} onChange={e => setSubjectForm(p => ({ ...p, semester: e.target.value }))}>
                    {[1,2,3,4,5,6,7,8].map(s => <option key={s} value={s}>Semester {s}</option>)}
                  </select>
                </div>
                <div className="form-group">
                  <label className="form-label">Credits</label>
                  <input className="form-input" type="number" min="1" value={subjectForm.credits} onChange={e => setSubjectForm(p => ({ ...p, credits: e.target.value }))} />
                </div>
                <div className="form-group">
                  <label className="form-label">Theory Marks</label>
                  <input className="form-input" type="number" value={subjectForm.theory_marks} onChange={e => setSubjectForm(p => ({ ...p, theory_marks: e.target.value }))} />
                </div>
                <div className="form-group">
                  <label className="form-label">Practical Marks</label>
                  <input className="form-input" type="number" value={subjectForm.practical_marks} onChange={e => setSubjectForm(p => ({ ...p, practical_marks: e.target.value }))} />
                </div>
              </div>
              <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'flex-end' }}>
                <button type="button" className="btn btn-secondary" onClick={() => setSubjectModal(false)}>Cancel</button>
                <button type="submit" className="btn btn-primary" disabled={saving}>{saving ? 'Saving...' : 'Add Subject'}</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Assign Course Modal */}
      {courseModal && (
        <div className="modal-overlay" onClick={() => setCourseModal(false)}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <span className="modal-title">Assign Course to Faculty</span>
              <button className="modal-close" onClick={() => setCourseModal(false)}>×</button>
            </div>
            <form onSubmit={handleAddCourse}>
              <div className="form-group">
                <label className="form-label">Subject</label>
                <select className="form-select" value={courseForm.subject} onChange={e => setCourseForm(p => ({ ...p, subject: e.target.value }))} required>
                  <option value="">— Select Subject —</option>
                  {subjects.map(s => <option key={s.id} value={s.id}>{s.subject_code} — {s.subject_name}</option>)}
                </select>
              </div>
              <div className="form-group">
                <label className="form-label">Faculty</label>
                <select className="form-select" value={courseForm.faculty} onChange={e => setCourseForm(p => ({ ...p, faculty: e.target.value }))} required>
                  <option value="">— Select Faculty —</option>
                  {faculty.map(f => <option key={f.id} value={f.id}>{f.name} ({f.department})</option>)}
                </select>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0 1rem' }}>
                <div className="form-group">
                  <label className="form-label">Section</label>
                  <select className="form-select" value={courseForm.section} onChange={e => setCourseForm(p => ({ ...p, section: e.target.value }))}>
                    {['A','B','C','D'].map(s => <option key={s}>{s}</option>)}
                  </select>
                </div>
                <div className="form-group">
                  <label className="form-label">Semester</label>
                  <select className="form-select" value={courseForm.semester} onChange={e => setCourseForm(p => ({ ...p, semester: e.target.value }))}>
                    {[1,2,3,4,5,6,7,8].map(s => <option key={s} value={s}>Semester {s}</option>)}
                  </select>
                </div>
                <div className="form-group" style={{ gridColumn: '1 / -1' }}>
                  <label className="form-label">Academic Year</label>
                  <input className="form-input" value={courseForm.academic_year} onChange={e => setCourseForm(p => ({ ...p, academic_year: e.target.value }))} placeholder="2024-25" />
                </div>
              </div>
              <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'flex-end' }}>
                <button type="button" className="btn btn-secondary" onClick={() => setCourseModal(false)}>Cancel</button>
                <button type="submit" className="btn btn-primary" disabled={saving}>{saving ? 'Saving...' : 'Assign Course'}</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
