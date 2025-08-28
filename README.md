# JKB Finance Insights

A comprehensive financial insights management system with AI-powered analysis capabilities, built using FastAPI, SQLite, and OpenAI integration.

## 🚀 Features

### Core Functionality
- **Financial Insights Management**: Add, edit, view, and delete financial insights
- **AI-Powered Analysis**: Automated text and image analysis using OpenAI API
- **Multi-Source Integration**: Support for various financial data sources (TD IDEAS, NEWS, OPINIONS)
- **Real-time Updates**: Live market data updates and AI analysis
- **Responsive Web Interface**: Modern, mobile-friendly UI built with Bootstrap

### AI Analysis Capabilities
- **Text Analysis**: AI-powered analysis of financial content using custom prompts
- **Image Analysis**: Technical chart analysis using OpenAI's multimodal API
- **Comprehensive Summaries**: Structured AI summaries with actionable insights
- **Confidence Scoring**: AI-generated confidence levels for recommendations
- **Event Timing**: Predicted event timing for market movements
- **Support/Resistance Levels**: AI-identified key price levels

### Technical Features
- **FastAPI Backend**: High-performance, async web framework
- **SQLite Database**: Lightweight, file-based database
- **Modular Architecture**: Clean separation of concerns with dedicated modules
- **Environment Configuration**: Secure configuration management
- **Server Management**: Robust server control scripts with auto-reload

## 🛠️ Technology Stack

- **Backend**: Python 3.13+, FastAPI, Uvicorn
- **Database**: SQLite with SQLAlchemy-style operations
- **AI Integration**: OpenAI API (GPT-4, GPT-5, Responses API)
- **Frontend**: HTML5, CSS3, JavaScript, Bootstrap 5
- **Server**: Uvicorn with auto-reload for development
- **Environment**: Virtual environment with dependency management

## 📋 Prerequisites

- Python 3.13 or higher
- OpenAI API key
- Virtual environment (recommended)

## 🚀 Installation

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd jkbFinanceInsights
   ```

2. **Create and activate virtual environment**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   cp env.example .env
   # Edit .env with your OpenAI API keys and configuration
   ```

## ⚙️ Configuration

Create a `.env` file with the following variables:

```env
# OpenAI Configuration
OPENAI_API_KEY=your-openai-api-key-here
OPENAI_SUMMARY_MODEL=gpt-5
OPENAI_PROMPT1_ID=your-prompt1-id-here
OPENAI_PROMPT1_VERSION_ID=your-prompt1-version-id-here
OPENAI_PROMPT2_ID=your-prompt2-id-here
OPENAI_PROMPT2_VERSION_ID=your-prompt2-version-id-here

# Server Configuration
SERVER_HOST=127.0.0.1
SERVER_PORT=8000
SERVER_RELOAD=true
```

## 🚀 Usage

### Starting the Server

#### Option 1: Using the server management script
```bash
# Start in production mode
./start.sh

# Start in development mode with auto-reload
./dev.sh

# Restart server
./restart.sh

# Stop server
./stop.sh

# Check server status
./status.sh

# View configuration
./config.sh
```

#### Option 2: Direct uvicorn command
```bash
# Development mode with auto-reload
uvicorn main:app --host 127.0.0.1 --port 8000 --reload

# Production mode
uvicorn main:app --host 127.0.0.1 --port 8000
```

### Accessing the Application

- **Main Terminal**: http://localhost:8000/
- **Add Insight**: http://localhost:8000/add
- **View Insight**: http://localhost:8000/insight/{id}
- **Edit Insight**: http://localhost:8000/edit-insight/{id}
- **API Endpoints**: http://localhost:8000/api/

## 📁 Project Structure

```
jkbFinanceInsights/
├── main.py                 # FastAPI application and routes
├── ai_worker.py           # AI analysis orchestration
├── items_management.py    # Database CRUD operations
├── fake_data.py           # Sample data generation
├── database_schema.py     # Database schema management
├── config.py              # Configuration management
├── server.py              # Server management utilities
├── requirements.txt       # Python dependencies
├── .env                   # Environment variables (not in git)
├── .gitignore            # Git ignore rules
├── static/               # Static assets (CSS, JS)
├── templates/            # HTML templates
└── *.sh                  # Server management scripts
```

## 🔧 API Endpoints

### Web Routes
- `GET /` - Main terminal view
- `GET /add` - Add new insight form
- `POST /add` - Create new insight
- `GET /insight/{id}` - View insight details
- `GET /edit-insight/{id}` - Edit insight form
- `POST /edit-insight/{id}` - Update insight

### API Routes
- `GET /api/insights` - List all insights
- `POST /api/insights` - Create insight via API
- `POST /api/update-market-data` - Trigger AI analysis
- `GET /api/feeds` - Get available feed types

## 🤖 AI Analysis Workflow

1. **Text Analysis**: Uses `OPENAI_PROMPT1_ID` for content analysis
2. **Image Analysis**: Uses `OPENAI_SUMMARY_MODEL` for chart analysis
3. **Summary Generation**: Uses `OPENAI_PROMPT2_ID` for final insights
4. **Data Processing**: Parses JSON responses and updates database
5. **Field Updates**: Updates all AI-related fields including confidence and timing

## 🗄️ Database Schema

### Insights Table
- **Basic Fields**: id, timeFetched, timePosted, type, title, content, symbol, exchange, imageURL
- **AI Fields**: AIImageSummary, AISummary, AIAction, AIConfidence, AIEventTime, AILevels

### Feed Names Table
- **Structure**: name, description, created_at
- **Default Feeds**: TD IDEAS RECENT, TD IDEAS POPULAR, TD OPINIONS, TD NEWS

## 🔒 Security & Best Practices

- **Environment Variables**: Sensitive data stored in `.env` (not in git)
- **Input Validation**: Pydantic models for data validation
- **Error Handling**: Comprehensive error handling and logging
- **Database Security**: Parameterized queries to prevent SQL injection

## 🧪 Testing

The application includes comprehensive testing capabilities:

```bash
# Test AI worker functions
python3 -c "from ai_worker import do_ai_summary; print('AI functions working')"

# Test database operations
python3 -c "from items_management import get_all_insights; print('Database working')"

# Test configuration
python3 -c "from config import get_config_summary; print(get_config_summary())"
```

## 🚀 Deployment

### Development
- Use `./dev.sh` for development with auto-reload
- Debug logging enabled
- Hot reload on file changes

### Production
- Use `./start.sh` for production deployment
- Disable debug logging
- Set appropriate environment variables

## 📝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Support

For support and questions:
- Check the documentation
- Review the code comments
- Open an issue on GitHub

## 🔄 Recent Updates

- ✅ **Edit Functionality**: Full CRUD operations for insights
- ✅ **AI Integration**: Complete OpenAI API integration
- ✅ **Symbol/Exchange Support**: Enhanced data fields
- ✅ **Server Management**: Robust server control scripts
- ✅ **Configuration Management**: Environment-based configuration
- ✅ **Database Schema**: Optimized schema with AI fields

---

**Built with ❤️ for financial insights and AI-powered analysis**
