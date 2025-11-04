import React from 'react';
import { Box, Typography, Paper, Grid } from '@mui/material';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

// Mock data
const mockData = Array.from({ length: 24 }, (_, i) => ({
  hour: `${i}:00`,
  truthScore: 0.7 + Math.random() * 0.15,
  verificationRate: 0.75 + Math.random() * 0.15,
  biasScore: 0.65 + Math.random() * 0.2,
}));

export default function Metrics() {
  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        System Metrics
      </Typography>

      <Grid container spacing={3}>
        <Grid item xs={12}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Truth Score Metrics (Last 24 Hours)
            </Typography>
            <ResponsiveContainer width="100%" height={400}>
              <LineChart data={mockData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                <XAxis dataKey="hour" stroke="#999" />
                <YAxis domain={[0, 1]} stroke="#999" />
                <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #333' }} />
                <Legend />
                <Line type="monotone" dataKey="truthScore" stroke="#2196f3" name="Truth Score" />
                <Line type="monotone" dataKey="verificationRate" stroke="#4caf50" name="Verification Rate" />
                <Line type="monotone" dataKey="biasScore" stroke="#ff9800" name="Bias Score" />
              </LineChart>
            </ResponsiveContainer>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
}
