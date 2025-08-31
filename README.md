# Amazon.de Automation Script

This Python script automates various tasks on Amazon.de using Playwright, including login, product browsing, wishlist management, and Prime cancellation.

## Features

- Logs into Amazon.de using provided credentials
- Browses 5 random product pages with human-like behavior
- Adds 2 products to wishlist
- Attempts to cancel Prime membership if active
- Routes traffic through proxy servers
- Comprehensive error handling with retry logic
- Structured JSON logging with timestamps
- Screenshot capture on errors

## Requirements

- Python 3.8+
- Playwright
- Internet connection
- Valid Amazon.de account credentials
- Proxy server access

## Setup Instructions

1. **Clone or download this project**
   ```bash
   cd amazon-test
   ```

2. **Create a virtual environment (recommended)**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Install Playwright browsers**
   ```bash
   playwright install chromium
   ```

5. **Create screenshots directory**
   ```bash
   mkdir -p screenshots
   ```

## Configuration

The script includes pre-configured:
- Amazon.de account credentials
- Proxy server settings
- German language selectors for Amazon.de

## Running the Script

```bash
python main.py
```

The script will:
1. Select a random account and proxy from the configured lists
2. Launch a visible Chrome browser (headful mode)
3. Execute all automation tasks
4. Generate a `log.json` file with detailed execution logs
5. Save error screenshots to the `screenshots/` directory if needed

## Output Files

- **log.json**: Structured log file with timestamps and status for each step
- **screenshots/**: Directory containing error screenshots (if any errors occur)

## Error Handling

- Each failed action is retried once automatically
- Screenshots are captured on persistent failures
- All errors are logged with detailed information
- Script continues execution when possible

## Log Structure

Each log entry contains:
```json
{
    "step": "Login",
    "status": "success",
    "timestamp": "2024-01-01T12:00:00.000000",
    "details": "Successfully logged in."
}
```

Status levels: `info`, `success`, `warning`, `error`, `critical`

## Security Notes

- Credentials are included in the script for testing purposes
- In production, use environment variables or secure credential storage
- Proxy credentials are embedded for the provided test proxies

## Troubleshooting

1. **Browser doesn't launch**: Ensure Playwright browsers are installed
2. **Login fails**: Check credentials and network connectivity
3. **Proxy errors**: Verify proxy server availability
4. **Element not found**: Amazon may have updated their page structure

## Development Time

Estimated development time: 4-5 hours including testing and documentation.
