import React, { useEffect, useState } from 'react';
import toast from 'react-hot-toast';
import { adminAPI } from '../../api';

export default function AdminStudents() {
  const [students, setStudents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({ branch: '', semester: '' });
  const [editModal, setEditModal] = useState(null);

  const load = () => {
    setLoading(true);
    adminAPI.getStudents(Object.fromEntries(Object.entries(filters).filter(([,v]) => v)))
      .then(r => setStudents(r.data.students))
      .finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, []);

  const handleDeactivate = async (id, name) => {
    if (!window.confirm(`Deactivate ${name}?`)) return;
    try {
      await adminAPI.deactivateStudent(id);
      toast.success(`${name} deactivated.`);
      load();
    } catch { toast.error('Failed to deactivate.'); }
  };

  const handleUpdate = async () => {
    try {
      await adminAPI.updateStudent(editModal.id, { semester: editModal.semester, branch: editModal.branch });
      toast.success('Student updated!');
      setEditModal(null);
      load();
    } catch { toast.error('Update failed.'); }
  };

  return (
    <div>
      <div className="page-header">
        <h2 className="page-title">Students</h2>
        <p className="page-subtitle">Manage all enrolled students</p>
      </div>

      {/* Filters */}
      <div className="card" style={{ marginBottom: '1rem', display: 'flex', gap: '1rem', flexWrap: 'wrap', alignItems: 'flex-end' }}>
        <div className="form-group" style={{ margin: 0 }}>
          <label className="form-label">Branch</label>
          <select className="form-select" value={filters.branch} onChange={e => setFilters(p => ({ ...p, branch: e.target.value }))}>
            <option value="">All Branches</option>
            {['CSE','ECE','ME','CE','EE'].map(b => <option key={b}>{b}</option>)}
          </select>
        </div>
        <div className="form-group" style={{ margin: 0 }}>
          <label className="form-label">Semester</label>
          <select className="form-select" value={filters.semester} onChange={e => setFilters(p => ({ ...p, semester: e.target.value }))}>
            <option value="">All Semesters</option>
            {[1,2,3,4,5,6,7,8].map(s => <option key={s} value={s}>Sem {s}</option>)}
          </select>
        </div>
        <button className="btn btn-primary" onClick={load}>Apply</button>
      </div>

      {loading ? <div className="loading-center"><div className="spinner" /></div> : (
        <div className="table-wrapper">
          <table>
            <thead><tr><th>Roll No</th><th>Name</th><th>Email</th><th>Branch</th><th>Semester</th><th>Year</th><th>Actions</th></tr></thead>
            <tbody>
              {students.length === 0 ? (
                <tr><td colSpan={7} style={{ textAlign: 'center', color: 'var(--text-muted)', padding: '2rem' }}>No students found.</td></tr>
              ) : students.map(s => (
                <tr key={s.id}>
                  <td><strong>{s.roll_number}</strong></td>
                  <td>{s.name}</td>
                  <td style={{ color: 'var(--text-muted)' }}>{s.email}</td>
                  <td><span className="badge badge-blue">{s.branch}</span></td>
                  <td>Sem {s.semester}</td>
                  <td>{s.enrollment_year}</td>
                  <td style={{ display: 'flex', gap: '0.5rem' }}>
                    <button className="btn btn-secondary btn-sm" onClick={() => setEditModal({ id: s.id, name: s.name, semester: s.semester, branch: s.branch })}>Edit</button>
                    <button className="btn btn-danger btn-sm" onClick={() => handleDeactivate(s.id, s.name)}>Deactivate</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {editModal && (
        <div className="modal-overlay" onClick={() => setEditModal(null)}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <span className="modal-title">Edit — {editModal.name}</span>
              <button className="modal-close" onClick={() => setEditModal(null)}>×</button>
            </div>
            <div className="form-group">
              <label className="form-label">Branch</label>
              <select className="form-select" value={editModal.branch} onChange={e => setEditModal(p => ({ ...p, branch: e.target.value }))}>
                {['CSE','ECE','ME','CE','EE'].map(b => <option key={b}>{b}</option>)}
              </select>
            </div>
            <div className="form-group">
              <label className="form-label">Semester</label>
              <select className="form-select" value={editModal.semester} onChange={e => setEditModal(p => ({ ...p, semester: Number(e.target.value) }))}>
                {[1,2,3,4,5,6,7,8].map(s => <option key={s} value={s}>Semester {s}</option>)}
              </select>
            </div>
            <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'flex-end' }}>
              <button className="btn btn-secondary" onClick={() => setEditModal(null)}>Cancel</button>
              <button className="btn btn-primary" onClick={handleUpdate}>Save</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
