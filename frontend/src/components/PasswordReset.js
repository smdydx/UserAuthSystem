
import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { authAPI } from '../services/api';

const PasswordReset = () => {
  const [step, setStep] = useState(1); // 1: Send OTP, 2: Verify OTP and Reset Password
  const [formData, setFormData] = useState({
    email: '',
    method: 'email',
    otp_code: '',
    new_password: ''
  });
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [loading, setLoading] = useState(false);

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const handleSendOTP = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setSuccess('');

    try {
      await authAPI.sendResetOTP(formData.email, formData.method);
      setSuccess(`OTP sent to your ${formData.method === 'email' ? 'email' : 'phone'}!`);
      setStep(2);
    } catch (error) {
      setError(error.response?.data?.detail || 'Failed to send OTP');
    }
    
    setLoading(false);
  };

  const handleResetPassword = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setSuccess('');

    try {
      await authAPI.resetPasswordWithOTP(
        formData.email,
        formData.otp_code,
        formData.new_password
      );
      setSuccess('Password reset successfully! You can now login with your new password.');
      setStep(1);
      setFormData({
        email: '',
        method: 'email',
        otp_code: '',
        new_password: ''
      });
    } catch (error) {
      setError(error.response?.data?.detail || 'Password reset failed');
    }
    
    setLoading(false);
  };

  return (
    <div className="form-container">
      <h2 style={{ textAlign: 'center', marginBottom: '30px' }}>
        {step === 1 ? 'Reset Password' : 'Enter OTP & New Password'}
      </h2>
      
      {error && (
        <div className="alert alert-error">
          {error}
        </div>
      )}

      {success && (
        <div className="alert alert-success">
          {success}
        </div>
      )}

      {step === 1 ? (
        <form onSubmit={handleSendOTP}>
          <div className="form-group">
            <label className="form-label">Email:</label>
            <input
              type="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              className="form-input"
              required
              placeholder="Enter your email"
            />
          </div>

          <div className="form-group">
            <label className="form-label">Send OTP via:</label>
            <select
              name="method"
              value={formData.method}
              onChange={handleChange}
              className="form-select"
            >
              <option value="email">Email</option>
              <option value="sms">SMS</option>
            </select>
          </div>

          <button
            type="submit"
            className="btn btn-primary"
            style={{ width: '100%', marginBottom: '20px' }}
            disabled={loading}
          >
            {loading ? 'Sending OTP...' : 'Send OTP'}
          </button>
        </form>
      ) : (
        <form onSubmit={handleResetPassword}>
          <div className="form-group">
            <label className="form-label">Email:</label>
            <input
              type="email"
              value={formData.email}
              className="form-input"
              disabled
              style={{ backgroundColor: '#f8f9fa' }}
            />
          </div>

          <div className="form-group">
            <label className="form-label">OTP Code:</label>
            <input
              type="text"
              name="otp_code"
              value={formData.otp_code}
              onChange={handleChange}
              className="form-input"
              required
              placeholder="Enter 6-digit OTP"
              maxLength="6"
            />
          </div>

          <div className="form-group">
            <label className="form-label">New Password:</label>
            <input
              type="password"
              name="new_password"
              value={formData.new_password}
              onChange={handleChange}
              className="form-input"
              required
              placeholder="Enter new password"
            />
          </div>

          <div className="two-columns">
            <button
              type="button"
              onClick={() => setStep(1)}
              className="btn btn-secondary"
              disabled={loading}
            >
              Back
            </button>
            <button
              type="submit"
              className="btn btn-primary"
              disabled={loading}
            >
              {loading ? 'Resetting...' : 'Reset Password'}
            </button>
          </div>
        </form>
      )}

      <div style={{ textAlign: 'center', marginTop: '20px' }}>
        <p>
          Remember your password? <Link to="/login">Login here</Link>
        </p>
      </div>
    </div>
  );
};

export default PasswordReset;
