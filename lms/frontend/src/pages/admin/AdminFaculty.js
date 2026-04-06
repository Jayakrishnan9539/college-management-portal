import React, { useEffect, useState } from 'react';
import toast from 'react-hot-toast';
import { adminAPI } from '../../api';

export default function AdminFaculty() {
  const [faculty, setFaculty] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [form, setForm] = useState({ name: '', email: '', phone: '', password: '', department: 'CSE', designation: 'Assistant Prof', qualification: '', experience_years: 0 });
  const [saving, setSaving] = useState(false);

  const load = () => {
    setLoading(true);
    adminAPI.getFaculty().then(r => setFaculty(r.data.faculty)).finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, []);

  const handleRegister = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      await adminAPI.registerFaculty({ ...form, experience_years: Number(form.experience_years) });
      toast.success('Faculty account created!');
      setShowModal(false);
      setForm({ name: '', email: '', phone: '', password: '', department: 'CSE', designation: 'Assistant Prof', qualification: '', experience_years: 0 });
      load();
    } catch (err) {
      toast.error(err.response?.data?.email?.[0] || 'Failed to create account.');
    } finally { setSaving(false); }
  };

  return (
    <div>
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div><h2 className="page-title">Faculty</h2><p className="page-subtitle">Manage teaching staff</p></div>
        <button className="btn btn-primary" onClick={() => setShowModal(true)}>+ Add Faculty</button>
      </div>

      {loading ? <div className="loading-center"><div className="spinner" /></div> : (
        <div className="table-wrapper">
          <table>
            <thead><tr><th>Name</th><th>Email</th><th>Department</th><th>Designation</th><th>Experience</th><th>Qualification</th></tr></thead>
            <tbody>
              {faculty.length === 0 ? <tr><td colSpan={6} style={{ textAlign: 'center', color: 'var(--text-muted)', padding: '2rem' }}>No faculty added yet.</td></tr>
              : faculty.map(f => (
                <tr key={f.id}>
                  <td><strong>{f.name}</strong></td>
                  <td style={{ color: 'var(--text-muted)' }}>{f.email}</td>
                  <td><span className="badge badge-blue">{f.department}</span></td>
                  <td>{f.designation}</td>
                  <td>{f.experience_years} yrs</td>
                  <td>{f.qualification || '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {showModal && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal" style={{ maxWidth: 520 }} onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <span className="modal-title">Add Faculty Member</span>
              <button className="modal-close" onClick={() => setShowModal(false)}>×</button>
            </div>
            <form onSubmit={handleRegister}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0 1rem' }}>
                {[
                  { name: 'name', label: 'Full Name', col: '1 / -1' },
                  { name: 'email', label: 'Email', type: 'email' },
                  { name: 'phone', label: 'Phone' },
                  { name: 'password', label: 'Password', type: 'password', col: '1 / -1' },
                  { name: 'qualification', label: 'Qualification' },
                  { name: 'experience_years', label: 'Experience (years)', type: 'number' },
                ].map(f => (
                  <div className="form-group" key={f.name} style={{ gridColumn: f.col }}>
                    <label className="form-label">{f.label}</label>
                    <input className="form-input" type={f.type || 'text'} value={form[f.name]} onChange={e => setForm(p => ({ ...p, [f.name]: e.target.value }))} required={['name','email','password'].includes(f.name)} />
                  </div>
                ))}
                <div className="form-group">
                  <label className="form-label">Department</label>
                  <select className="form-select" value={form.department} onChange={e => setForm(p => ({ ...p, department: e.target.value }))}>
                    {['CSE','ECE','ME','CE','EE'].map(b => <option key={b}>{b}</option>)}
                  </select>
                </div>
                <div className="form-group">
                  <label className="form-label">Designation</label>
                  <select className="form-select" value={form.designation} onChange={e => setForm(p => ({ ...p, designation: e.target.value }))}>
                    {['Professor','Associate Prof','Assistant Prof'].map(d => <option key={d}>{d}</option>)}
                  </select>
                </div>
              </div>
              <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'flex-end' }}>
                <button type="button" className="btn btn-secondary" onClick={() => setShowModal(false)}>Cancel</button>
                <button type="submit" className="btn btn-primary" disabled={saving}>{saving ? 'Creating...' : 'Create Account'}</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
