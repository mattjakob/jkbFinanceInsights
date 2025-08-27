# JKB Finance Terminal

A professional financial insights terminal with AI-powered analysis, designed to look and feel like a professional trading platform.

## Features

### 🎛️ Control Panel
- **SYMBOL**: Select trading pairs (BITSTAMP:BTCUSD, BINANCE:BTCUSDT, COINBASE:BTC-USD)
- **FEED TYPE**: Filter by content type (ALL, NEWS, ANALYSIS, ALERTS)
- **INTERVAL**: Set update frequency (60s, 5m, 15m, 1h)
- **ITEMS**: Choose number of displayed items (10, 25, 50, 100)
- **AI**: Toggle AI analysis on/off
- **UPDATE**: Manual refresh button with loading states

### 🤖 AI Engine Status
Real-time display of AI processing status with timestamps and analysis IDs.

### 📊 Financial Insights Table
- **TYPE**: Visual indicators for different content types (news, analysis, location)
- **AGE**: Time elapsed since posting
- **TITLE**: Financial insight headlines and content
- **AI SUMMARY**: AI-generated analysis and insights
- **ACTION**: Trading recommendations (BUY, SELL, HOLD)
- **CONF%**: Confidence percentage for AI recommendations
- **EVENT TIME**: Predicted or actual event timing
- **LEVELS**: Support, resistance, target, stop-loss, and invalidation levels

### 🔄 Interactive Features
- Loading spinners for incomplete AI analysis
- Row hover effects and click interactions
- Auto-refresh functionality
- Responsive design for all screen sizes

## Screenshots

The interface closely matches the professional JKB Finance Terminal design with:
- Dark terminal theme
- Professional control panel layout
- Real-time AI engine status
- Comprehensive financial data table
- Loading states and interactive elements

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd jkbFinanceInsights
```

2. Create a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the application:
```bash
python main.py
```

5. Open your browser and navigate to `http://localhost:8000`

## Technology Stack

- **Backend**: FastAPI with Python 3.13+
- **Frontend**: HTML5, CSS3, JavaScript (ES6+)
- **Styling**: Bootstrap 5 with custom terminal theme
- **Database**: SQLite with SQLAlchemy-style queries
- **Icons**: Bootstrap Icons for professional look

## Database Schema

The application uses a SQLite database with the following structure:

```sql
CREATE TABLE insights (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timeFetched TEXT NOT NULL,
    timePosted TEXT NOT NULL,
    type TEXT NOT NULL,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    imageURL TEXT,
    AITextSummary TEXT,
    AIImageSummary TEXT,
    AISummary TEXT,
    AIAction TEXT,
    AIConfidence REAL,
    AIEventTime TEXT,
    AILevels TEXT
);
```

## API Endpoints

- `GET /` - Main terminal interface
- `GET /add` - Add new insight form
- `POST /add` - Create new insight
- `GET /insight/{id}` - View insight details
- `DELETE /insight/{id}` - Delete insight
- `GET /api/insights` - JSON API for insights
- `POST /api/insights` - Create insight via API

## Customization

### Styling
The interface uses CSS custom properties for easy theming:
- `--terminal-bg`: Main background color
- `--terminal-accent`: Accent color (green)
- `--terminal-text`: Text color
- `--terminal-border`: Border colors

### JavaScript Features
- Control panel interactions
- Table row interactions
- Auto-refresh functionality
- Loading state management

## Server Management

The project includes convenient shell scripts for managing the server:

- **`./start.sh`** - Start the server in production mode (automatically stops any existing server first)
- **`./start.sh dev`** - Start the server in development mode with auto-reload
- **`./dev.sh`** - Start the server in development mode with auto-reload (recommended for development)
- **`./stop.sh`** - Stop the running server
- **`./restart.sh`** - Restart the server in production mode
- **`./restart.sh dev`** - Restart the server in development mode with auto-reload
- **`./status.sh`** - Check server status
- **`./config.sh`** - Show current configuration settings

You can also use the Python server management script directly:

```bash
python3 server.py start    # Start server in production mode
python3 server.py dev      # Start server in development mode with auto-reload
python3 server.py stop     # Stop server
python3 server.py restart  # Restart server in production mode
python3 server.py restart --reload  # Restart server in development mode
python3 server.py status   # Show status
```

### Development Mode Features

- **Auto-reload**: Server automatically restarts when Python files change
- **File watching**: Monitors all files in the current directory for changes
- **Hot reload**: No need to manually restart the server during development
- **Uvicorn integration**: Uses uvicorn with `--reload` flag for optimal development experience

The server management interface provides clean, Docker-like text output without emojis or unnecessary visual clutter.

## Configuration Management

The application uses environment variables for configuration, loaded from a `.env` file. If no `.env` file exists, sensible defaults are used.

### Environment Variables

Create a `.env` file in the project root with the following settings. You can copy from `env.example`:

```bash
cp env.example .env
```

```bash
# Server Configuration
SERVER_HOST=127.0.0.1
SERVER_PORT=8000
SERVER_RELOAD=true
SERVER_WORKERS=1

# Database Configuration
DATABASE_URL=finance_insights.db

# Environment
ENVIRONMENT=development
DEBUG=true

# Uvicorn Configuration
UVICORN_HOST=127.0.0.1
UVICORN_PORT=8000
UVICORN_RELOAD=true
UVICORN_RELOAD_DIR=.
UVICORN_LOG_LEVEL=info
```

### Configuration Commands

- **`./config.sh`** or **`python3 server.py config`** - Show current configuration
- **`python3 server.py config`** - Display all configuration values and their sources

### Configuration Priority

1. Environment variables (highest priority)
2. `.env` file
3. Default values (lowest priority)

This allows for flexible deployment configurations across different environments.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support or questions, please open an issue in the GitHub repository.
