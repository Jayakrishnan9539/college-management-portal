import React, { useEffect, useState } from 'react';
import toast from 'react-hot-toast';
import { adminAPI } from '../../api';

export default function AdminAnnouncements() {
  const [announcements, setAnnouncements] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState({
    title: '', description: '', target_audience: 'ALL', expires_at: '',
  });

  const load = () => {
    setLoading(true);
    adminAPI.getAnnouncements().then(r => setAnnouncements(r.data)).finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, []);

  const handlePost = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      await adminAPI.createAnnouncement({ ...form, expires_at: form.expires_at || null });
      toast.success('Announcement posted!');
      setShowModal(false);
      setForm({ title: '', description: '', target_audience: 'ALL', expires_at: '' });
      load();
    } catch { toast.error('Failed to post announcement.'); }
    finally { setSaving(false); }
  };

  const AUDIENCE_COLORS = { ALL: 'badge-blue', STUDENT: 'badge-green', FACULTY: 'badge-yellow' };

  if (loading) return <div className="loading-center"><div className="spinner" /></div>;

  return (
    <div>
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div><h2 className="page-title">Announcements</h2><p className="page-subtitle">Post notices to students, faculty, or everyone</p></div>
        <button className="btn btn-primary" onClick={() => setShowModal(true)}>+ Post Announcement</button>
      </div>

      {announcements.length === 0 ? (
        <div className="card empty-state">
          <div style={{ fontSize: '2.5rem' }}>📢</div>
          <p>No announcements yet. Post one to notify students and faculty.</p>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {announcements.map(a => (
            <div key={a.id} className="card" style={{ borderLeft: `4px solid ${a.target_audience === 'ALL' ? 'var(--primary)' : a.target_audience === 'STUDENT' ? 'var(--success)' : 'var(--warning)'}` }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '0.5rem' }}>
                <div style={{ flex: 1 }}>
                  <div style={{ fontWeight: 700, fontSize: '1rem', marginBottom: '0.35rem' }}>{a.title}</div>
                  <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem', lineHeight: 1.6 }}>{a.description}</p>
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '0.35rem', flexShrink: 0 }}>
                  <span className={`badge ${AUDIENCE_COLORS[a.target_audience]}`}>→ {a.target_audience}</span>
                  <span className={`badge ${a.is_active ? 'badge-green' : 'badge-gray'}`}>{a.is_active ? 'Active' : 'Expired'}</span>
                </div>
              </div>
              <div style={{ marginTop: '0.75rem', fontSize: '0.8rem', color: 'var(--text-muted)', display: 'flex', gap: '1rem' }}>
                <span>📅 Posted: {new Date(a.created_at).toLocaleString('en-IN')}</span>
                {a.expires_at && <span>⏳ Expires: {new Date(a.expires_at).toLocaleDateString('en-IN')}</span>}
              </div>
            </div>
          ))}
        </div>
      )}

      {showModal && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal" style={{ maxWidth: 520 }} onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <span className="modal-title">Post Announcement</span>
              <button className="modal-close" onClick={() => setShowModal(false)}>×</button>
            </div>
            <form onSubmit={handlePost}>
              <div className="form-group">
                <label className="form-label">Title</label>
                <input className="form-input" placeholder="e.g., Semester Exam Schedule Released" value={form.title} onChange={e => setForm(p => ({ ...p, title: e.target.value }))} required />
              </div>
              <div className="form-group">
                <label className="form-label">Message</label>
                <textarea className="form-textarea" rows={4} placeholder="Write the full announcement here..." value={form.description} onChange={e => setForm(p => ({ ...p, description: e.target.value }))} required style={{ resize: 'vertical' }} />
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0 1rem' }}>
                <div className="form-group">
                  <label className="form-label">Target Audience</label>
                  <select className="form-select" value={form.target_audience} onChange={e => setForm(p => ({ ...p, target_audience: e.target.value }))}>
                    <option value="ALL">Everyone</option>
                    <option value="STUDENT">Students Only</option>
                    <option value="FACULTY">Faculty Only</option>
                  </select>
                </div>
                <div className="form-group">
                  <label className="form-label">Expires On (optional)</label>
                  <input className="form-input" type="date" value={form.expires_at} onChange={e => setForm(p => ({ ...p, expires_at: e.target.value }))} />
                </div>
              </div>
              <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'flex-end' }}>
                <button type="button" className="btn btn-secondary" onClick={() => setShowModal(false)}>Cancel</button>
                <button type="submit" className="btn btn-primary" disabled={saving}>{saving ? 'Posting...' : 'Post Announcement'}</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
