# Seedr API Wrapper & Web Interface

A logical wrapper around the Seedr.cc API, providing enhanced features like smart torrent adding, automated downloads, and a local web interface for managing your Seedr account.

## 🚀 Features

- **FastAPI Powered**: High-performance, modern Python web framework.
- **Smart Torrent Adding**: Automatically checks for available storage space before adding torrents to prevent quota errors.
- **Auto-Download**: One-step process to add a torrent, wait for it to process on Seedr, and immediately get direct download links.
- **Folder Management**: Create, rename, delete, and list folders recursively.
- **File Management**: Rename, delete, and search files; fetch direct download links.
- **Device & Account Info**: View account storage/bandwidth usage and manage authorized devices.
- **VLC Integration**: Directly stream or play downloaded files in your local VLC media player (supports playlists).
- **Swagger Documentation**: Interactive API documentation available at `/docs` or `/redoc`.

## 📋 Prerequisites

- Python 3.8+
- [Seedr.cc](https://www.seedr.cc/) account
- VLC Media Player (optional, for streaming features)

## 🛠️ Installation

1.  Clone the repository:
    ```bash
    git clone <repository-url>
    cd <repository-name>
    ```

2.  Create a virtual environment (recommended):
    ```bash
    python -m venv venv
    # Windows
    .\venv\Scripts\activate
    # Linux/Mac
    source venv/bin/activate
    ```

3.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

## ⚙️ Configuration

1.  Copy the example environment file:
    ```bash
    cp .env.example .env
    ```

2.  Edit `.env` and add your configuration:
    ```ini
    # Server Settings
    HOST=0.0.0.0
    PORT=5000
    DEBUG=True
    LOG_LEVEL=INFO

    # VLC Path (Adjust if installed in a different location)
    VLC_PATH="C:\Program Files\VideoLAN\VLC\vlc.exe"

    # Default Auth (Optional: for personal single-user mode)
    DEFAULT_AUTH=False
    DEFAULT_USERNAME=your_email
    DEFAULT_PASSWORD=your_password
    ```

## ▶️ Usage

1.  Start the application:
    ```bash
    uvicorn main:app --reload
    # Or generically:
    python main.py
    ```

2.  Open your browser and navigate to:
    - **API Docs (Swagger)**: [http://localhost:5000/docs](http://localhost:5000/docs)
    - **API Docs (Redoc)**: [http://localhost:5000/redoc](http://localhost:5000/redoc)

## 📚 API Documentation

For detailed information about all available endpoints, parameters, and response formats, please refer to the [API Reference](docs/API_REFERENCE.md) or use the interactive Swagger UI.

## 🧩 Project Structure

- `main.py`: Main FastAPI application entry point.
- `routers/`: Contains API route definitions (auth, account, files, torrents, vlc).
- `utils/`: Helper utilities for Seedr client management.
- `config.py`: Application configuration using Pydantic.

## 📄 License

[MIT License](LICENSE)
