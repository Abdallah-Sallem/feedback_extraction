# HR Feedback Intelligence Platform

<div align="center">

![HR Feedback](https://img.shields.io/badge/HR-Feedback%20Intelligence-6366f1?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.8+-3776ab?style=flat-square&logo=python)
![Streamlit](https://img.shields.io/badge/Streamlit-Latest-FF4B4B?style=flat-square&logo=streamlit)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)
![Status](https://img.shields.io/badge/Status-Active-brightgreen?style=flat-square)

A comprehensive intelligent HR feedback system powered by advanced NLP analysis and automated document processing.

[Features](#features) • [Installation](#installation) • [Quick Start](#quick-start) • [Architecture](#architecture) • [Usage](#usage)

</div>

---

## 📋 Overview

The **HR Feedback Intelligence Platform** is a sophisticated system designed to streamline feedback collection, analysis, and reporting within HR departments. It combines optical character recognition (OCR), natural language processing (NLP), and intelligent data aggregation to extract actionable insights from HR feedback documents.

### Key Capabilities
- 📄 **Automated Document Processing** - Process multiple file formats automatically
- 🔍 **Intelligent Text Analysis** - Extract and analyze feedback using Mistral AI
- 📊 **Real-time Insights** - Generate interactive dashboards and visualizations
- 📈 **Executive Reporting** - Create professional aggregated reports
- 🔄 **Continuous Monitoring** - Real-time file system monitoring for new feedback
- 💾 **Persistent Storage** - SQLite database for feedback tracking

---

## ✨ Features

### 🤖 Intelligent Processing
- **Multi-format OCR**: Extract text from images and documents
- **Advanced NLP Analysis**: Sentiment analysis, keyword extraction, theme identification
- **Automated Classification**: Categorize feedback into themes and sentiments
- **Real-time Processing**: Continuous monitoring of watched folder for new files

### 📊 Analytics & Reporting
- **Interactive Dashboards**: Visualize feedback trends and patterns
- **Sentiment Analysis**: Understand emotional context of feedback
- **Keyword Extraction**: Identify key themes and topics
- **Executive Summaries**: Generate professional aggregated reports
- **Search Capabilities**: Full-text search across all processed feedback

### 💼 Enterprise Features
- **User-friendly Interface**: Streamlit-based web application
- **Database Management**: SQLite persistence layer
- **Configuration Management**: Environment-based settings
- **Scalable Architecture**: Modular design for easy extensions

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────┐
│         Streamlit Web Interface             │
│       (app.py - Interactive Dashboard)      │
└────────────────┬────────────────────────────┘
                 │
        ┌────────┼────────┐
        │        │        │
        ▼        ▼        ▼
    ┌────────────────────────────────┐
    │  Processing Engines            │
    ├────────────────────────────────┤
    │ • OCR Engine (ocr_engine.py)   │
    │ • Analysis Engine (analysis_)  │
    │ • Report Generator (report_)   │
    │ • Aggregation (aggregation.py) │
    └────────┬─────────────────────┘
             │
    ┌────────▼─────────┐
    │  Database Layer  │
    │  (database.py)   │
    │  SQLite Storage  │
    └──────────────────┘
             ▲
             │
    ┌────────▼──────────┐
    │ Folder Watcher    │
    │ (watcher.py)      │
    │ Real-time Monitor │
    └────────┬──────────┘
             │
    ┌────────▼──────────────────┐
    │ watched_feedback/         │
    │ (Auto-processed Files)    │
    └───────────────────────────┘
```

### Module Overview

| Module | Purpose |
|--------|---------|
| **app.py** | Main Streamlit application with UI/UX |
| **ocr_engine.py** | Extract text from images and documents |
| **analysis_engine.py** | NLP analysis using Mistral AI |
| **aggregation.py** | Compute statistical aggregations |
| **report_generator.py** | Generate executive-level reports |
| **watcher.py** | Monitor folder for new files |
| **database.py** | SQLite database operations |
| **config.py** | Configuration and environment variables |

---

## 🚀 Installation

### Prerequisites
- **Python 3.8+**
- **pip** (Python package manager)
- **Mistral AI API Key** (for NLP features)
- **Git** (for version control)

### Step 1: Clone the Repository
```bash
git clone https://github.com/yourusername/hr-feedback-platform.git
cd hr-feedback-platform
```

### Step 2: Create Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables
Create a `.env` file in the project root:
```env
# Mistral AI Configuration
MISTRAL_API_KEY=your_mistral_api_key_here

# Database Configuration
DB_PATH=hr_feedback.db

# Watched Folder for Auto-processing
WATCHED_FOLDER=watched_feedback
```

---

## 🏃 Quick Start

### Launch the Application
```bash
streamlit run app.py
```

The application will open in your default browser at `http://localhost:8501`

### Basic Workflow
1. **Upload Feedback** - Place feedback documents in the `watched_feedback/` folder
2. **Processing** - The system automatically processes new files
3. **Analysis** - View analyzed results in the dashboard
4. **Reports** - Generate executive reports from aggregated data
5. **Export** - Download insights and reports

---

## 📖 Usage

### Uploading Documents
- Supported formats: PDF, PNG, JPG, JPEG, TIFF
- Place files in the `watched_feedback/` folder
- System auto-detects and processes new files

### Processing Feedback
```python
from ocr_engine import extract_text_from_file
from analysis_engine import analyze_raw_text

# Extract text
text = extract_text_from_file('feedback.pdf')

# Analyze feedback
analysis = analyze_raw_text(text)
```

### Generating Reports
```python
from report_generator import generate_executive_report

# Create report
report = generate_executive_report(analyzed_documents)
```

### Searching Documents
Use the search interface to find specific feedback by keywords, date range, or sentiment.

---

## ⚙️ Configuration

### Environment Variables
| Variable | Description | Default |
|----------|-------------|---------|
| `MISTRAL_API_KEY` | Mistral AI API key for NLP | (required) |
| `DB_PATH` | SQLite database file path | `hr_feedback.db` |
| `WATCHED_FOLDER` | Folder for auto-processing | `watched_feedback` |

### Customization
Edit `config.py` to modify default settings:
```python
DB_PATH = os.environ.get("DB_PATH", "hr_feedback.db")
WATCHED_FOLDER = os.environ.get("WATCHED_FOLDER", "watched_feedback")
```

---

## 📁 Project Structure

```
hr_feedback_platform/
├── app.py                  # Main Streamlit application
├── config.py               # Configuration settings
├── database.py             # Database operations
├── ocr_engine.py           # Text extraction
├── analysis_engine.py      # NLP analysis
├── aggregation.py          # Data aggregation
├── report_generator.py     # Report generation
├── watcher.py              # Folder monitoring
├── requirements.txt        # Python dependencies
├── watched_feedback/       # Auto-processed files
├── hr_feedback.db          # SQLite database
├── .env                    # Environment variables (not committed)
└── README.md              # This file
```

---

## 🔐 Security Considerations

- **API Keys**: Never commit `.env` file to version control
- **Database**: Ensure `hr_feedback.db` has proper access controls
- **File Permissions**: Set appropriate permissions on `watched_feedback/` folder
- **Input Validation**: Always validate uploaded files

---

## 📊 Features in Detail

### Dashboard Components
- **Feedback Overview**: Summary statistics and trends
- **Sentiment Analysis**: Visual representation of sentiment distribution
- **Key Themes**: Extracted topics and themes
- **Timeline View**: Feedback over time
- **Search Interface**: Full-text search capabilities

### Automated Processing
- Real-time file monitoring
- Batch processing capabilities
- Error handling and logging
- Status tracking

---

## 🐛 Troubleshooting

### Database Issues
```bash
# Reset database
rm hr_feedback.db
streamlit run app.py
```

### OCR Problems
- Ensure images are clear and readable
- Supported formats: PDF, PNG, JPG, JPEG, TIFF
- Check file permissions

### API Connection
- Verify `MISTRAL_API_KEY` is set correctly
- Check internet connection
- Ensure API key has valid quota

---

## 📝 API Reference

### OCR Engine
```python
extract_text_from_file(file_path: str) -> str
```

### Analysis Engine
```python
analyze_raw_text(text: str) -> dict
```

### Aggregation
```python
compute_aggregation(documents: list) -> dict
```

### Report Generator
```python
generate_executive_report(documents: list) -> str
```

---

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 👥 Support

For support, email your-email@example.com or open an issue on GitHub.

---

## 🙏 Acknowledgments

- Built with [Streamlit](https://streamlit.io/)
- Powered by [Mistral AI](https://mistral.ai/)
- Database: [SQLite](https://www.sqlite.org/)
- Visualization: [Plotly](https://plotly.com/)

---

<div align="center">

**[⬆ back to top](#hr-feedback-intelligence-platform)**

Made with ❤️ for HR Excellence

</div>
