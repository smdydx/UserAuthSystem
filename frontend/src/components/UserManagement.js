
import React, { useState, useEffect } from 'react';
import { usersAPI } from '../services/api';

const UserManagement = () => {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedRole, setSelectedRole] = useState('');
  const [currentPage, setCurrentPage] = useState(0);

  useEffect(() => {
    fetchUsers();
  }, [searchTerm, selectedRole, currentPage]);

  const fetchUsers = async () => {
    try {
      const params = {
        skip: currentPage * 10,
        limit: 10,
        ...(searchTerm && { search: searchTerm }),
        ...(selectedRole && { role: selectedRole })
      };
      
      const response = await usersAPI.getUsers(params);
      setUsers(response.data);
    } catch (error) {
      setError('Failed to fetch users');
    } finally {
      setLoading(false);
    }
  };

  const handleUserAction = async (userId, action) => {
    setError('');
    setSuccess('');
    
    try {
      let message = '';
      switch (action) {
        case 'activate':
          await usersAPI.activateUser(userId);
          message = 'User activated successfully';
          break;
        case 'deactivate':
          await usersAPI.deactivateUser(userId);
          message = 'User deactivated successfully';
          break;
        case 'delete':
          if (window.confirm('Are you sure you want to delete this user? This action cannot be undone.')) {
            await usersAPI.deleteUser(userId);
            message = 'User deleted successfully';
          } else {
            return;
          }
          break;
        default:
          return;
      }
      
      setSuccess(message);
      await fetchUsers();
    } catch (error) {
      setError(error.response?.data?.detail || `Failed to ${action} user`);
    }
  };

  const getRoleBadgeClass = (role) => {
    switch (role) {
      case 'admin': return 'badge-admin';
      case 'vendor': return 'badge-vendor';
      case 'customer': return 'badge-customer';
      default: return 'badge-customer';
    }
  };

  if (loading) {
    return <div className="loading">Loading users...</div>;
  }

  return (
    <div>
      <h1>User Management</h1>
      
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

      {/* Filters */}
      <div className="card" style={{ marginBottom: '20px' }}>
        <h3>Filters</h3>
        <div className="two-columns">
          <div className="form-group">
            <label className="form-label">Search:</label>
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="form-input"
              placeholder="Search by email or name"
            />
          </div>
          
          <div className="form-group">
            <label className="form-label">Role:</label>
            <select
              value={selectedRole}
              onChange={(e) => setSelectedRole(e.target.value)}
              className="form-select"
            >
              <option value="">All Roles</option>
              <option value="admin">Admin</option>
              <option value="vendor">Vendor</option>
              <option value="customer">Customer</option>
            </select>
          </div>
        </div>
      </div>

      {/* Users List */}
      <div className="user-list">
        {users.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '40px', color: '#666' }}>
            No users found
          </div>
        ) : (
          users.map((user) => (
            <div key={user.id} className="user-item">
              <div className="user-info">
                <div className="user-details">
                  <h3>{user.full_name || user.email}</h3>
                  <p><strong>Email:</strong> {user.email}</p>
                  <p><strong>Phone:</strong> {user.phone_number || 'Not provided'}</p>
                  <p>
                    <strong>Role:</strong> 
                    <span className={`badge ${getRoleBadgeClass(user.role)}`} style={{ marginLeft: '8px' }}>
                      {user.role}
                    </span>
                  </p>
                  <p><strong>Status:</strong> {user.is_active ? '✅ Active' : '❌ Inactive'}</p>
                  <p><strong>Verified:</strong> {user.is_verified ? '✅ Yes' : '❌ No'}</p>
                  <p><strong>Joined:</strong> {new Date(user.created_at).toLocaleDateString()}</p>
                  {user.last_login && (
                    <p><strong>Last login:</strong> {new Date(user.last_login).toLocaleString()}</p>
                  )}
                </div>
                
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  {user.is_active ? (
                    <button
                      onClick={() => handleUserAction(user.id, 'deactivate')}
                      className="btn btn-secondary"
                      style={{ fontSize: '14px', padding: '8px 12px' }}
                    >
                      Deactivate
                    </button>
                  ) : (
                    <button
                      onClick={() => handleUserAction(user.id, 'activate')}
                      className="btn btn-success"
                      style={{ fontSize: '14px', padding: '8px 12px' }}
                    >
                      Activate
                    </button>
                  )}
                  
                  <button
                    onClick={() => handleUserAction(user.id, 'delete')}
                    className="btn btn-danger"
                    style={{ fontSize: '14px', padding: '8px 12px' }}
                  >
                    Delete
                  </button>
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Pagination */}
      <div style={{ textAlign: 'center', marginTop: '20px' }}>
        <button
          onClick={() => setCurrentPage(Math.max(0, currentPage - 1))}
          disabled={currentPage === 0}
          className="btn btn-secondary"
          style={{ marginRight: '10px' }}
        >
          Previous
        </button>
        
        <span style={{ margin: '0 15px', color: '#666' }}>
          Page {currentPage + 1}
        </span>
        
        <button
          onClick={() => setCurrentPage(currentPage + 1)}
          disabled={users.length < 10}
          className="btn btn-secondary"
          style={{ marginLeft: '10px' }}
        >
          Next
        </button>
      </div>
    </div>
  );
};

export default UserManagement;
