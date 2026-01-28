const express = require('express');
const multer = require('multer');
const path = require('path');
const fs = require('fs');

const app = express();
const port = process.env.PORT || 3000;

// Configure multer for file uploads
const storage = multer.diskStorage({
  destination: (req, file, cb) => {
    cb(null, '/tmp/'); // Use temp directory
  },
  filename: (req, file, cb) => {
    cb(null, Date.now() + path.extname(file.originalname));
  }
});

const upload = multer({
  storage: storage,
  fileFilter: (req, file, cb) => {
    if (file.mimetype === 'application/zip' || path.extname(file.originalname).toLowerCase() === '.zip') {
      cb(null, true);
    } else {
      cb(new Error('Only ZIP files are allowed'));
    }
  }
});

// Serve static files (for a simple HTML page if needed)
app.use(express.static('public'));

// Home page with upload form
app.get('/', (req, res) => {
  res.send(`
    <!DOCTYPE html>
    <html>
    <head>
        <title>Zip to IPA Converter</title>
    </head>
    <body>
        <h1>Convert ZIP to IPA</h1>
        <form action="/convert" method="post" enctype="multipart/form-data">
            <input type="file" name="file" accept=".zip" required>
            <button type="submit">Convert</button>
        </form>
    </body>
    </html>
  `);
});

// Convert endpoint
app.post('/convert', upload.single('file'), (req, res) => {
  if (!req.file) {
    return res.status(400).send('No file uploaded');
  }

  const inputPath = req.file.path;
  const outputFilename = path.basename(req.file.originalname, '.zip') + '.ipa';
  const outputPath = path.join('/tmp/', outputFilename);

  // Copy file and rename to .ipa
  fs.copyFile(inputPath, outputPath, (err) => {
    if (err) {
      console.error(err);
      return res.status(500).send('Error converting file');
    }

    // Send the file
    res.download(outputPath, outputFilename, (err) => {
      if (err) {
        console.error(err);
      }
      // Clean up files
      fs.unlink(inputPath, () => {});
      fs.unlink(outputPath, () => {});
    });
  });
});

// API endpoint
app.post('/api/convert', upload.single('file'), (req, res) => {
  if (!req.file) {
    return res.status(400).json({ error: 'No file uploaded' });
  }

  const inputPath = req.file.path;
  const outputFilename = path.basename(req.file.originalname, '.zip') + '.ipa';
  const outputPath = path.join('/tmp/', outputFilename);

  fs.copyFile(inputPath, outputPath, (err) => {
    if (err) {
      console.error(err);
      return res.status(500).json({ error: 'Error converting file' });
    }

    res.download(outputPath, outputFilename, (err) => {
      if (err) {
        console.error(err);
      }
      fs.unlink(inputPath, () => {});
      fs.unlink(outputPath, () => {});
    });
  });
});

// For Vercel deployment
module.exports = app;

// For local development
if (require.main === module) {
  app.listen(port, () => {
    console.log(`Server running on port ${port}`);
  });
}