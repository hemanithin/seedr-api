# Seedr API Reference

This document provides a comprehensive reference for the Seedr API wrapper. It details all available endpoints, their methods, parameters, and response structures.

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
    "access_token": "...",
    "refresh_token": "...",
    "device_code": null,
    "user_id": 12345,
    "client_id": "...",
    "grant_type": "password"
  }
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

---

### Login with Refresh Token
`POST /login/refresh-token`

Authenticates using an existing refresh token.

**Body Parameters**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `refresh_token` | string | Yes | Valid refresh token |
| `user_id` | string | No | Optional identifier (default: "default") |

---

### Refresh Access Token
`POST /refresh`

Refreshes the current access token.

**Query Parameters**
- `user_id`: string (default: "default")

---

### Logout
`POST /logout`

Logs out and removes the stored session.

**Query Parameters**
- `user_id`: string (default: "default")

---

## 👤 Account

Base path: `/api/v1/account`

### Get Settings
`GET /settings`

Retrieves account settings.

**Query Parameters**
- `user_id`: string (default: "default")

### Get Memory & Bandwidth
`GET /memory-bandwidth`

Retrieves storage and bandwidth usage information.

### Get Authorized Devices
`GET /devices`

Retrieves a list of devices authorized to access the account.

### Change Account Name
`PUT /name`

**Body Parameters**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `name` | string | Yes | New name |
| `password` | string | Yes | Current password |

### Change Password
`PUT /password`

**Body Parameters**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `old_password` | string | Yes | Current password |
| `new_password` | string | Yes | New password |

### Get Wishlist
`GET /list_wishlist`

Retrieves the user's wishlist items.

**Query Parameters**
- `user_id`: string (default: "default")

**Response (Success 200)**
```json
{
  "result": true,
  "code": 200,
  "wishlist": [
    {
      "id": 35382393,
      "user_id": 3526833,
      "title": "Torrent Title",
      "size": 10059377743,
      "torrent_hash": "2a43e0ea55e594c32db7b965e735bbe06997fb51",
      "torrent_magnet": "magnet:?xt=urn:btih:...",
      "torrent_meta": "0",
      "created": "2026-01-04 13:45:16",
      "added": 0,
      "is_private": 0
    }
  ]
}
```

---

## 📁 Files

Base path: `/api/v1/files`

### List Contents
`GET /list`

Lists contents of a specific folder (or root).

**Query Parameters**
| Name | Type | Description |
|------|------|-------------|
| `folder_id` | string | Folder ID to list (default: "0" for root) |
| `user_id` | string | User identifier |

### List All Contents
`GET /list-all`

Recursively lists all files and folders in the account.

### Create Folder
`POST /folder`

**Body Parameters**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `name` | string | Yes | Name of the new folder |

### Rename File
`PUT /file/{file_id}/rename`

**Body Parameters**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `new_name` | string | Yes | New filename |

### Rename Folder
`PUT /folder/{folder_id}/rename`

**Body Parameters**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `new_name` | string | Yes | New folder name |

### Delete File
`DELETE /file/{file_id}`

Deletes a specific file.

### Delete Folder
`DELETE /folder/{folder_id}`

Deletes a specific folder.

### Search Files
`GET /search`

Searches for files matching a query.

**Query Parameters**
- `query`: string (Required)

### Get Download URL (Fetch)
`GET /fetch/{file_id}`

Gets the direct download URL for a file.

### Create Folder Archive
`POST /archive/{folder_id}`

Generates download links for all files in a folder.

### Check Archive Status
`GET /archive/{archive_id}/status`

Checks the status of an archive creation process.

---

## ⚡ Torrents

Base path: `/api/v1/torrents`

### Add Torrent (Basic)
`POST /add`

Adds a torrent via magnet link without extra checks.

**Body Parameters**
| Name | Type | Description |
|------|------|-------------|
| `magnet_link` | string | Magnet URI |
| `folder_id` | string | Target folder ID (default: "-1") |

### Smart Add (With Space Check)
`POST /smartAdd`

Adds a torrent but checks for available storage space first.

**Body Parameters**
| Name | Type | Default | Description |
|------|------|---------|-------------|
| `magnet_link` | string | - | Magnet URI |
| `skip_space_check` | boolean | false | If true, skips the pre-check |

### Add & Download
`POST /addAndDownload`

Adds a torrent, waits for it to finish downloading on Seedr, and returns direct download links.

**Body Parameters**
| Name | Type | Default | Description |
|------|------|---------|-------------|
| `magnet_link` | string | - | Magnet URI |
| `wait_for_completion` | boolean | true | Wait for download to finish |
| `play_in_vlc` | boolean | false | Auto-play in VLC when ready |

### Add Torrent File
`POST /add/file`

Upload a `.torrent` file to add.

**Form Data**
- `file`: .torrent file (binary)
- `folder_id`: string

### List Active Torrents
`GET /list`

Lists all active torrents and their progress.

### Delete Torrent
`DELETE /{torrent_id}`

Removes a torrent from the active list.

### Delete Wishlist Item
`DELETE /wishlist/{wishlist_id}`

Removes an item from the wishlist.

### Get Torrent Metadata
`POST /metadata`

Fetches metadata for a torrent query/hash.

---

## 📺 VLC Player

Base path: `/api/v1/vlc`

### Play URL
`POST /play`

Plays a given URL in the local VLC player.

**Body Parameters**
| Name | Type | Default | Description |
|------|------|---------|-------------|
| `url` | string | - | Direct download/stream URL |
| `enqueue` | boolean | false | Add to playlist instead of replacing |

### Get VLC Config
`GET /config`

Returns current VLC path and configuration status.
