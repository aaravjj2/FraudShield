# FraudShield Dashboard

Real-time fraud detection dashboard with SHAP explainability visualization.

## Features

- **Live Transaction Feed**: Polls `/transactions` every 2 seconds with real-time updates
- **Manual Test Form**: Submit test transactions with custom features
- **SHAP Waterfall Visualization**: Click fraud rows to see feature contributions
- **Real-time Statistics**: Model F1, AUC-ROC, fraud rate, and latency metrics
- **Professional Fintech UI**: Dark theme, accessible, keyboard navigation

## Required data-testid Attributes (for Playwright tests)

- `transaction-feed` - Main table container
- `fraud-row` - Fraud transaction rows (red background + warning icon)
- `legit-row` - Legitimate transaction rows (green tint)
- `shap-drawer` - SHAP waterfall drawer/panel
- `shap-bar` - Individual feature bars in waterfall
- `amount-input` - Transaction amount input field
- `v1-input` - Feature V1 input field
- `v2-input` - Feature V2 input field
- `submit-btn` - Submit prediction button
- `stats-bar` - Statistics dashboard at top

## Development

```bash
# Install dependencies
npm install

# Start dev server (http://localhost:3000)
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

## Environment Variables

Create `.env` file:

```
VITE_API_URL=http://localhost:8000
```

## API Integration

The dashboard connects to the FraudShield backend at `http://localhost:8000`:

- `POST /predict` - Single transaction prediction
- `POST /batch` - Batch predictions
- `GET /transactions?limit=50&offset=0` - Recent transactions
- `GET /stats` - Model statistics
- `GET /health` - Health check

## Docker Deployment

```bash
# Build image
docker build -t fraudshield-dashboard .

# Run container
docker run -p 80:80 fraudshield-dashboard
```

## Accessibility

- ARIA labels on all interactive elements
- Keyboard navigation support (Tab, Enter, Escape)
- 4.5:1 contrast ratio minimum
- Screen reader friendly

## Browser Support

- Chrome/Edge (latest)
- Firefox (latest)
- Safari (latest)

## Tech Stack

- React 18+ with TypeScript (strict mode)
- Vite for fast development
- CSS Modules for styling
- Fetch API for HTTP calls
- No external UI library dependencies
