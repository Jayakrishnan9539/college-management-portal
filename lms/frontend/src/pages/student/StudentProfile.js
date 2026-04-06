import React, { useEffect, useState } from 'react';
import toast from 'react-hot-toast';
import { studentAPI, authAPI } from '../../api';

export default function StudentProfile() {
  const [profile, setProfile] = useState(null);
  const [form, setForm] = useState({});
  const [pwForm, setPwForm] = useState({ old_password: '', new_password: '', confirm: '' });
  const [saving, setSaving] = useState(false);
  const [changingPw, setChangingPw] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    studentAPI.getProfile().then(r => { setProfile(r.data); setForm({ phone: r.data.phone, dob: r.data.dob || '', address: r.data.address || '', city: r.data.city || '', pincode: r.data.pincode || '' }); }).finally(() => setLoading(false));
  }, []);

  const handleSave = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      const res = await studentAPI.updateProfile(form);
      setProfile(res.data);
      toast.success('Profile updated successfully!');
    } catch { toast.error('Failed to update profile.'); }
    finally { setSaving(false); }
  };

  const handleChangePw = async (e) => {
    e.preventDefault();
    if (pwForm.new_password !== pwForm.confirm) { toast.error("Passwords don't match"); return; }
    setChangingPw(true);
    try {
      await authAPI.changePassword({ old_password: pwForm.old_password, new_password: pwForm.new_password });
      toast.success('Password changed!');
      setPwForm({ old_password: '', new_password: '', confirm: '' });
    } catch (err) {
      toast.error(err.response?.data?.old_password?.[0] || err.response?.data?.new_password?.[0] || 'Failed to change password.');
    } finally { setChangingPw(false); }
  };

  if (loading) return <div className="loading-center"><div className="spinner" /></div>;

  return (
    <div>
      <div className="page-header"><h2 className="page-title">My Profile</h2></div>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.25rem', maxWidth: 900 }}>
        {/* Profile info */}
        <div className="card" style={{ gridColumn: '1 / -1' }}>
          <div style={{ display: 'flex', gap: '1.25rem', alignItems: 'center', marginBottom: '1.5rem' }}>
            <div style={{ width: 64, height: 64, borderRadius: '50%', background: 'var(--primary)', color: 'white', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '1.75rem', fontWeight: 700 }}>
              {profile?.name?.[0]?.toUpperCase()}
            </div>
            <div>
              <div style={{ fontWeight: 700, fontSize: '1.25rem' }}>{profile?.name}</div>
              <div style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>{profile?.email}</div>
              <div style={{ marginTop: '0.25rem' }}>
                <span className="badge badge-blue">{profile?.branch}</span>
                <span className="badge badge-gray" style={{ marginLeft: 6 }}>Semester {profile?.semester}</span>
                <span className="badge badge-green" style={{ marginLeft: 6 }}>Roll: {profile?.roll_number}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Edit profile form */}
        <div className="card">
          <h3 style={{ marginBottom: '1rem', fontSize: '1rem' }}>✏️ Edit Profile</h3>
          <form onSubmit={handleSave}>
            {[
              { name: 'phone', label: 'Phone', type: 'tel' },
              { name: 'dob', label: 'Date of Birth', type: 'date' },
              { name: 'address', label: 'Address', type: 'text' },
              { name: 'city', label: 'City', type: 'text' },
              { name: 'pincode', label: 'Pincode', type: 'text' },
            ].map(f => (
              <div className="form-group" key={f.name}>
                <label className="form-label">{f.label}</label>
                <input className="form-input" type={f.type} value={form[f.name] || ''} onChange={e => setForm(p => ({ ...p, [f.name]: e.target.value }))} />
              </div>
            ))}
            <button className="btn btn-primary btn-full" type="submit" disabled={saving}>
              {saving ? 'Saving...' : 'Save Changes'}
            </button>
          </form>
        </div>

        {/* Change password form */}
        <div className="card">
          <h3 style={{ marginBottom: '1rem', fontSize: '1rem' }}>🔐 Change Password</h3>
          <form onSubmit={handleChangePw}>
            <div className="form-group">
              <label className="form-label">Current Password</label>
              <input className="form-input" type="password" value={pwForm.old_password} onChange={e => setPwForm(p => ({ ...p, old_password: e.target.value }))} required />
            </div>
            <div className="form-group">
              <label className="form-label">New Password</label>
              <input className="form-input" type="password" value={pwForm.new_password} onChange={e => setPwForm(p => ({ ...p, new_password: e.target.value }))} required />
            </div>
            <div className="form-group">
              <label className="form-label">Confirm New Password</label>
              <input className="form-input" type="password" value={pwForm.confirm} onChange={e => setPwForm(p => ({ ...p, confirm: e.target.value }))} required />
            </div>
            <button className="btn btn-primary btn-full" type="submit" disabled={changingPw}>
              {changingPw ? 'Changing...' : 'Change Password'}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
