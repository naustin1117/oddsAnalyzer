# NHL Odds Analyzer - Frontend

React frontend for the NHL Odds Analyzer application.

## Quick Start

**Run the frontend server:**
```bash
cd frontend
npm run dev
```

The app will be available at **http://localhost:5173**

**Note:** Make sure the backend API is running on http://localhost:8000 before starting the frontend.

## Setup

1. Install dependencies:
```bash
npm install
```

2. Make sure the API is running on `http://localhost:8000`

3. Start the development server:
```bash
npm run dev
```

The app will be available at `http://localhost:5173`

## Environment Variables

Create a `.env` file (already provided) with:

```
VITE_API_URL=http://localhost:8000
```

## API Integration

The frontend connects to the FastAPI backend using the API utility in `src/api.js`.

The default API key for development is `dev-key-123` (configured in `src/api.js`).

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build locally

## Tech Stack

- React 18
- Vite
- CSS Modules