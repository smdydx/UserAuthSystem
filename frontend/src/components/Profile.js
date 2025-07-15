
import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { usersAPI } from '../services/api';

const Profile = () => {
  const { user, fetchUserProfile } = useAuth();
  const [editing, setEditing] = useState(false);
  const [changingPassword, setChangingPassword] = useState(false);
  const [formData, setFormData] = useState({
    full_name: user?.full_name || '',
    email: user?.email || '',
    phone_number: user?.phone_number || ''
  });
  const [passwordData, setPasswordData] = useState({
    current_password: '',
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

  const handlePasswordChange = (e) => {
    setPasswordData({
      ...passwordData,
      [e.target.name]: e.target.value
    });
  };

  const handleUpdateProfile = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setSuccess('');

    try {
      await usersAPI.updateUser(user.id, formData);
      setSuccess('Profile updated successfully!');
      await fetchUserProfile();
      setEditing(false);
    } catch (error) {
      setError(error.response?.data?.detail || 'Failed to update profile');
    }
    
    setLoading(false);
  };

  const handleChangePassword = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setSuccess('');

    try {
      await usersAPI.changePassword(user.id, passwordData);
      setSuccess('Password changed successfully!');
      setPasswordData({ current_password: '', new_password: '' });
      setChangingPassword(false);
    } catch (error) {
      setError(error.response?.data?.detail || 'Failed to change password');
    }
    
    setLoading(false);
  };

  return (
    <div>
      <h1>My Profile</h1>
      
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

      <div className="grid">
        {/* Profile Information */}
        <div className="card">
          <h3>Profile Information</h3>
          
          {!editing ? (
            <>
              <p><strong>Email:</strong> {user?.email}</p>
              <p><strong>Full Name:</strong> {user?.full_name || 'Not provided'}</p>
              <p><strong>Phone:</strong> {user?.phone_number || 'Not provided'}</p>
              <p><strong>Role:</strong> <span className={`badge badge-${user?.role}`}>{user?.role}</span></p>
              <p><strong>Status:</strong> {user?.is_verified ? '✅ Verified' : '❌ Not Verified'}</p>
              <p><strong>Member since:</strong> {new Date(user?.created_at).toLocaleDateString()}</p>
              
              <button 
                onClick={() => setEditing(true)}
                className="btn btn-primary"
                style={{ marginTop: '15px' }}
              >
                Edit Profile
              </button>
            </>
          ) : (
            <form onSubmit={handleUpdateProfile}>
              <div className="form-group">
                <label className="form-label">Email:</label>
                <input
                  type="email"
                  value={formData.email}
                  className="form-input"
                  disabled
                  style={{ backgroundColor: '#f8f9fa' }}
                />
                <small style={{ color: '#666' }}>Email cannot be changed</small>
              </div>

              <div className="form-group">
                <label className="form-label">Full Name:</label>
                <input
                  type="text"
                  name="full_name"
                  value={formData.full_name}
                  onChange={handleChange}
                  className="form-input"
                  placeholder="Enter your full name"
                />
              </div>

              <div className="form-group">
                <label className="form-label">Phone Number:</label>
                <input
                  type="tel"
                  name="phone_number"
                  value={formData.phone_number}
                  onChange={handleChange}
                  className="form-input"
                  placeholder="Enter your phone number"
                />
              </div>

              <div className="two-columns">
                <button
                  type="button"
                  onClick={() => setEditing(false)}
                  className="btn btn-secondary"
                  disabled={loading}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="btn btn-primary"
                  disabled={loading}
                >
                  {loading ? 'Saving...' : 'Save Changes'}
                </button>
              </div>
            </form>
          )}
        </div>

        {/* Change Password */}
        <div className="card">
          <h3>Change Password</h3>
          
          {!changingPassword ? (
            <>
              <p>Keep your account secure by using a strong password.</p>
              <button 
                onClick={() => setChangingPassword(true)}
                className="btn btn-primary"
                style={{ marginTop: '15px' }}
              >
                Change Password
              </button>
            </>
          ) : (
            <form onSubmit={handleChangePassword}>
              <div className="form-group">
                <label className="form-label">Current Password:</label>
                <input
                  type="password"
                  name="current_password"
                  value={passwordData.current_password}
                  onChange={handlePasswordChange}
                  className="form-input"
                  required
                  placeholder="Enter current password"
                />
              </div>

              <div className="form-group">
                <label className="form-label">New Password:</label>
                <input
                  type="password"
                  name="new_password"
                  value={passwordData.new_password}
                  onChange={handlePasswordChange}
                  className="form-input"
                  required
                  placeholder="Enter new password"
                />
              </div>

              <div className="two-columns">
                <button
                  type="button"
                  onClick={() => setChangingPassword(false)}
                  className="btn btn-secondary"
                  disabled={loading}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="btn btn-primary"
                  disabled={loading}
                >
                  {loading ? 'Changing...' : 'Change Password'}
                </button>
              </div>
            </form>
          )}
        </div>
      </div>
    </div>
  );
};

export default Profile;
