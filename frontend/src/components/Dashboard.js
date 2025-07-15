
import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { authAPI, usersAPI } from '../services/api';

const Dashboard = () => {
  const { user } = useAuth();
  const [stats, setStats] = useState(null);
  const [healthStatus, setHealthStatus] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      // Fetch health status
      const healthResponse = await authAPI.healthCheck();
      setHealthStatus(healthResponse.data);

      // Fetch user statistics (only for admin)
      if (user?.role === 'admin') {
        try {
          const statsResponse = await usersAPI.getUserStatistics();
          setStats(statsResponse.data);
        } catch (error) {
          console.error('Failed to fetch statistics:', error);
        }
      }
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="loading">Loading dashboard...</div>;
  }

  return (
    <div>
      <h1>Dashboard</h1>
      
      <div className="grid">
        {/* User Info Card */}
        <div className="card">
          <h3>Your Profile</h3>
          <p><strong>Email:</strong> {user?.email}</p>
          <p><strong>Name:</strong> {user?.full_name || 'Not provided'}</p>
          <p><strong>Role:</strong> <span className={`badge badge-${user?.role}`}>{user?.role}</span></p>
          <p><strong>Status:</strong> {user?.is_verified ? '✅ Verified' : '❌ Not Verified'}</p>
          <p><strong>Member since:</strong> {new Date(user?.created_at).toLocaleDateString()}</p>
          {user?.last_login && (
            <p><strong>Last login:</strong> {new Date(user?.last_login).toLocaleString()}</p>
          )}
        </div>

        {/* System Health Card */}
        <div className="card">
          <h3>System Health</h3>
          {healthStatus ? (
            <>
              <p><strong>Status:</strong> {healthStatus.status === 'healthy' ? '✅ Healthy' : '❌ Issues'}</p>
              <p><strong>Service:</strong> {healthStatus.service}</p>
            </>
          ) : (
            <p>Unable to fetch health status</p>
          )}
        </div>

        {/* Admin Statistics */}
        {user?.role === 'admin' && stats && (
          <div className="card">
            <h3>User Statistics</h3>
            <p><strong>Total Users:</strong> {stats.total_users}</p>
            <p><strong>Active Users:</strong> {stats.active_users}</p>
            <p><strong>Verified Users:</strong> {stats.verified_users}</p>
            <p><strong>Admins:</strong> {stats.admins}</p>
            <p><strong>Vendors:</strong> {stats.vendors}</p>
            <p><strong>Customers:</strong> {stats.customers}</p>
          </div>
        )}

        {/* Quick Actions Card */}
        <div className="card">
          <h3>Quick Actions</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            <button 
              onClick={() => window.location.href = '/profile'}
              className="btn btn-primary"
            >
              Edit Profile
            </button>
            {user?.role === 'admin' && (
              <button 
                onClick={() => window.location.href = '/users'}
                className="btn btn-success"
              >
                Manage Users
              </button>
            )}
            <button 
              onClick={() => window.open('/docs', '_blank')}
              className="btn btn-secondary"
            >
              View API Docs
            </button>
          </div>
        </div>
      </div>

      {/* Welcome Message */}
      <div className="card" style={{ marginTop: '20px', textAlign: 'center' }}>
        <h3>Welcome to FastAPI Authentication System! 🎉</h3>
        <p>
          You are successfully logged in as <strong>{user?.role}</strong>. 
          This dashboard shows your profile information and system status.
        </p>
        {user?.role === 'admin' && (
          <p>
            As an admin, you have access to user management features and system statistics.
          </p>
        )}
      </div>
    </div>
  );
};

export default Dashboard;
