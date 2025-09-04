# 💰 SaaS Pricing Scraper

A powerful web application that extracts pricing plans from websites with a beautiful dark theme UI. Built with Python Flask and modern web technologies.

## ✨ Features

- **Single Domain Scraping**: Input a single domain to extract pricing information
- **Bulk Scraping**: Upload a CSV file or enter multiple domains for batch processing
- **Real-time Results**: View scraping progress and results in real-time
- **CSV Export**: Download scraped data as a CSV file
- **Modern Dark UI**: Beautiful gradient design with smooth animations
- **Responsive Design**: Works perfectly on desktop and mobile devices

## 🚀 Quick Start

### Prerequisites

- Python 3.7 or higher
- pip (Python package installer)

### Installation

1. **Clone or download the project**
   ```bash
   git clone <repository-url>
   cd SaaS-Pricing-Scraper
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**
   ```bash
   python app.py
   ```

4. **Open your browser**
   Navigate to `http://localhost:5000`

## 📖 Usage

### Single Domain Scraping

1. Click on the "Single Domain" tab
2. Enter a domain URL (e.g., `example.com` or `https://example.com`)
3. Click "Scrape Pricing"
4. View the results in the table below

### Bulk Scraping

#### Option 1: CSV File Upload
1. Click on the "Bulk Scraping" tab
2. Click "Choose CSV File" and select your CSV file
3. The CSV should contain one domain per row in the first column
4. Click "Start Bulk Scraping"

#### Option 2: Text Input
1. Click on the "Bulk Scraping" tab
2. Enter domains in the text area (one per line)
3. Click "Start Bulk Scraping"

### Downloading Results

- After scraping is complete, click the "Download CSV" button
- The CSV file will contain: URL, Plan Name, Price, Billing Period, Features, Timestamp, and Error columns

## 📊 CSV Format

### Input CSV (for bulk scraping)
```
example1.com
example2.com
example3.com
```

### Output CSV (downloaded results)
```csv
URL,Plan Name,Price,Billing Period,Features,Timestamp,Error
https://example1.com,Pro,$29.99,Monthly,"Feature 1; Feature 2; Feature 3",2024-01-15 10:30:00,
https://example2.com,Basic,$9.99,Monthly,"Feature A; Feature B",2024-01-15 10:31:00,
```

## 🔧 How It Works

The scraper uses intelligent pattern matching to extract pricing information:

1. **Price Detection**: Looks for common price patterns ($XX.XX, XX USD, etc.)
2. **Plan Names**: Identifies common plan types (Basic, Pro, Premium, Enterprise, etc.)
3. **Billing Periods**: Detects billing cycles (monthly, yearly, quarterly, etc.)
4. **Features**: Extracts feature lists from pricing sections
5. **Error Handling**: Gracefully handles websites that can't be scraped

## 🛠️ Technical Details

- **Backend**: Python Flask
- **Frontend**: HTML5, CSS3, JavaScript (Vanilla)
- **Web Scraping**: BeautifulSoup4, Requests
- **Data Processing**: Pandas
- **File Handling**: CSV processing with Python's built-in csv module

## 📁 Project Structure

```
SaaS-Pricing-Scraper/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── README.md             # This file
└── templates/
    └── index.html        # Main HTML template
```

## ⚠️ Important Notes

- **Rate Limiting**: The scraper includes a 1-second delay between requests to be respectful to websites
- **User Agent**: Uses a proper browser user agent to avoid being blocked
- **Error Handling**: Gracefully handles network errors and invalid websites
- **File Size Limit**: Maximum CSV file size is 16MB

## 🎨 Customization

### Styling
The dark theme can be customized by modifying the CSS in `templates/index.html`. The main color variables are:
- Primary gradient: `#00d4ff` to `#ff6b6b`
- Background: `#1a1a2e` to `#0f3460`
- Text: `#ffffff`

### Scraping Logic
The scraping logic can be enhanced by modifying the `extract_pricing_info()` function in `app.py`. You can add more selectors or patterns for better extraction.

## 🤝 Contributing

Feel free to submit issues and enhancement requests!

## 📄 License

This project is open source and available under the MIT License.

## 🆘 Troubleshooting

### Common Issues

1. **"Module not found" errors**
   - Make sure you've installed all dependencies: `pip install -r requirements.txt`

2. **Port already in use**
   - Change the port in `app.py`: `app.run(debug=True, host='0.0.0.0', port=5001)`

3. **CSV upload not working**
   - Ensure your CSV file has domains in the first column
   - Check that the file is not corrupted

4. **No results found**
   - Some websites may block scraping attempts
   - Try different domains or check the error column for details

### Getting Help

If you encounter any issues, please check the error messages in the application or create an issue in the repository.
