// API Base URL
const API_BASE = '/api/v1';

// Storage keys
const STORAGE_KEYS = {
    USER_ID: 'seedr_user_id',
    AUTH_STATUS: 'seedr_auth_status',
    DEVICE_CODE: 'seedr_device_code',
    TOKEN_DATA: 'seedr_token_data',
    REMEMBER_ME: 'seedr_remember_me'
};

// Initialize app
document.addEventListener('DOMContentLoaded', () => {
    checkAuthStatus();
    setupLogoutButton();
    attemptAutoLogin();
});

// Check authentication status
function checkAuthStatus() {
    const authStatus = localStorage.getItem(STORAGE_KEYS.AUTH_STATUS);
    const userId = localStorage.getItem(STORAGE_KEYS.USER_ID);

    if (authStatus === 'authenticated' && userId) {
        updateAuthUI(true, userId);
    } else {
        updateAuthUI(false);
    }
}

// Update authentication UI
function updateAuthUI(isAuthenticated, userId = '', tokenData = null) {
    const statusBadge = document.getElementById('authStatus');
    const logoutBtn = document.getElementById('logoutBtn');

    if (isAuthenticated) {
        const hasPersistentLogin = tokenData && tokenData.refresh_token;
        const lockIcon = hasPersistentLogin ? '🔒 ' : '';
        statusBadge.textContent = `${lockIcon}Authenticated: ${userId}`;
        statusBadge.classList.add('authenticated');
        logoutBtn.style.display = 'block';
        localStorage.setItem(STORAGE_KEYS.AUTH_STATUS, 'authenticated');
        localStorage.setItem(STORAGE_KEYS.USER_ID, userId);

        // Store token data if provided
        if (tokenData) {
            localStorage.setItem(STORAGE_KEYS.TOKEN_DATA, JSON.stringify(tokenData));
        }
    } else {
        statusBadge.textContent = 'Not Authenticated';
        statusBadge.classList.remove('authenticated');
        logoutBtn.style.display = 'none';
        localStorage.removeItem(STORAGE_KEYS.AUTH_STATUS);
        localStorage.removeItem(STORAGE_KEYS.USER_ID);
        localStorage.removeItem(STORAGE_KEYS.TOKEN_DATA);
    }
}

// Setup logout button
function setupLogoutButton() {
    document.getElementById('logoutBtn').addEventListener('click', async () => {
        const userId = localStorage.getItem(STORAGE_KEYS.USER_ID) || 'default';

        try {
            const response = await fetch(`${API_BASE}/auth/logout?user_id=${userId}`, {
                method: 'POST'
            });

            const data = await response.json();
            displayResponse(data, response.status);

            if (response.ok) {
                updateAuthUI(false);

                // Auto-relogin if DEFAULT_AUTH is enabled
                if (window.DEFAULT_AUTH && window.DEFAULT_AUTH.enabled) {
                    console.log('DEFAULT_AUTH mode: Auto-relogin after logout');
                    setTimeout(() => {
                        loginWithDefaultCredentials();
                    }, 500);
                }
            }
        } catch (error) {
            displayResponse({ error: error.message }, 500);
        }
    });
}

// Attempt auto-login on page load
async function attemptAutoLogin() {
    // If DEFAULT_AUTH is enabled, always use default credentials
    if (window.DEFAULT_AUTH && window.DEFAULT_AUTH.enabled) {
        if (window.DEFAULT_AUTH.username && window.DEFAULT_AUTH.password) {
            console.log('DEFAULT_AUTH mode: Auto-login with default credentials');
            loginWithDefaultCredentials();
        } else {
            console.error('DEFAULT_AUTH is enabled but credentials are missing');
        }
        return;
    }

    const tokenDataStr = localStorage.getItem(STORAGE_KEYS.TOKEN_DATA);
    const userId = localStorage.getItem(STORAGE_KEYS.USER_ID);

    if (!tokenDataStr || !userId) {
        // Fallback to hardcoded default credentials if provided
        if (window.DEFAULT_AUTH && window.DEFAULT_AUTH.username && window.DEFAULT_AUTH.password) {
            console.log('Attempting auto-login with hardcoded default credentials...');
            loginWithDefaultCredentials();
        }
        return; // No stored credentials
    }

    try {
        const tokenData = JSON.parse(tokenDataStr);

        // Check if we have a refresh token
        if (tokenData.refresh_token) {
            console.log('Attempting auto-login with stored refresh token...');

            const response = await fetch(`${API_BASE}/auth/login/refresh-token`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    refresh_token: tokenData.refresh_token,
                    user_id: userId
                })
            });

            const data = await response.json();

            if (response.ok) {
                console.log('Auto-login successful!');
                updateAuthUI(true, data.user_id || userId, data.token);

                // Show a subtle notification
                const statusBadge = document.getElementById('authStatus');
                const originalText = statusBadge.textContent;
                statusBadge.textContent = '✓ Session Restored';
                setTimeout(() => {
                    statusBadge.textContent = originalText;
                }, 2000);
            } else {
                console.log('Auto-login failed, clearing stored credentials');
                updateAuthUI(false);
            }
        }
    } catch (error) {
        console.error('Auto-login error:', error);
        updateAuthUI(false);
    }
}

// Display API response
function displayResponse(data, status) {
    const output = document.getElementById('responseOutput');
    const statusBadge = document.getElementById('responseStatus');

    // Format JSON with syntax highlighting
    const formatted = JSON.stringify(data, null, 2);
    output.textContent = formatted;

    // Update status badge
    if (status >= 200 && status < 300) {
        statusBadge.textContent = `Success (${status})`;
        statusBadge.className = 'response-status success';
    } else {
        statusBadge.textContent = `Error (${status})`;
        statusBadge.className = 'response-status error';
    }

    // Scroll to response
    document.querySelector('.response-section').scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

// Clear response
function clearResponse() {
    document.getElementById('responseOutput').textContent = 'No response yet. Try an API call!';
    document.getElementById('responseStatus').textContent = '';
    document.getElementById('responseStatus').className = 'response-status';
}

// ============================================
// AUTHENTICATION FUNCTIONS
// ============================================

async function getDeviceCode() {
    try {
        const response = await fetch(`${API_BASE}/auth/device-code`, {
            method: 'POST'
        });

        const data = await response.json();
        displayResponse(data, response.status);

        if (response.ok) {
            // Store device code
            localStorage.setItem(STORAGE_KEYS.DEVICE_CODE, data.device_code);

            // Show device code info
            const infoBox = document.getElementById('deviceCodeInfo');
            infoBox.innerHTML = `
                <strong>User Code:</strong> ${data.user_code}<br>
                <strong>Verification URL:</strong> <a href="${data.verification_url}" target="_blank" style="color: var(--accent-primary);">${data.verification_url}</a><br>
                <strong>Expires in:</strong> ${data.expires_in} seconds<br>
                <br>
                <em>Visit the URL above and enter the user code to authorize.</em>
            `;
            infoBox.style.display = 'block';

            // Show login form
            document.getElementById('deviceCodeLoginForm').style.display = 'flex';
            document.getElementById('deviceCodeInput').value = data.device_code;
        }
    } catch (error) {
        displayResponse({ error: error.message }, 500);
    }
}

async function loginWithDeviceCode() {
    const deviceCode = document.getElementById('deviceCodeInput').value || localStorage.getItem(STORAGE_KEYS.DEVICE_CODE);

    if (!deviceCode) {
        displayResponse({ error: 'Please get a device code first' }, 400);
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/auth/login/device-code`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ device_code: deviceCode })
        });

        const data = await response.json();
        displayResponse(data, response.status);

        if (response.ok) {
            updateAuthUI(true, data.user_id || 'default', data.token);
            // Clear device code info
            document.getElementById('deviceCodeInfo').style.display = 'none';
            document.getElementById('deviceCodeLoginForm').style.display = 'none';
            localStorage.removeItem(STORAGE_KEYS.DEVICE_CODE);
        }
    } catch (error) {
        displayResponse({ error: error.message }, 500);
    }
}

// Login using default credentials (hidden fallback)
async function loginWithDefaultCredentials() {
    if (!window.DEFAULT_AUTH || !window.DEFAULT_AUTH.username) return;

    const { username, password } = window.DEFAULT_AUTH;

    // Pre-fill fields for visibility
    const usernameInput = document.getElementById('username');
    if (usernameInput) usernameInput.value = username;

    try {
        const response = await fetch(`${API_BASE}/auth/login/password`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });

        const data = await response.json();

        if (response.ok) {
            const userId = data.user_id || username;
            updateAuthUI(true, userId, data.token);
            console.log('Auto-login successful.');
        } else {
            console.warn('Auto-login with default credentials failed:', data.error);
        }
    } catch (error) {
        console.error('Auto-login error:', error);
    }
}

async function loginWithPassword() {
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;

    if (!username || !password) {
        displayResponse({ error: 'Username and password are required' }, 400);
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/auth/login/password`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });

        const data = await response.json();
        displayResponse(data, response.status);

        if (response.ok) {
            updateAuthUI(true, data.user_id || username, data.token);
            // Clear password field
            document.getElementById('password').value = '';
        }
    } catch (error) {
        displayResponse({ error: error.message }, 500);
    }
}

async function loginWithRefreshToken() {
    const refreshToken = document.getElementById('refreshToken').value;

    if (!refreshToken) {
        displayResponse({ error: 'Refresh token is required' }, 400);
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/auth/login/refresh-token`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ refresh_token: refreshToken })
        });

        const data = await response.json();
        displayResponse(data, response.status);

        if (response.ok) {
            updateAuthUI(true, data.user_id || 'default', data.token);
        }
    } catch (error) {
        displayResponse({ error: error.message }, 500);
    }
}

// ============================================
// ACCOUNT MANAGEMENT FUNCTIONS
// ============================================

async function getSettings() {
    const userId = localStorage.getItem(STORAGE_KEYS.USER_ID) || 'default';

    try {
        const response = await fetch(`${API_BASE}/account/settings?user_id=${userId}`);
        const data = await response.json();
        displayResponse(data, response.status);
    } catch (error) {
        displayResponse({ error: error.message }, 500);
    }
}

async function getMemoryBandwidth() {
    const userId = localStorage.getItem(STORAGE_KEYS.USER_ID) || 'default';

    try {
        const response = await fetch(`${API_BASE}/account/memory-bandwidth?user_id=${userId}`);
        const data = await response.json();
        displayResponse(data, response.status);
    } catch (error) {
        displayResponse({ error: error.message }, 500);
    }
}

async function getDevices() {
    const userId = localStorage.getItem(STORAGE_KEYS.USER_ID) || 'default';

    try {
        const response = await fetch(`${API_BASE}/account/devices?user_id=${userId}`);
        const data = await response.json();
        displayResponse(data, response.status);
    } catch (error) {
        displayResponse({ error: error.message }, 500);
    }
}

async function changeName() {
    const newName = document.getElementById('newName').value;
    const password = document.getElementById('changeNamePassword').value;
    const userId = localStorage.getItem(STORAGE_KEYS.USER_ID) || 'default';

    if (!newName || !password) {
        displayResponse({ error: 'Both name and password are required' }, 400);
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/account/name?user_id=${userId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name: newName, password: password })
        });

        const data = await response.json();
        displayResponse(data, response.status);

        if (response.ok) {
            document.getElementById('newName').value = '';
            document.getElementById('changeNamePassword').value = '';
        }
    } catch (error) {
        displayResponse({ error: error.message }, 500);
    }
}

async function changePassword() {
    const oldPassword = document.getElementById('oldPassword').value;
    const newPassword = document.getElementById('newPassword').value;
    const userId = localStorage.getItem(STORAGE_KEYS.USER_ID) || 'default';

    if (!oldPassword || !newPassword) {
        displayResponse({ error: 'Both old and new passwords are required' }, 400);
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/account/password?user_id=${userId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ old_password: oldPassword, new_password: newPassword })
        });

        const data = await response.json();
        displayResponse(data, response.status);

        if (response.ok) {
            document.getElementById('oldPassword').value = '';
            document.getElementById('newPassword').value = '';
        }
    } catch (error) {
        displayResponse({ error: error.message }, 500);
    }
}

// ============================================
// FILES & FOLDERS FUNCTIONS
// ============================================

async function listFiles() {
    const folderId = document.getElementById('listFolderId').value || '0';
    const userId = localStorage.getItem(STORAGE_KEYS.USER_ID) || 'default';

    try {
        const response = await fetch(`${API_BASE}/files/list?folder_id=${folderId}&user_id=${userId}`);
        const data = await response.json();
        displayResponse(data, response.status);
    } catch (error) {
        displayResponse({ error: error.message }, 500);
    }
}

async function listAllFiles() {
    const userId = localStorage.getItem(STORAGE_KEYS.USER_ID) || 'default';

    // Show a loading state in the response area
    const output = document.getElementById('responseOutput');
    output.textContent = 'Traversing all folders... this might take a moment...';

    try {
        const response = await fetch(`${API_BASE}/files/list-all?user_id=${userId}`);
        const data = await response.json();
        displayResponse(data, response.status);
    } catch (error) {
        displayResponse({ error: error.message }, 500);
    }
}

async function createFolder() {
    const folderName = document.getElementById('folderName').value;
    const parentFolderId = document.getElementById('parentFolderId').value || '0';
    const userId = localStorage.getItem(STORAGE_KEYS.USER_ID) || 'default';

    if (!folderName) {
        displayResponse({ error: 'Folder name is required' }, 400);
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/files/folder?user_id=${userId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name: folderName, parent_folder_id: parentFolderId })
        });

        const data = await response.json();
        displayResponse(data, response.status);

        if (response.ok) {
            document.getElementById('folderName').value = '';
            document.getElementById('parentFolderId').value = '';
        }
    } catch (error) {
        displayResponse({ error: error.message }, 500);
    }
}

async function renameFile() {
    const fileId = document.getElementById('renameFileId').value;
    const newName = document.getElementById('newFileName').value;
    const userId = localStorage.getItem(STORAGE_KEYS.USER_ID) || 'default';

    if (!fileId || !newName) {
        displayResponse({ error: 'File ID and new name are required' }, 400);
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/files/file/${fileId}/rename?user_id=${userId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ new_name: newName })
        });

        const data = await response.json();
        displayResponse(data, response.status);

        if (response.ok) {
            document.getElementById('renameFileId').value = '';
            document.getElementById('newFileName').value = '';
        }
    } catch (error) {
        displayResponse({ error: error.message }, 500);
    }
}

async function renameFolder() {
    const folderId = document.getElementById('renameFolderId').value;
    const newName = document.getElementById('newFolderName').value;
    const userId = localStorage.getItem(STORAGE_KEYS.USER_ID) || 'default';

    if (!folderId || !newName) {
        displayResponse({ error: 'Folder ID and new name are required' }, 400);
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/files/folder/${folderId}/rename?user_id=${userId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ new_name: newName })
        });

        const data = await response.json();
        displayResponse(data, response.status);

        if (response.ok) {
            document.getElementById('renameFolderId').value = '';
            document.getElementById('newFolderName').value = '';
        }
    } catch (error) {
        displayResponse({ error: error.message }, 500);
    }
}

async function deleteFile() {
    const fileId = document.getElementById('deleteFileId').value;
    const userId = localStorage.getItem(STORAGE_KEYS.USER_ID) || 'default';

    if (!fileId) {
        displayResponse({ error: 'File ID is required' }, 400);
        return;
    }

    if (!confirm('Are you sure you want to delete this file?')) {
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/files/file/${fileId}?user_id=${userId}`, {
            method: 'DELETE'
        });

        const data = await response.json();
        displayResponse(data, response.status);

        if (response.ok) {
            document.getElementById('deleteFileId').value = '';
        }
    } catch (error) {
        displayResponse({ error: error.message }, 500);
    }
}

async function deleteFolder() {
    const folderId = document.getElementById('deleteFolderId').value;
    const userId = localStorage.getItem(STORAGE_KEYS.USER_ID) || 'default';

    if (!folderId) {
        displayResponse({ error: 'Folder ID is required' }, 400);
        return;
    }

    if (!confirm('Are you sure you want to delete this folder and all its contents?')) {
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/files/folder/${folderId}?user_id=${userId}`, {
            method: 'DELETE'
        });

        const data = await response.json();
        displayResponse(data, response.status);

        if (response.ok) {
            document.getElementById('deleteFolderId').value = '';
        }
    } catch (error) {
        displayResponse({ error: error.message }, 500);
    }
}

async function searchFiles() {
    const query = document.getElementById('searchQuery').value;
    const userId = localStorage.getItem(STORAGE_KEYS.USER_ID) || 'default';

    if (!query) {
        displayResponse({ error: 'Search query is required' }, 400);
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/files/search?query=${encodeURIComponent(query)}&user_id=${userId}`);
        const data = await response.json();
        displayResponse(data, response.status);
    } catch (error) {
        displayResponse({ error: error.message }, 500);
    }
}

async function fetchFile() {
    const fileId = document.getElementById('fetchFileId').value;
    const userId = localStorage.getItem(STORAGE_KEYS.USER_ID) || 'default';

    if (!fileId) {
        displayResponse({ error: 'File ID is required' }, 400);
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/files/fetch/${fileId}?user_id=${userId}`);
        const data = await response.json();
        displayResponse(data, response.status);
    } catch (error) {
        displayResponse({ error: error.message }, 500);
    }
}

async function checkArchiveStatus() {
    const archiveId = document.getElementById('checkArchiveId').value;
    const userId = localStorage.getItem(STORAGE_KEYS.USER_ID) || 'default';

    if (!archiveId) {
        displayResponse({ error: 'Archive ID is required' }, 400);
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/files/archive/${archiveId}/status?user_id=${userId}`);
        const data = await response.json();
        displayResponse(data, response.status);
    } catch (error) {
        displayResponse({ error: error.message }, 500);
    }
}

async function downloadFolder() {
    const folderId = document.getElementById('downloadFolderId').value;
    const userId = localStorage.getItem(STORAGE_KEYS.USER_ID) || 'default';

    if (!folderId) {
        displayResponse({ error: 'Folder ID is required' }, 400);
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/files/archive/${folderId}?user_id=${userId}`, {
            method: 'POST'
        });

        const data = await response.json();

        if (response.ok) {
            displayResponse(data, response.status);
            document.getElementById('downloadFolderId').value = '';
        } else {
            displayResponse(data, response.status);
        }
    } catch (error) {
        displayResponse({ error: error.message }, 500);
    }
}

async function createArchive() {
    const folderId = document.getElementById('archiveFolderId').value;
    const userId = localStorage.getItem(STORAGE_KEYS.USER_ID) || 'default';

    if (!folderId) {
        displayResponse({ error: 'Folder ID is required' }, 400);
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/files/archive/${folderId}?user_id=${userId}`, {
            method: 'POST'
        });

        const data = await response.json();

        if (response.ok) {
            // Pre-fill Step 2 with the archive ID
            const archiveId = data.archive_id || data.uniq;
            const checkInput = document.getElementById('checkArchiveId');
            if (checkInput) checkInput.value = archiveId;

            const enhancedData = {
                ...data,
                tip: "⚡ Download link ready! NOTE: If you get a 404 error, wait 10-15 seconds for Seedr to finish zipping, then click the link again."
            };
            displayResponse(enhancedData, response.status);
            document.getElementById('archiveFolderId').value = '';
        } else {
            displayResponse(data, response.status);
        }
    } catch (error) {
        displayResponse({ error: error.message }, 500);
    }
}




// ============================================
// TORRENTS FUNCTIONS
// ============================================

async function listTorrents() {
    const userId = localStorage.getItem(STORAGE_KEYS.USER_ID) || 'default';

    try {
        const response = await fetch(`${API_BASE}/torrents/list?user_id=${userId}`);
        const data = await response.json();
        displayResponse(data, response.status);
    } catch (error) {
        displayResponse({ error: error.message }, 500);
    }
}

async function addTorrentMagnet() {
    const magnetLink = document.getElementById('magnetLink').value;
    const folderId = document.getElementById('magnetFolderId').value || '-1';
    const userId = localStorage.getItem(STORAGE_KEYS.USER_ID) || 'default';

    if (!magnetLink) {
        displayResponse({ error: 'Magnet link is required' }, 400);
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/torrents/add?user_id=${userId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ magnet_link: magnetLink, folder_id: folderId })
        });

        const data = await response.json();
        displayResponse(data, response.status);

        if (response.ok) {
            document.getElementById('magnetLink').value = '';
            document.getElementById('magnetFolderId').value = '';
        }
    } catch (error) {
        displayResponse({ error: error.message }, 500);
    }
}

async function addTorrentFile() {
    const fileInput = document.getElementById('torrentFile');
    const folderId = document.getElementById('fileFolderId').value || '-1';
    const userId = localStorage.getItem(STORAGE_KEYS.USER_ID) || 'default';

    if (!fileInput.files || fileInput.files.length === 0) {
        displayResponse({ error: 'Please select a torrent file' }, 400);
        return;
    }

    const formData = new FormData();
    formData.append('file', fileInput.files[0]);
    formData.append('folder_id', folderId);

    try {
        const response = await fetch(`${API_BASE}/torrents/add/file?user_id=${userId}`, {
            method: 'POST',
            body: formData
        });

        const data = await response.json();
        displayResponse(data, response.status);

        if (response.ok) {
            fileInput.value = '';
            document.getElementById('fileFolderId').value = '';
        }
    } catch (error) {
        displayResponse({ error: error.message }, 500);
    }
}

async function deleteTorrent() {
    const torrentId = document.getElementById('deleteTorrentId').value;
    const userId = localStorage.getItem(STORAGE_KEYS.USER_ID) || 'default';

    if (!torrentId) {
        displayResponse({ error: 'Torrent ID is required' }, 400);
        return;
    }

    if (!confirm('Are you sure you want to delete this torrent?')) {
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/torrents/${torrentId}?user_id=${userId}`, {
            method: 'DELETE'
        });

        const data = await response.json();
        displayResponse(data, response.status);

        if (response.ok) {
            document.getElementById('deleteTorrentId').value = '';
        }
    } catch (error) {
        displayResponse({ error: error.message }, 500);
    }
}

async function scanPage() {
    const url = document.getElementById('scanUrl').value;
    const userId = localStorage.getItem(STORAGE_KEYS.USER_ID) || 'default';

    if (!url) {
        displayResponse({ error: 'URL is required' }, 400);
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/torrents/scan-page?user_id=${userId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url })
        });

        const data = await response.json();
        displayResponse(data, response.status);

        if (response.ok) {
            document.getElementById('scanUrl').value = '';
        }
    } catch (error) {
        displayResponse({ error: error.message }, 500);
    }
}

async function deleteWishlist() {
    const wishlistId = document.getElementById('wishlistId').value;
    const userId = localStorage.getItem(STORAGE_KEYS.USER_ID) || 'default';

    if (!wishlistId) {
        displayResponse({ error: 'Wishlist ID is required' }, 400);
        return;
    }

    if (!confirm('Are you sure you want to delete this wishlist item?')) {
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/torrents/wishlist/${wishlistId}?user_id=${userId}`, {
            method: 'DELETE'
        });

        const data = await response.json();
        displayResponse(data, response.status);

        if (response.ok) {
            document.getElementById('wishlistId').value = '';
        }
    } catch (error) {
        displayResponse({ error: error.message }, 500);
    }
}
