import React, { useState, useEffect } from 'react';
import { 
    Box, 
    Typography, 
    Container, 
    Paper,
    Table,
    TableBody,
    TableCell,
    TableContainer,
    TableHead,
    TableRow,
    CircularProgress,
    Alert,
    TextField,
    Grid,
    MenuItem
} from '@mui/material';
import { useAuth } from '../context/AuthContext';
import { api } from '../utils/api';

function Bookings() {
    const { user, isAuthenticated, token } = useAuth();
    const [bookings, setBookings] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [searchTerm, setSearchTerm] = useState('');
    const [statusFilter, setStatusFilter] = useState('');
    const [terminalFilter, setTerminalFilter] = useState('');

    useEffect(() => {
        console.log('Auth state:', { 
            isAuthenticated, 
            token: token ? 'Token present' : 'No token', 
            user 
        });
        
        if (isAuthenticated) {
            fetchBookings();
        } else {
            setError('Not authenticated. Please log in.');
            setLoading(false);
        }
    }, [isAuthenticated, searchTerm, statusFilter, terminalFilter]);

    const fetchBookings = async () => {
        try {
            setLoading(true);
            const params = {};
            
            if (searchTerm) params.search = searchTerm;
            if (statusFilter) params.status = statusFilter;
            if (terminalFilter) params.terminal = terminalFilter;

            console.log('Fetching bookings with params:', params);

            const response = await api.getBookings(params);
            
            // Enhanced logging for debugging
            console.log('Raw bookings response:', response);

            if (Array.isArray(response)) {
                setBookings(response);
                setError('');
            } else {
                console.error('Invalid response format:', response);
                setError('Invalid response format from server');
                setBookings([]);
            }
        } catch (err) {
            console.error('Complete error object:', err);
            const errorMessage = err.message || 'Unknown error';
            console.error('Error fetching bookings:', errorMessage);
            setError(`Failed to load bookings: ${errorMessage}`);
            setBookings([]);
        } finally {
            setLoading(false);
        }
    };

    const handleSearch = (event) => {
        setSearchTerm(event.target.value);
    };

    const handleStatusFilter = (event) => {
        setStatusFilter(event.target.value);
    };

    const handleTerminalFilter = (event) => {
        setTerminalFilter(event.target.value);
    };

    const statusOptions = [
        { value: '', label: 'All Statuses' },
        { value: 'pending', label: 'Pending' },
        { value: 'arrived', label: 'Arrived' },
        { value: 'parked', label: 'Parked' },
        { value: 'collected', label: 'Collected' }
    ];

    const terminalOptions = [
        { value: '', label: 'All Terminals' },
        { value: 'T1', label: 'Terminal 1' },
        { value: 'T2', label: 'Terminal 2' },
        { value: 'T3', label: 'Terminal 3' }
    ];

    return (
        <Container maxWidth="lg">
            <Box sx={{ my: 4 }}>
                <Typography variant="h4" gutterBottom>
                    Bookings
                </Typography>

                <Paper elevation={3} sx={{ p: 3, mb: 3 }}>
                    <Grid container spacing={2}>
                        <Grid item xs={12} sm={4}>
                            <TextField
                                fullWidth
                                label="Search"
                                variant="outlined"
                                value={searchTerm}
                                onChange={handleSearch}
                                placeholder="Search by ref, registration, or customer"
                            />
                        </Grid>
                        <Grid item xs={12} sm={4}>
                            <TextField
                                fullWidth
                                select
                                label="Status Filter"
                                variant="outlined"
                                value={statusFilter}
                                onChange={handleStatusFilter}
                            >
                                {statusOptions.map((option) => (
                                    <MenuItem key={option.value} value={option.value}>
                                        {option.label}
                                    </MenuItem>
                                ))}
                            </TextField>
                        </Grid>
                        <Grid item xs={12} sm={4}>
                            <TextField
                                fullWidth
                                select
                                label="Terminal Filter"
                                variant="outlined"
                                value={terminalFilter}
                                onChange={handleTerminalFilter}
                            >
                                {terminalOptions.map((option) => (
                                    <MenuItem key={option.value} value={option.value}>
                                        {option.label}
                                    </MenuItem>
                                ))}
                            </TextField>
                        </Grid>
                    </Grid>
                </Paper>

                <Paper elevation={3} sx={{ width: '100%', overflow: 'hidden' }}>
                    {loading ? (
                        <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
                            <CircularProgress />
                        </Box>
                    ) : error ? (
                        <Alert severity="error" sx={{ m: 2 }}>{error}</Alert>
                    ) : bookings.length === 0 ? (
                        <Alert severity="info" sx={{ m: 2 }}>No bookings found</Alert>
                    ) : (
                        <TableContainer>
                            <Table stickyHeader>
                                <TableHead>
                                    <TableRow>
                                        <TableCell>Booking Ref</TableCell>
                                        <TableCell>Customer Name</TableCell>
                                        <TableCell>Registration</TableCell>
                                        <TableCell>Terminal</TableCell>
                                        <TableCell>Drop Off Status</TableCell>
                                        <TableCell>Collection Status</TableCell>
                                        <TableCell>Entry Time</TableCell>
                                        <TableCell>Return Time</TableCell>
                                    </TableRow>
                                </TableHead>
                                <TableBody>
                                    {bookings.map((booking) => (
                                        <TableRow key={booking.id} hover>
                                            <TableCell>{booking.bookingRef}</TableCell>
                                            <TableCell>{booking.customerName}</TableCell>
                                            <TableCell>{booking.registration}</TableCell>
                                            <TableCell>{booking.terminal}</TableCell>
                                            <TableCell>{booking.dropOffStatus}</TableCell>
                                            <TableCell>{booking.collectionStatus}</TableCell>
                                            <TableCell>{booking.entryDateTime}</TableCell>
                                            <TableCell>{booking.returnDateTime}</TableCell>
                                        </TableRow>
                                    ))}
                                </TableBody>
                            </Table>
                        </TableContainer>
                    )}
                </Paper>
            </Box>
        </Container>
    );
}

export default Bookings;
