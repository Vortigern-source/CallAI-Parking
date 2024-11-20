import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Paper,
  Typography,
  CircularProgress,
  Alert,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Grid,
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import { api } from '../utils/api';

// Syntax highlighting for code
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { materialDark } from 'react-syntax-highlighter/dist/esm/styles/prism';

export default function Functions() {
  const [functions, setFunctions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchFunctions = useCallback(async () => {
    try {
      setLoading(true);
      const data = await api.getFunctions();
      setFunctions(data);
      setError(null);
    } catch (err) {
      console.error('Error fetching functions:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchFunctions();
  }, [fetchFunctions]);

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
        Error loading functions: {error}
      </Alert>
    );
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Bot Functions ({functions.length})
      </Typography>

      <Typography variant="body1" paragraph>
        These functions define the bot's capabilities and how it interacts with various services.
      </Typography>

      {functions.map((func) => (
        <Accordion key={func.name} sx={{ mb: 2 }}>
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Typography variant="h6">{func.name}</Typography>
          </AccordionSummary>
          <AccordionDetails>
            <Grid container spacing={2}>
              <Grid item xs={12}>
                <Typography variant="subtitle1" color="text.secondary" gutterBottom>
                  Description
                </Typography>
                <Typography paragraph>{func.description}</Typography>
              </Grid>

              <Grid item xs={12}>
                <Typography variant="subtitle1" color="text.secondary" gutterBottom>
                  Parameters
                </Typography>
                <Paper variant="outlined" sx={{ p: 2 }}>
                  {Object.entries(func.parameters || {}).map(([name, details]) => (
                    <Box key={name} sx={{ mb: 2 }}>
                      <Typography variant="subtitle2" component="span">
                        {name}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Type: {details?.type || 'N/A'}
                      </Typography>
                      <Typography variant="body2">
                        {details?.description || 'No description available'}
                      </Typography>
                    </Box>
                  ))}
                </Paper>
              </Grid>

              <Grid item xs={12}>
                <Typography variant="subtitle1" color="text.secondary" gutterBottom>
                  Implementation
                </Typography>
                <Paper variant="outlined">
                  <SyntaxHighlighter
                    language="python"
                    style={materialDark}
                    customStyle={{
                      margin: 0,
                      borderRadius: 4,
                    }}
                  >
                    {func.implementation || 'No implementation details available'}
                  </SyntaxHighlighter>
                </Paper>
              </Grid>
            </Grid>
          </AccordionDetails>
        </Accordion>
      ))}

      {functions.length === 0 && (
        <Alert severity="info">
          No functions found
        </Alert>
      )}
    </Box>
  );
}
