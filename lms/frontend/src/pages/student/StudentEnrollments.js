import React, { useEffect, useState } from 'react';
import toast from 'react-hot-toast';
import { studentAPI, adminAPI } from '../../api';

export default function StudentEnrollments() {
  const [enrollments, setEnrollments] = useState([]);
  const [courses, setCourses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [selectedCourse, setSelectedCourse] = useState('');
  const [academicYear, setAcademicYear] = useState('2024-25');
  const [enrolling, setEnrolling] = useState(false);

  const load = () => {
    setLoading(true);
    Promise.all([studentAPI.getEnrollments(), adminAPI.getCourses()])
      .then(([eRes, cRes]) => { setEnrollments(eRes.data); setCourses(cRes.data); })
      .finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, []);

  const handleEnroll = async () => {
    if (!selectedCourse) { toast.error('Please select a course'); return; }
    setEnrolling(true);
    try {
      await studentAPI.enroll({ course_id: Number(selectedCourse), academic_year: academicYear });
      toast.success('Enrolled successfully!');
      setShowModal(false);
      load();
    } catch (err) {
      toast.error(err.response?.data?.error || 'Enrollment failed.');
    } finally {
      setEnrolling(false);
    }
  };

  const handleDrop = async (id) => {
    if (!window.confirm('Are you sure you want to drop this course?')) return;
    try {
      await studentAPI.dropCourse(id);
      toast.success('Course dropped.');
      load();
    } catch {
      toast.error('Failed to drop course.');
    }
  };

  if (loading) return <div className="loading-center"><div className="spinner" /></div>;

  return (
    <div>
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <h2 className="page-title">My Enrollments</h2>
          <p className="page-subtitle">Courses you're enrolled in this semester</p>
        </div>
        <button className="btn btn-primary" onClick={() => setShowModal(true)}>+ Enroll in Course</button>
      </div>

      {enrollments.length === 0 ? (
        <div className="card empty-state">
          <div style={{ fontSize: '2.5rem' }}>📚</div>
          <p>You're not enrolled in any courses yet. Click "Enroll in Course" to get started.</p>
        </div>
      ) : (
        <div className="table-wrapper">
          <table>
            <thead>
              <tr>
                <th>Subject Code</th><th>Subject Name</th><th>Faculty</th><th>Section</th>
                <th>Academic Year</th><th>Status</th><th>Action</th>
              </tr>
            </thead>
            <tbody>
              {enrollments.map(e => (
                <tr key={e.id}>
                  <td><strong>{e.subject_code}</strong></td>
                  <td>{e.subject_name}</td>
                  <td>{e.faculty_name}</td>
                  <td>Section {e.section}</td>
                  <td>{e.academic_year}</td>
                  <td><span className={`badge ${e.status === 'ACTIVE' ? 'badge-green' : 'badge-gray'}`}>{e.status}</span></td>
                  <td>
                    {e.status === 'ACTIVE' && (
                      <button className="btn btn-danger btn-sm" onClick={() => handleDrop(e.id)}>Drop</button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Enroll modal */}
      {showModal && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <span className="modal-title">Enroll in a Course</span>
              <button className="modal-close" onClick={() => setShowModal(false)}>×</button>
            </div>
            <div className="form-group">
              <label className="form-label">Select Course</label>
              <select className="form-select" value={selectedCourse} onChange={e => setSelectedCourse(e.target.value)}>
                <option value="">— Select a course —</option>
                {courses.map(c => (
                  <option key={c.id} value={c.id}>
                    {c.subject_code} | {c.subject_name} | {c.faculty_name} | Sec {c.section}
                  </option>
                ))}
              </select>
            </div>
            <div className="form-group">
              <label className="form-label">Academic Year</label>
              <input className="form-input" value={academicYear} onChange={e => setAcademicYear(e.target.value)} placeholder="2024-25" />
            </div>
            <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'flex-end' }}>
              <button className="btn btn-secondary" onClick={() => setShowModal(false)}>Cancel</button>
              <button className="btn btn-primary" onClick={handleEnroll} disabled={enrolling}>
                {enrolling ? 'Enrolling...' : 'Enroll'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
