# Truth-First Search Dashboard

React-based monitoring and management dashboard for the Truth-First Search system.

## Features

- **System Overview**: Real-time metrics and health status
- **Metrics Visualization**: Truth score trends, component scores, and performance metrics
- **A/B Testing**: Experiment management and results analysis
- **Alerts Management**: System alerts and notifications
- **Document Browser**: Search and analyze scored documents

## Tech Stack

- **React 18** with TypeScript
- **Material-UI (MUI)** for components
- **Recharts** for data visualization
- **React Query** for data fetching
- **React Router** for navigation
- **Vite** for build tooling

## Getting Started

### Prerequisites

- Node.js 18+
- npm or yarn

### Installation

```bash
cd dashboard
npm install
```

### Development

```bash
npm run dev
```

The dashboard will be available at http://localhost:5173

### Build for Production

```bash
npm run build
```

Output will be in the `dist/` directory.

### Preview Production Build

```bash
npm run preview
```

## Configuration

Create a `.env` file in the dashboard directory:

```env
VITE_API_URL=http://localhost:8000
VITE_OPENSEARCH_URL=https://localhost:9200
```

## Project Structure

```
dashboard/
├── src/
│   ├── components/     # Reusable UI components
│   │   └── Layout.tsx
│   ├── pages/          # Page components
│   │   ├── Dashboard.tsx
│   │   ├── Metrics.tsx
│   │   ├── Experiments.tsx
│   │   ├── Alerts.tsx
│   │   └── Documents.tsx
│   ├── services/       # API services
│   ├── utils/          # Utility functions
│   └── App.tsx         # Main app component
├── public/             # Static assets
├── package.json
└── vite.config.ts
```

## API Integration

The dashboard expects a REST API with the following endpoints:

- `GET /api/metrics` - System metrics
- `GET /api/experiments` - A/B test experiments
- `GET /api/alerts` - System alerts
- `GET /api/documents` - Scored documents
- `POST /api/experiments/{id}/start` - Start experiment
- `POST /api/alerts/{id}/acknowledge` - Acknowledge alert

See the API documentation for full details.

## Development

### Adding a New Page

1. Create component in `src/pages/`
2. Add route in `src/App.tsx`
3. Add navigation item in `src/components/Layout.tsx`

### Adding API Integration

1. Create service file in `src/services/`
2. Use React Query hooks for data fetching
3. Handle loading and error states

## Deployment

### Docker

```dockerfile
FROM node:18-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

### Nginx Configuration

```nginx
server {
    listen 80;
    server_name _;
    root /usr/share/nginx/html;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api {
        proxy_pass http://api:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## Contributing

1. Follow TypeScript best practices
2. Use Material-UI components
3. Maintain responsive design
4. Add proper error handling
5. Write meaningful commit messages

## License

MIT
