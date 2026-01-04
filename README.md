# Seedr API Manager

A high-performance, automated REST API wrapper for Seedr.cc, built with **FastAPI**.

This project provides a robust backend service to manage your Seedr account programmatically. It fills the gaps in the official API by adding **smart logic**, **automation workflows**, and **local device integration**.

## 🚀 Key Features

- **Smart Torrent Adding**: Pre-checks your available quota against the torrent size before adding it, preventing "Out of Storage" errors.
- **Auto-Download Workflow**: A single endpoint (`/addAndDownload`) that adds a torrent, waits for cloud processing, and returns direct download links immediately.
- **Local Playback**: detailed integration with your local VLC media player to stream or play downloaded files directly.
- **Full File Management**: Recursively list, search, rename, and delete files and folders.
- **Fast & Async**: Built on FastAPI for high concurrency and performance.

## 📚 API Documentation

Complete documentation for all endpoints is available in the [**API Reference**](docs/API_REFERENCE.md).

You can also explore the interactive API docs when the server is running:
- **Swagger UI**: `http://localhost:5000/docs`
- **ReDoc**: `http://localhost:5000/redoc`

## 🛠️ Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/hemanithin/seedr-api.git
    cd seedr-api
    ```

2.  **Set up Virtual Environment:**
    ```bash
    python -m venv venv
    # Windows
    .\venv\Scripts\activate
    # Linux/Mac
    source venv/bin/activate
    ```

3.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## ⚙️ Configuration

1.  Create your environment file:
    ```bash
    cp .env.example .env
    ```

2.  Configure `.env`:
    ```ini
    # Server
    HOST=0.0.0.0
    PORT=5000
    LOG_LEVEL=INFO

    # VLC Path (Required for playback features)
    VLC_PATH="C:\Program Files\VideoLAN\VLC\vlc.exe"

    # Default Auth (Optional)
    DEFAULT_AUTH=False
    DEFAULT_USERNAME=your_email
    DEFAULT_PASSWORD=your_password
    ```

## ▶️ Usage

Start the API server:
```bash
python main.py
```
Or using uvicorn directly:
```bash
uvicorn main:app --reload --port 5000
```

The API is now ready to accept requests. Use the [API Reference](docs/API_REFERENCE.md) to see how to authenticate and interact with the endpoints.

## 📄 License

[MIT License](LICENSE)
