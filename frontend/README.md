# Evolve Frontend

This directory contains a TypeScript scaffold for a future web-based frontend. Currently, the primary interface is the Streamlit application (`app.py` in the root directory).

## Current Status

The frontend is a minimal TypeScript placeholder. The main user interface is implemented using **Streamlit** (see `../app.py`).

## Structure

```
frontend/
├── package.json       # Node.js dependencies and scripts
├── tsconfig.json      # TypeScript configuration
├── src/
│   └── index.ts      # Entry point (placeholder)
└── README.md         # This file
```

## Future Development

This scaffold is prepared for building a custom web frontend that could:
- Connect to the FastAPI backend (`../api.py`)
- Provide real-time evolution monitoring
- Offer interactive code editing and visualization
- Display detailed fitness metrics and generation history

### To Get Started

1. Install Node.js dependencies:
   ```bash
   npm install
   ```

2. Type-check the TypeScript code:
   ```bash
   npm run typecheck
   ```

3. Build the project:
   ```bash
   npm run build
   ```

## Using the Current UI

For now, use the Streamlit interface from the project root:

```bash
cd ..
streamlit run app.py
```

## Contributing

If you'd like to build out the web frontend:
1. Add React, Vue, or your preferred framework
2. Implement API client for `../api.py` endpoints
3. Create visualization components for fitness evolution
4. Add real-time experiment monitoring

See `../CONTRIBUTING.md` for more details.

