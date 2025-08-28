# Finance Insights Web App

A simple, user-friendly web application for managing finance insights with AI analysis capabilities.

## Features

- **Simple Interface**: Clean, responsive design using Bootstrap
- **SQLite Database**: Lightweight database storage
- **AI Integration Ready**: Fields for AI-generated summaries, actions, and analysis
- **CRUD Operations**: Create, read, update, and delete insights
- **REST API**: RESTful endpoints for programmatic access
- **Image Support**: Display images with insights
- **Real-time UI**: Interactive features with JavaScript

## Database Schema

The application uses a single SQLite table with the following fields:

- `id`: Primary key (auto-increment)
- `timeFetched`: When the insight was fetched
- `timePosted`: When the insight was posted
- `type`: Category of insight (News, Analysis, Market Update, etc.)
- `title`: Title of the insight
- `content`: Main content/description
- `imageURL`: Optional image URL
- `AITextSummary`: AI-generated text summary
- `AIImageSummary`: AI-generated image summary
- `AISummary`: Overall AI summary
- `AIAction`: Recommended action from AI
- `AIConfidence`: Confidence level (0-1)
- `AIEventTime`: AI-predicted event time
- `AILevels`: AI risk/importance levels

## Quick Start

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the Application**:
   ```bash
   python main.py
   ```

3. **Open Your Browser**:
   Navigate to `http://localhost:8000`

## API Endpoints

- `GET /`: Web interface home page
- `GET /add`: Add new insight form
- `POST /add`: Create new insight
- `GET /insight/{id}`: View insight details
- `DELETE /insight/{id}`: Delete insight
- `GET /api/insights`: Get all insights (JSON)
- `POST /api/insights`: Create insight via API (JSON)

## Usage

### Adding Insights
1. Click "Add New Insight" button
2. Fill in the required fields (Type, Title, Content)
3. Optionally add AI analysis data
4. Submit the form

### Viewing Insights
- Home page shows all insights in a card layout
- Click "View Details" to see full insight information
- AI summaries and actions are highlighted

### Deleting Insights
- Click the trash icon on any insight card
- Confirm deletion in the popup dialog

## Development

The application is built with:
- **FastAPI**: Modern Python web framework
- **SQLite**: Embedded database
- **Jinja2**: Template engine
- **Bootstrap 5**: CSS framework
- **Vanilla JavaScript**: Frontend interactions

## File Structure

```
jkbFinanceInsights/
├── main.py              # Main FastAPI application
├── requirements.txt     # Python dependencies
├── finance_insights.db  # SQLite database (created automatically)
├── templates/           # HTML templates
│   ├── base.html       # Base template
│   ├── index.html      # Home page
│   ├── add.html        # Add insight form
│   └── detail.html     # Insight details
└── static/             # Static files
    ├── style.css       # Custom styles
    └── script.js       # JavaScript functionality
```

## Contributing

This is a minimal, easy-to-use application designed for simplicity. Feel free to extend it with additional features as needed.
