import React from 'react';
import {
  Box,
  Typography,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  LinearProgress,
} from '@mui/material';

// Mock experiments data
const mockExperiments = [
  {
    id: '1',
    name: 'Truth Score Weights Optimization',
    status: 'running',
    progress: 0.67,
    variants: 2,
    samples: 1234,
    targetSamples: 2000,
    startedAt: '2024-01-15',
  },
  {
    id: '2',
    name: 'Bias Detection Threshold Test',
    status: 'completed',
    progress: 1.0,
    variants: 3,
    samples: 3000,
    targetSamples: 3000,
    startedAt: '2024-01-10',
    winner: 'Variant B',
  },
  {
    id: '3',
    name: 'Verification Source Priority',
    status: 'draft',
    progress: 0,
    variants: 2,
    samples: 0,
    targetSamples: 1500,
  },
];

const getStatusColor = (status: string) => {
  switch (status) {
    case 'running':
      return 'info';
    case 'completed':
      return 'success';
    case 'draft':
      return 'default';
    default:
      return 'default';
  }
};

export default function Experiments() {
  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        A/B Testing Experiments
      </Typography>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Experiment Name</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Progress</TableCell>
              <TableCell align="right">Samples</TableCell>
              <TableCell align="right">Variants</TableCell>
              <TableCell>Started</TableCell>
              <TableCell>Winner</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {mockExperiments.map((exp) => (
              <TableRow key={exp.id} hover>
                <TableCell>{exp.name}</TableCell>
                <TableCell>
                  <Chip label={exp.status} color={getStatusColor(exp.status)} size="small" />
                </TableCell>
                <TableCell sx={{ minWidth: 200 }}>
                  <Box display="flex" alignItems="center">
                    <Box flexGrow={1} mr={1}>
                      <LinearProgress variant="determinate" value={exp.progress * 100} />
                    </Box>
                    <Typography variant="body2">{Math.round(exp.progress * 100)}%</Typography>
                  </Box>
                </TableCell>
                <TableCell align="right">
                  {exp.samples.toLocaleString()} / {exp.targetSamples.toLocaleString()}
                </TableCell>
                <TableCell align="right">{exp.variants}</TableCell>
                <TableCell>{exp.startedAt || '-'}</TableCell>
                <TableCell>{exp.winner || '-'}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );
}
