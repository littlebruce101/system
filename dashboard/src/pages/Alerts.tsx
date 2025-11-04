import React from 'react';
import { Box, Typography, Paper, List, ListItem, ListItemText, Chip, IconButton } from '@mui/material';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ErrorIcon from '@mui/icons-material/Error';
import WarningIcon from '@mui/icons-material/Warning';
import InfoIcon from '@mui/icons-material/Info';

const mockAlerts = [
  {
    id: '1',
    severity: 'warning',
    title: 'Truth Score Degradation Detected',
    description: 'Average truth score has dropped from 0.75 to 0.68 in the last hour',
    triggeredAt: '2024-01-15T14:30:00Z',
    status: 'active',
  },
  {
    id: '2',
    severity: 'error',
    title: 'High Error Rate',
    description: 'Verification error rate at 12% (threshold: 10%)',
    triggeredAt: '2024-01-15T13:15:00Z',
    status: 'acknowledged',
  },
  {
    id: '3',
    severity: 'info',
    title: 'New Experiment Started',
    description: 'A/B test "Weight Optimization" is now running',
    triggeredAt: '2024-01-15T10:00:00Z',
    status: 'resolved',
  },
];

const getSeverityIcon = (severity: string) => {
  switch (severity) {
    case 'error':
      return <ErrorIcon color="error" />;
    case 'warning':
      return <WarningIcon color="warning" />;
    case 'info':
      return <InfoIcon color="info" />;
    default:
      return <InfoIcon />;
  }
};

const getSeverityColor = (severity: string) => {
  switch (severity) {
    case 'error':
      return 'error';
    case 'warning':
      return 'warning';
    case 'info':
      return 'info';
    default:
      return 'default';
  }
};

export default function Alerts() {
  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        System Alerts
      </Typography>

      <Paper>
        <List>
          {mockAlerts.map((alert, index) => (
            <ListItem
              key={alert.id}
              divider={index < mockAlerts.length - 1}
              secondaryAction={
                <IconButton edge="end" aria-label="resolve">
                  <CheckCircleIcon />
                </IconButton>
              }
            >
              <Box mr={2}>{getSeverityIcon(alert.severity)}</Box>
              <ListItemText
                primary={
                  <Box display="flex" alignItems="center" gap={1}>
                    <Typography>{alert.title}</Typography>
                    <Chip
                      label={alert.status}
                      size="small"
                      color={alert.status === 'active' ? 'error' : 'default'}
                    />
                  </Box>
                }
                secondary={
                  <>
                    <Typography variant="body2" color="textSecondary">
                      {alert.description}
                    </Typography>
                    <Typography variant="caption" color="textSecondary">
                      {new Date(alert.triggeredAt).toLocaleString()}
                    </Typography>
                  </>
                }
              />
            </ListItem>
          ))}
        </List>
      </Paper>
    </Box>
  );
}
