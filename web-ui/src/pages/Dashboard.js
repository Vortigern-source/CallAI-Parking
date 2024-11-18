import React, { useState, useEffect } from 'react';
import { 
  Container, 
  Typography, 
  Grid, 
  Paper, 
  Table, 
  TableBody, 
  TableCell, 
  TableContainer, 
  TableHead, 
  TableRow,
  CircularProgress,
  Alert,
  Box
} from '@mui/material';
import { api } from '../utils/api';

function Dashboard() {
  const [dashboardStats, setDashboardStats] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchDashboardStats = async () => {
      try {
        setIsLoading(true);
        const response = await api.getDashboardStats();
        setDashboardStats(response);
        setError(null);
      } catch (error) {
        console.error('Failed to fetch dashboard statistics:', error);
        setError(error.message || 'Failed to load dashboard statistics');
        setDashboardStats(null);
      } finally {
        setIsLoading(false);
      }
    };

    fetchDashboardStats();
  }, []);

  if (isLoading) {
    return (
      <Container maxWidth="md" style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
        <CircularProgress />
      </Container>
    );
  }

  return (
    <Container maxWidth="md">
      <Typography variant="h4" gutterBottom>
        Dashboard
      </Typography>

      {error && (
        <Alert severity="error" style={{ marginBottom: '16px' }}>
          {error}
        </Alert>
      )}

      {dashboardStats ? (
        <Grid container spacing={3}>
          {/* Users Statistics */}
          <Grid item xs={12} md={4}>
            <Paper elevation={3} style={{ padding: '16px', height: '100%' }}>
              <Typography variant="h6" gutterBottom>
                User Statistics
              </Typography>
              <Typography>Total Users: {dashboardStats.users.total}</Typography>
              <Typography>Admin Users: {dashboardStats.users.admin}</Typography>
              <Typography>Active Users: {dashboardStats.users.active}</Typography>
            </Paper>
          </Grid>

          {/* Bookings Statistics */}
          <Grid item xs={12} md={4}>
            <Paper elevation={3} style={{ padding: '16px', height: '100%' }}>
              <Typography variant="h6" gutterBottom>
                Booking Statistics
              </Typography>
              <Typography>Total Bookings: {dashboardStats.bookings.total}</Typography>
              <Typography>Drop-offs: {dashboardStats.bookings.drop_off}</Typography>
              <Typography>Collections: {dashboardStats.bookings.collection}</Typography>
              <Typography>Recent (7 days): {dashboardStats.bookings.recent}</Typography>
            </Paper>
          </Grid>

          {/* System Statistics */}
          <Grid item xs={12} md={4}>
            <Paper elevation={3} style={{ padding: '16px', height: '100%' }}>
              <Typography variant="h6" gutterBottom>
                System Performance
              </Typography>
              <Typography>CPU Usage: {dashboardStats.system.cpu_usage}%</Typography>
              <Typography>Memory Usage: {dashboardStats.system.memory_usage}%</Typography>
            </Paper>
          </Grid>

          {/* Bookings by Terminal */}
          <Grid item xs={12}>
            <Paper elevation={3} style={{ padding: '16px' }}>
              <Typography variant="h6" gutterBottom>
                Bookings by Terminal
              </Typography>
              <TableContainer>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Terminal</TableCell>
                      <TableCell>Number of Bookings</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {Object.entries(dashboardStats.bookings.by_terminal).map(([terminal, count]) => (
                      <TableRow key={terminal}>
                        <TableCell>{terminal}</TableCell>
                        <TableCell>{count}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </Paper>
          </Grid>
        </Grid>
      ) : (
        <Alert severity="warning">
          No dashboard statistics available
        </Alert>
      )}
    </Container>
  );
}

export default Dashboard;
