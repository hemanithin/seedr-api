# Seedr API Wrapper & Web Interface

A logical wrapper around the Seedr.cc API, providing enhanced features like smart torrent adding, automated downloads, and a local web interface for managing your Seedr account.

## 🚀 Features

- **Smart Torrent Adding**: Automatically checks for available storage space before adding torrents.
- **Auto-Download**: Add a torrent and automatically wait for it to finish, then get direct download links.
- **VLC Integration**: Direct playback of media files in your local VLC player.
- **Web Interface**: A clean, responsive web UI to manage files, torrents, and settings.
- **Swagger Documentation**: Interactive API documentation available at `/docs`.

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
    python app.py
    ```

2.  Open your browser and navigate to:
    - **Web Interface**: [http://localhost:5000/test](http://localhost:5000/test)
    - **API Docs**: [http://localhost:5000/docs](http://localhost:5000/docs)

## 📚 API Documentation

For detailed information about all available endpoints, parameters, and response formats, please refer to the [API Reference](docs/API_REFERENCE.md).

## 🧩 Project Structure

- `app.py`: Main Flask application entry point.
- `routes/`: Contains API route definitions (auth, account, files, torrents, vlc).
- `utils/`: Helper utilities for Seedr client management.
- `templates/`: HTML templates for the web interface.
- `static/`: Static assets (CSS, JS).

## 📄 License

[MIT License](LICENSE)
