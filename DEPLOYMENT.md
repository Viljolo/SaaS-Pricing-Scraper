# Deployment Guide

## Vercel Deployment

This application is configured to deploy on Vercel with the following setup:

### File Structure
```
SaaS-Pricing-Scraper/
├── api/
│   └── index.py          # Flask API serverless function
├── vercel.json           # Vercel configuration
├── requirements.txt      # Python dependencies
├── public/
│   └── index.html        # Static frontend
└── domains.csv           # Sample CSV file
```

### Configuration

1. **vercel.json**: Routes API calls to serverless function and serves static files
2. **api/index.py**: Flask API serverless function with CORS support and proper error handling
3. **requirements.txt**: Minimal dependencies for Vercel compatibility

### API Endpoints

- `GET /api/health` - Health check
- `POST /api/scrape_single` - Single domain scraping
- `POST /api/scrape_bulk` - Bulk domain scraping
- `GET /api/get_results` - Get scraping results
- `POST /api/stop_scraping` - Stop bulk scraping
- `GET /api/download_csv` - Download results as CSV

### Deployment Steps

1. Push code to GitHub
2. Connect repository to Vercel
3. Vercel will automatically detect Python and install dependencies
4. The app should deploy successfully

### Troubleshooting

If you get 404 errors:
1. Check that `vercel.json` is properly configured
2. Ensure all API routes have `/api/` prefix
3. Verify static files are in `public/` directory
4. Check Vercel build logs for Python errors

### Local Testing

```bash
# Install dependencies
py -m pip install -r requirements.txt

# Run Flask app (for local testing)
py api/index.py

# Test API
curl http://localhost:5000/api/health
```
