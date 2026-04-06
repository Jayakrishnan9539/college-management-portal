import React, { useEffect, useState } from 'react';
import toast from 'react-hot-toast';
import { adminAPI } from '../../api';

export default function AdminFees() {
  const [structures, setStructures] = useState([]);
  const [report, setReport] = useState(null);
  const [tab, setTab] = useState('structures');
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState({
    branch: 'CSE', semester: 1, due_date: '',
    tuition_fee: 0, hostel_fee: 0, library_fee: 0, lab_fee: 0,
  });

  const load = () => {
    setLoading(true);
    Promise.all([adminAPI.getFeeStructures(), adminAPI.getFeeReport()])
      .then(([sRes, rRes]) => { setStructures(sRes.data); setReport(rRes.data); })
      .finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, []);

  const handleSave = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      await adminAPI.createFeeStructure({
        ...form,
        semester: Number(form.semester),
        tuition_fee: Number(form.tuition_fee),
        hostel_fee: Number(form.hostel_fee),
        library_fee: Number(form.library_fee),
        lab_fee: Number(form.lab_fee),
      });
      toast.success('Fee structure created!');
      setShowModal(false);
      load();
    } catch (err) {
      toast.error(err.response?.data?.non_field_errors?.[0] || 'Failed. This branch/semester may already have a fee structure.');
    } finally { setSaving(false); }
  };

  const totalFee = Number(form.tuition_fee) + Number(form.hostel_fee) + Number(form.library_fee) + Number(form.lab_fee);

  if (loading) return <div className="loading-center"><div className="spinner" /></div>;

  return (
    <div>
      <div className="page-header"><h2 className="page-title">Fee Management</h2></div>

      <div className="auth-tabs" style={{ maxWidth: 300, marginBottom: '1.25rem' }}>
        <button className={`auth-tab ${tab === 'structures' ? 'active' : ''}`} onClick={() => setTab('structures')}>Fee Structures</button>
        <button className={`auth-tab ${tab === 'report' ? 'active' : ''}`} onClick={() => setTab('report')}>Payment Report</button>
      </div>

      {tab === 'structures' && (
        <>
          <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: '1rem' }}>
            <button className="btn btn-primary" onClick={() => setShowModal(true)}>+ Add Fee Structure</button>
          </div>
          <div className="table-wrapper">
            <table>
              <thead><tr><th>Branch</th><th>Semester</th><th>Tuition</th><th>Hostel</th><th>Library</th><th>Lab</th><th>Total</th><th>Due Date</th></tr></thead>
              <tbody>
                {structures.length === 0
                  ? <tr><td colSpan={8} style={{ textAlign: 'center', color: 'var(--text-muted)', padding: '2rem' }}>No fee structures defined yet.</td></tr>
                  : structures.map(s => (
                    <tr key={s.id}>
                      <td><span className="badge badge-blue">{s.branch}</span></td>
                      <td>Sem {s.semester}</td>
                      <td>₹{Number(s.tuition_fee).toLocaleString('en-IN')}</td>
                      <td>₹{Number(s.hostel_fee).toLocaleString('en-IN')}</td>
                      <td>₹{Number(s.library_fee).toLocaleString('en-IN')}</td>
                      <td>₹{Number(s.lab_fee).toLocaleString('en-IN')}</td>
                      <td><strong>₹{Number(s.total_fee).toLocaleString('en-IN')}</strong></td>
                      <td>{new Date(s.due_date).toLocaleDateString('en-IN')}</td>
                    </tr>
                  ))}
              </tbody>
            </table>
          </div>
        </>
      )}

      {tab === 'report' && (
        <>
          <div className="stats-grid" style={{ marginBottom: '1.25rem' }}>
            <div className="stat-card" style={{ borderTop: '3px solid var(--success)' }}>
              <div className="stat-label">Total Collected</div>
              <div className="stat-value" style={{ color: 'var(--success)' }}>₹{Number(report?.total_collected || 0).toLocaleString('en-IN')}</div>
            </div>
            <div className="stat-card">
              <div className="stat-label">Payments Received</div>
              <div className="stat-value">{report?.payment_count || 0}</div>
            </div>
          </div>
          <div className="table-wrapper">
            <table>
              <thead><tr><th>Receipt No</th><th>Student</th><th>Roll No</th><th>Branch/Sem</th><th>Amount</th><th>Date</th><th>Status</th></tr></thead>
              <tbody>
                {!report?.payments?.length
                  ? <tr><td colSpan={7} style={{ textAlign: 'center', color: 'var(--text-muted)', padding: '2rem' }}>No payments yet.</td></tr>
                  : report.payments.map(p => (
                    <tr key={p.id}>
                      <td><code style={{ fontSize: '0.8rem' }}>{p.receipt_number}</code></td>
                      <td>{p.student_name}</td>
                      <td>{p.roll_number}</td>
                      <td>{p.fee_branch} / Sem {p.fee_semester}</td>
                      <td><strong>₹{Number(p.amount_paid).toLocaleString('en-IN')}</strong></td>
                      <td>{new Date(p.payment_date).toLocaleDateString('en-IN')}</td>
                      <td><span className="badge badge-green">{p.payment_status}</span></td>
                    </tr>
                  ))}
              </tbody>
            </table>
          </div>
        </>
      )}

      {showModal && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal" style={{ maxWidth: 520 }} onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <span className="modal-title">Create Fee Structure</span>
              <button className="modal-close" onClick={() => setShowModal(false)}>×</button>
            </div>
            <form onSubmit={handleSave}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0 1rem' }}>
                <div className="form-group">
                  <label className="form-label">Branch</label>
                  <select className="form-select" value={form.branch} onChange={e => setForm(p => ({ ...p, branch: e.target.value }))}>
                    {['CSE','ECE','ME','CE','EE'].map(b => <option key={b}>{b}</option>)}
                  </select>
                </div>
                <div className="form-group">
                  <label className="form-label">Semester</label>
                  <select className="form-select" value={form.semester} onChange={e => setForm(p => ({ ...p, semester: e.target.value }))}>
                    {[1,2,3,4,5,6,7,8].map(s => <option key={s} value={s}>Semester {s}</option>)}
                  </select>
                </div>
                {[
                  { name: 'tuition_fee', label: 'Tuition Fee (₹)' },
                  { name: 'hostel_fee', label: 'Hostel Fee (₹)' },
                  { name: 'library_fee', label: 'Library Fee (₹)' },
                  { name: 'lab_fee', label: 'Lab Fee (₹)' },
                ].map(f => (
                  <div className="form-group" key={f.name}>
                    <label className="form-label">{f.label}</label>
                    <input className="form-input" type="number" min="0" value={form[f.name]} onChange={e => setForm(p => ({ ...p, [f.name]: e.target.value }))} />
                  </div>
                ))}
                <div className="form-group" style={{ gridColumn: '1 / -1' }}>
                  <label className="form-label">Due Date</label>
                  <input className="form-input" type="date" value={form.due_date} onChange={e => setForm(p => ({ ...p, due_date: e.target.value }))} required />
                </div>
              </div>
              <div style={{ padding: '0.75rem', background: 'var(--primary-light)', borderRadius: 8, marginBottom: '1rem', fontWeight: 700, color: 'var(--primary)' }}>
                Total Fee: ₹{totalFee.toLocaleString('en-IN')}
              </div>
              <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'flex-end' }}>
                <button type="button" className="btn btn-secondary" onClick={() => setShowModal(false)}>Cancel</button>
                <button type="submit" className="btn btn-primary" disabled={saving}>{saving ? 'Saving...' : 'Create Structure'}</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
