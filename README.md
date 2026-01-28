# Zip-to-ipa

A web application with API to convert ZIP files to IPA files, available in both Python (Flask) and Node.js (Express) versions.

## Publishing the Website

The Node.js version is configured for easy deployment to Vercel.

### Deploy to Vercel

1. Sign up for [Vercel](https://vercel.com) if you haven't.
2. Connect your GitHub repository.
3. Vercel will detect the `vercel.json` and deploy automatically.
4. Your site will be live at a URL like `https://zip-to-ipa.vercel.app`.

The website name will be based on your Vercel project settings.

## Python Version (Flask)

### Local Development

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the application:
   ```bash
   python app.py
   ```

The app will run on http://localhost:5000

### Deployment

See deployment options above.

## Node.js Version (Express)

### Local Development

1. Install dependencies:
   ```bash
   npm install
   ```

2. Run the application:
   ```bash
   npm start
   ```

The app will run on http://localhost:3000

### Deployment

Configured for Vercel. See publishing section above.

## Usage

### Web Interface

Visit the deployed URL in your browser. Upload a ZIP file, and download the converted IPA file.

### API

Send a POST request to `/api/convert` with the ZIP file as `file` parameter.

Example using curl:
```bash
curl -X POST -F "file=@example.zip" https://your-deployed-url/api/convert -o output.ipa
```

## Description

IPA (iOS App Store Package) files are essentially ZIP archives with a different extension, used for distributing iOS applications. This tool copies the ZIP file and renames it to have a `.ipa` extension.

## Requirements

- For Python: Python 3.x, Flask, Werkzeug
- For Node.js: Node.js, Express, Multer

## Note

Ensure the ZIP file contains the proper iOS app structure (Payload folder with .app bundle) for it to be a valid IPA file.