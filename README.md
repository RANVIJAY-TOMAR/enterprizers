# Excel Summarizer App

A web application that analyzes Excel/CSV files and provides client-wise and zone-wise status summaries.

## Features

- Upload Excel (.xlsx, .xls) or CSV files
- Automatic column detection and normalization
- Client-level summary with completion percentages
- Zone-level rollup summary
- Downloadable Excel report with multiple sheets
- Modern React + Tailwind UI
- Handles large files (~50k rows × 100 columns)

## Project Structure

```
├── server/
│   └── app.py              # Flask backend server
├── client/                  # React frontend
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── lib/           # API utilities
│   │   ├── App.jsx        # Main app component
│   │   └── main.jsx       # Entry point
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   └── postcss.config.js
├── requirements.txt         # Python dependencies
└── README.md
```

## Setup Instructions

### Backend (Flask)

1. **Create and activate virtual environment:**
   ```bash
   python -m venv .venv
   .venv\Scripts\activate  # Windows
   # or
   source .venv/bin/activate  # Mac/Linux
   ```

2. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the Flask server:**
   ```bash
   cd server
   python app.py
   ```
   The server will run on http://127.0.0.1:5000

### Frontend (React)

1. **Install Node.js dependencies:**
   ```bash
   cd client
   npm install
   ```

2. **Start development server:**
   ```bash
   npm run dev
   ```
   The frontend will run on http://localhost:5173

## Usage

1. Open http://localhost:5173 in your browser
2. Upload an Excel/CSV file with columns: Zone, Client Name, Order Status
3. View the generated summaries
4. Download the Excel report with detailed breakdowns

## API Endpoints

- `POST /api/upload` - Upload and analyze Excel/CSV files
- `GET /api/report/<key>` - Download generated Excel reports

## Dependencies

### Backend
- Flask 2.0.1
- flask-cors 3.0.10
- pandas 1.1.5
- openpyxl 3.0.7
- Werkzeug 2.0.1

### Frontend
- React 18.3.1
- Vite 5.4.2
- Tailwind CSS 3.4.10

## Notes

- The app uses older package versions to ensure compatibility on Windows without requiring C++ compilers
- For production, consider replacing the in-memory report cache with Redis or S3
- The app automatically normalizes column names and status values for better compatibility
