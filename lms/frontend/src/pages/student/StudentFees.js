import React, { useEffect, useState } from 'react';
import toast from 'react-hot-toast';
import { studentAPI } from '../../api';

export default function StudentFees() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [paying, setPaying] = useState(false);
  const [txnId, setTxnId] = useState('');

  const load = () => {
    setLoading(true);
    studentAPI.getFees().then(r => setData(r.data)).finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, []);

  const handlePay = async () => {
    if (!txnId.trim()) { toast.error('Please enter a transaction ID'); return; }
    setPaying(true);
    try {
      await studentAPI.payFees({
        fee_structure_id: data.fee_structure.id,
        amount_paid: data.fee_structure.total_fee,
        transaction_id: txnId,
      });
      toast.success('Payment recorded successfully!');
      load();
    } catch (err) {
      toast.error(err.response?.data?.error || 'Payment failed. Please try again.');
    } finally {
      setPaying(false);
    }
  };

  if (loading) return <div className="loading-center"><div className="spinner" /></div>;

  if (!data?.fee_structure) {
    return (
      <div>
        <div className="page-header"><h2 className="page-title">Fee Payment</h2></div>
        <div className="card empty-state">
          <div style={{ fontSize: '2.5rem' }}>💳</div>
          <p>No fee structure defined for your branch and semester yet.</p>
        </div>
      </div>
    );
  }

  const fee = data.fee_structure;

  return (
    <div>
      <div className="page-header">
        <h2 className="page-title">Fee Payment</h2>
        <p className="page-subtitle">View and pay your semester fees</p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.25rem', maxWidth: 800 }}>
        {/* Fee breakdown */}
        <div className="card">
          <h3 style={{ marginBottom: '1rem', fontSize: '1rem' }}>💰 Fee Breakdown</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            {[
              { label: 'Tuition Fee', value: fee.tuition_fee },
              { label: 'Hostel Fee', value: fee.hostel_fee },
              { label: 'Library Fee', value: fee.library_fee },
              { label: 'Lab Fee', value: fee.lab_fee },
            ].map(row => (
              <div key={row.label} style={{ display: 'flex', justifyContent: 'space-between', padding: '0.5rem 0', borderBottom: '1px solid var(--border)' }}>
                <span style={{ color: 'var(--text-muted)', fontSize: '0.875rem' }}>{row.label}</span>
                <span style={{ fontWeight: 600 }}>₹{Number(row.value).toLocaleString('en-IN')}</span>
              </div>
            ))}
            <div style={{ display: 'flex', justifyContent: 'space-between', padding: '0.5rem 0', fontWeight: 700 }}>
              <span>Total Due</span>
              <span style={{ color: 'var(--primary)', fontSize: '1.1rem' }}>₹{Number(fee.total_fee).toLocaleString('en-IN')}</span>
            </div>
          </div>
          <div style={{ marginTop: '0.75rem', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
            Due Date: {new Date(fee.due_date).toLocaleDateString('en-IN', { day: 'numeric', month: 'long', year: 'numeric' })}
          </div>
        </div>

        {/* Payment status / form */}
        <div className="card">
          <h3 style={{ marginBottom: '1rem', fontSize: '1rem' }}>
            {data.is_paid ? '✅ Payment Status' : '💳 Make Payment'}
          </h3>
          {data.is_paid ? (
            <div>
              <span className="badge badge-green" style={{ fontSize: '0.9rem', padding: '0.4rem 1rem', marginBottom: '1rem', display: 'inline-block' }}>
                ✅ PAID
              </span>
              <div style={{ fontSize: '0.875rem', color: 'var(--text-muted)' }}>
                <div><strong>Receipt No:</strong> {data.payment.receipt_number}</div>
                <div style={{ marginTop: '0.5rem' }}><strong>Paid On:</strong> {new Date(data.payment.payment_date).toLocaleString('en-IN')}</div>
                <div style={{ marginTop: '0.5rem' }}><strong>Amount:</strong> ₹{Number(data.payment.amount_paid).toLocaleString('en-IN')}</div>
              </div>
            </div>
          ) : (
            <div>
              <div style={{ marginBottom: '1rem', padding: '0.75rem', background: 'var(--warning-light)', borderRadius: 8, fontSize: '0.875rem', color: 'var(--warning)' }}>
                ⚠️ Your fee payment is due. Please pay before {new Date(fee.due_date).toLocaleDateString('en-IN')}.
              </div>
              <div className="form-group">
                <label className="form-label">Transaction / UPI Reference ID</label>
                <input className="form-input" placeholder="e.g. UPI123456789" value={txnId} onChange={e => setTxnId(e.target.value)} />
              </div>
              <div style={{ marginBottom: '1rem', fontSize: '0.875rem', color: 'var(--text-muted)' }}>
                Amount to pay: <strong>₹{Number(fee.total_fee).toLocaleString('en-IN')}</strong>
              </div>
              <button className="btn btn-primary btn-full" onClick={handlePay} disabled={paying}>
                {paying ? 'Recording Payment...' : `Pay ₹${Number(fee.total_fee).toLocaleString('en-IN')}`}
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
