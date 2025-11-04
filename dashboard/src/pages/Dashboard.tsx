import React from 'react';
import {
  Grid,
  Paper,
  Typography,
  Box,
  Card,
  CardContent,
  LinearProgress,
} from '@mui/material';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from 'recharts';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import TrendingDownIcon from '@mui/icons-material/TrendingDown';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ErrorIcon from '@mui/icons-material/Error';

// Mock data - in production, fetch from API
const mockTruthScores = [
  { time: '00:00', score: 0.72 },
  { time: '04:00', score: 0.75 },
  { time: '08:00', score: 0.73 },
  { time: '12:00', score: 0.78 },
  { time: '16:00', score: 0.76 },
  { time: '20:00', score: 0.74 },
];

const mockComponentScores = [
  { name: 'Verification', value: 0.78 },
  { name: 'Bias', value: 0.72 },
  { name: 'Claims', value: 0.68 },
];

const mockVerificationStatus = [
  { name: 'Verified', value: 456, color: '#4caf50' },
  { name: 'Contradicted', value: 89, color: '#f44336' },
  { name: 'Unsupported', value: 234, color: '#ff9800' },
  { name: 'Uncertain', value: 123, color: '#9e9e9e' },
];

interface MetricCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  trend?: 'up' | 'down' | 'neutral';
  trendValue?: string;
  icon?: React.ReactElement;
  color?: string;
}

function MetricCard({ title, value, subtitle, trend, trendValue, icon, color }: MetricCardProps) {
  const getTrendIcon = () => {
    if (trend === 'up') return <TrendingUpIcon sx={{ color: 'success.main' }} />;
    if (trend === 'down') return <TrendingDownIcon sx={{ color: 'error.main' }} />;
    return null;
  };

  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Box display="flex" justifyContent="space-between" alignItems="flex-start">
          <Box>
            <Typography color="textSecondary" gutterBottom variant="body2">
              {title}
            </Typography>
            <Typography variant="h4" component="div" sx={{ color: color || 'text.primary' }}>
              {value}
            </Typography>
            {subtitle && (
              <Typography variant="body2" color="textSecondary" sx={{ mt: 1 }}>
                {subtitle}
              </Typography>
            )}
            {trend && trendValue && (
              <Box display="flex" alignItems="center" mt={1}>
                {getTrendIcon()}
                <Typography
                  variant="body2"
                  sx={{
                    ml: 0.5,
                    color: trend === 'up' ? 'success.main' : trend === 'down' ? 'error.main' : 'text.secondary',
                  }}
                >
                  {trendValue}
                </Typography>
              </Box>
            )}
          </Box>
          {icon && (
            <Box sx={{ opacity: 0.3, fontSize: 48 }}>
              {icon}
            </Box>
          )}
        </Box>
      </CardContent>
    </Card>
  );
}

export default function Dashboard() {
  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        System Overview
      </Typography>

      {/* Key Metrics */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="Avg Truth Score"
            value="0.74"
            subtitle="Last 24 hours"
            trend="up"
            trendValue="+3.2%"
            color="primary.main"
            icon={<CheckCircleIcon />}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="Documents Scored"
            value="12,456"
            subtitle="Total processed"
            trend="up"
            trendValue="+284 today"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="Verification Rate"
            value="82%"
            subtitle="Claims verified"
            trend="neutral"
            color="success.main"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <MetricCard
            title="Active Alerts"
            value="3"
            subtitle="2 warnings, 1 info"
            trend="down"
            trendValue="-2 from yesterday"
            icon={<ErrorIcon />}
          />
        </Grid>
      </Grid>

      {/* Charts */}
      <Grid container spacing={3}>
        {/* Truth Score Trend */}
        <Grid item xs={12} md={8}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Truth Score Trend
            </Typography>
            <ResponsiveContainer width="100%" height={300}>
              <AreaChart data={mockTruthScores}>
                <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                <XAxis dataKey="time" stroke="#999" />
                <YAxis domain={[0, 1]} stroke="#999" />
                <Tooltip
                  contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #333' }}
                />
                <Area
                  type="monotone"
                  dataKey="score"
                  stroke="#2196f3"
                  fill="#2196f3"
                  fillOpacity={0.3}
                />
              </AreaChart>
            </ResponsiveContainer>
          </Paper>
        </Grid>

        {/* Component Scores */}
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Component Scores
            </Typography>
            <Box sx={{ mt: 2 }}>
              {mockComponentScores.map((component) => (
                <Box key={component.name} sx={{ mb: 2 }}>
                  <Box display="flex" justifyContent="space-between" mb={0.5}>
                    <Typography variant="body2">{component.name}</Typography>
                    <Typography variant="body2" color="primary">
                      {(component.value * 100).toFixed(0)}%
                    </Typography>
                  </Box>
                  <LinearProgress
                    variant="determinate"
                    value={component.value * 100}
                    sx={{ height: 8, borderRadius: 1 }}
                  />
                </Box>
              ))}
            </Box>
          </Paper>
        </Grid>

        {/* Verification Status Distribution */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Verification Status Distribution
            </Typography>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={mockVerificationStatus}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={(entry) => `${entry.name}: ${entry.value}`}
                  outerRadius={100}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {mockVerificationStatus.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #333' }}
                />
              </PieChart>
            </ResponsiveContainer>
          </Paper>
        </Grid>

        {/* Recent Activity */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Recent Activity
            </Typography>
            <Box sx={{ mt: 2 }}>
              {[
                { time: '2 min ago', event: 'High truth score document indexed', icon: <CheckCircleIcon color="success" /> },
                { time: '15 min ago', event: 'Alert: Low verification rate detected', icon: <ErrorIcon color="warning" /> },
                { time: '1 hour ago', event: 'Experiment "Weight Optimization" completed', icon: <CheckCircleIcon color="info" /> },
                { time: '2 hours ago', event: 'System health check passed', icon: <CheckCircleIcon color="success" /> },
              ].map((activity, index) => (
                <Box
                  key={index}
                  display="flex"
                  alignItems="center"
                  sx={{
                    mb: 1.5,
                    pb: 1.5,
                    borderBottom: index < 3 ? '1px solid rgba(255,255,255,0.1)' : 'none',
                  }}
                >
                  {activity.icon}
                  <Box ml={2}>
                    <Typography variant="body2">{activity.event}</Typography>
                    <Typography variant="caption" color="textSecondary">
                      {activity.time}
                    </Typography>
                  </Box>
                </Box>
              ))}
            </Box>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
}
