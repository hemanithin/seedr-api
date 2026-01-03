# Seedr API Reference

This document provides a comprehensive reference for the Seedr API wrapper. It details all available endpoints, their method, parameters, and response structures, including positive and negative scenarios.

## 🔗 Authentication

Base path: `/api/v1/auth`

### Get Device Code
`POST /device-code`

Initiates the device code authentication flow.

**Response (Success 200)**
```json
{
  "device_code": "string",
  "user_code": "string",
  "verification_url": "string",
  "expires_in": 300,
  "interval": 5
}
```

---

### Login with Password
`POST /login/password`

Authenticates using Seedr username and password.

**Body Parameters**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `username` | string | Yes | Seedr username or email |
| `password` | string | Yes | Seedr password |

**Response (Success 200)**
```json
{
  "message": "Login successful",
  "user_id": "user@example.com",
  "token": {
    "access_token": "62a1135cbd5c7de308db950ef7c55525628c2075",
    "refresh_token": "7ff9714e61c8dee059c35e22fd13e02d0fd29aea",
    "device_code": null,
    "user_id": 3526833,
    "client_id": "seedr_chrome_extension",
    "grant_type": "password"
  }
}
```

**Response (Authentication Failed 401)**
```json
{
  "error": "Authentication failed: Invalid credentials"
}
```

---

### Login with Device Code
`POST /login/device-code`

Completes the device code authentication flow.

**Body Parameters**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `device_code` | string | Yes | Code obtained from `/device-code` |
| `user_id` | string | No | Optional identifier (default: "default") |

**Response (Success 200)**
```json
{
  "message": "Login successful",
  "user_id": "default",
  "token": {
     "access_token": "...",
     "refresh_token": "...",
     "device_code": "...",
     ...
  }
}
```

## 👤 Account

Base path: `/api/v1/account`

### Get Settings
`GET /settings`

Retrieves account settings.

**Query Parameters**
- `user_id`: string (default: "default")

**Response (Success 200)**
```json
{
  "result": true,
  "code": 200,
  "settings": {
    "allow_remote_access": true,
    "site_language": "en",
    "subtitles_language": "eng",
    "email_announcements": true,
    "email_newsletter": true
  },
  "account": {
    "username": "user@email.com",
    "user_id": 1234567,
    "premium": 0,
    "package_id": -1,
    "package_name": "NON-PREMIUM",
    "space_used": 1732991947,
    "space_max": 4831838208,
    "bandwidth_used": 44523158818,
    "email": "user@email.com"
  },
  "country": "India"
}
```

---

### Get Memory & Bandwidth
`GET /memory-bandwidth`

Retrieves storage and bandwidth usage information.

**Query Parameters**
- `user_id`: string (default: "default")

**Response (Success 200)**
```json
{
  "bandwidth_used": 44523158818,
  "bandwidth_max": 536870912000,
  "space_used": 1732991947,
  "space_max": 4831838208,
  "is_premium": 0
}
```

## 📁 Files

Base path: `/api/v1/files`

### List Contents
`GET /list`

Lists contents of a specific folder (or root).

**Query Parameters**
| Name | Type | Description |
|------|------|-------------|
| `user_id` | string | User identifier (default: "default") |
| `folder_id` | string | Folder ID to list (default: "0" for root) |

**Response (Success 200)**
```json
{
  "folders": [
    {
      "id": 12345,
      "name": "My Folder",
      "size": 0,
      "last_update": "2024-01-01 12:00:00"
    }
  ],
  "files": [
    {
      "folder_file_id": 67890,
      "name": "video.mp4",
      "size": 1048576,
      "date": "2024-01-01 12:00:00",
      "play_video": true
    }
  ]
}
```

---

### Create Folder
`POST /folder`

Creates a new folder.

**Body Parameters**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `name` | string | Yes | Name of the new folder |

**Response (Success 200)**
```json
{
  "success": true,
  "message": "Folder created successfully",
  "result": {
      "id": 123456,
      "name": "New Folder",
      "result": true,
      "code": 200
  }
}
```

---

### Get Download URL (Fetch)
`GET /fetch/<file_id>`

Gets the direct download URL for a file.

**Path Parameters**
- `file_id`: ID of the file to download

**Response (Success 200)**
```json
{
  "url": "https://example.com/down/load/token/filename.mp4",
  "name": "filename.mp4",
  "size": 1024
}
```

## ⚡ Torrents

Base path: `/api/v1/torrents`

### Smart Add (With Space Check)
`POST /smartAdd`

Adds a torrent but checks for available storage space first.

**Body Parameters**
| Name | Type | Default | Description |
|------|------|---------|-------------|
| `magnet_link` | string | - | Magnet URI |
| `skip_space_check` | boolean | false | If true, skips the pre-check |

**Response (Insufficient Storage 507)**
```json
{
  "success": false,
  "error": "Insufficient storage space",
  "message": "Cannot add torrent - not enough space available",
  "space_check": {
    "torrent_size": 10737418240,
    "torrent_size_formatted": "10.00 GB",
    "available_space": 5368709120,
    "available_space_formatted": "5.00 GB",
    "space_needed": 5368709120,
    "space_needed_formatted": "5.00 GB",
    "sufficient": false
  }
}
```

---

### Add & Download
`POST /addAndDownload`

Adds a torrent, waits for it to finish downloading on Seedr, and returns direct download links.

**Response (Completed 200)**
```json
{
  "success": true,
  "status": "completed",
  "message": "Torrent completed! 1 file(s) ready for download",
  "folder_id": 12345,
  "wait_time_seconds": 45,
  "files": [
    {
      "file_id": 98765,
      "name": "movie.mp4",
      "size": 5000000,
      "size_formatted": "4.76 MB",
      "download_url": "https://..."
    }
  ]
}
```
