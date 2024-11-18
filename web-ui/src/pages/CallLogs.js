import React, { useState, useEffect } from 'react';
import {
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
  CircularProgress,
  Box,
  Chip,
  Alert,
} from '@mui/material';
import { api } from '../utils/api';

const getStatusColor = (status) => {
  switch (status.toLowerCase()) {
    case 'completed':
      return 'success';
    case 'in progress':
      return 'warning';
    default:
      return 'default';
  }
};

const formatDuration = (duration) => {
  if (duration === 'Ongoing') return duration;
  if (duration === 'Unknown') return 'Unknown';

  try {
    const [hours, minutes, seconds] = duration.split(':');
    if (hours === '0') {
      return `${minutes}m ${Math.round(parseFloat(seconds))}s`;
    }
    return `${hours}h ${minutes}m ${Math.round(parseFloat(seconds))}s`;
  } catch (e) {
    console.error('Error formatting duration:', e);
    return duration;
  }
};

export default function CallLogs() {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchLogs = async () => {
      try {
        setLoading(true);
        const data = await api.get('/calls');
        setLogs(data);
        setError(null);
      } catch (err) {
        console.error('Error fetching call logs:', err);
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchLogs();
    // Refresh every minute
    const interval = setInterval(fetchLogs, 60000);
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="200px">
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ mb: 2 }}>
        Error loading call logs: {error}
      </Alert>
    );
  }

  return (
    <>
      <Typography variant="h4" gutterBottom>
        Call Logs ({logs.length})
      </Typography>

      <TableContainer component={Paper}>
        <Table sx={{ minWidth: 650 }} aria-label="call logs table">
          <TableHead>
            <TableRow>
              <TableCell>Timestamp</TableCell>
              <TableCell>Phone Number</TableCell>
              <TableCell>Duration</TableCell>
              <TableCell>Status</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {logs.map((log) => (
              <TableRow
                key={log.id}
                sx={{ '&:last-child td, &:last-child th': { border: 0 } }}
              >
                <TableCell>{new Date(log.timestamp).toLocaleString('en-GB')}</TableCell>
                <TableCell>{log.phoneNumber}</TableCell>
                <TableCell>{formatDuration(log.duration)}</TableCell>
                <TableCell>
                  <Chip
                    label={log.status}
                    color={getStatusColor(log.status)}
                    size="small"
                  />
                </TableCell>
              </TableRow>
            ))}
            {logs.length === 0 && (
              <TableRow>
                <TableCell colSpan={4} align="center">
                  No call logs found
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </TableContainer>
    </>
  );
}
