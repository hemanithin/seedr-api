from flask_restx import fields


def create_models(api):
    """Create all Swagger models for the API"""
    
    # Authentication Models
    device_code_response = api.model('DeviceCodeResponse', {
        'device_code': fields.String(description='Device code for authentication'),
        'user_code': fields.String(description='User code to display'),
        'verification_uri': fields.String(description='URL for user to visit'),
        'expires_in': fields.Integer(description='Expiration time in seconds'),
        'interval': fields.Integer(description='Polling interval in seconds')
    })
    
    password_login_request = api.model('PasswordLoginRequest', {
        'username': fields.String(required=True, description='Seedr username/email'),
        'password': fields.String(required=True, description='Seedr password')
    })
    
    device_code_login_request = api.model('DeviceCodeLoginRequest', {
        'device_code': fields.String(required=True, description='Device code from get_device_code')
    })
    
    refresh_token_request = api.model('RefreshTokenRequest', {
        'refresh_token': fields.String(required=True, description='Refresh token')
    })
    
    token_response = api.model('TokenResponse', {
        'access_token': fields.String(description='Access token'),
        'refresh_token': fields.String(description='Refresh token'),
        'token_type': fields.String(description='Token type (usually Bearer)'),
        'expires_in': fields.Integer(description='Token expiration in seconds')
    })
    
    # Account Models
    settings_response = api.model('SettingsResponse', {
        'account': fields.Raw(description='Account information'),
        'user': fields.Raw(description='User information')
    })
    
    memory_bandwidth_response = api.model('MemoryBandwidthResponse', {
        'space_used': fields.String(description='Space used'),
        'space_max': fields.String(description='Maximum space'),
        'bandwidth_used': fields.String(description='Bandwidth used'),
        'bandwidth_max': fields.String(description='Maximum bandwidth')
    })
    
    change_name_request = api.model('ChangeNameRequest', {
        'name': fields.String(required=True, description='New account name'),
        'password': fields.String(required=True, description='Current password for verification')
    })
    
    change_password_request = api.model('ChangePasswordRequest', {
        'old_password': fields.String(required=True, description='Current password'),
        'new_password': fields.String(required=True, description='New password')
    })
    
    # File/Folder Models
    file_model = api.model('File', {
        'id': fields.String(description='File ID'),
        'name': fields.String(description='File name'),
        'size': fields.Integer(description='File size in bytes'),
        'folder_file_id': fields.String(description='Parent folder ID')
    })
    
    folder_model = api.model('Folder', {
        'id': fields.String(description='Folder ID'),
        'name': fields.String(description='Folder name'),
        'size': fields.Integer(description='Total size in bytes')
    })
    
    folder_contents_response = api.model('FolderContentsResponse', {
        'folders': fields.List(fields.Nested(folder_model), description='List of folders'),
        'files': fields.List(fields.Nested(file_model), description='List of files')
    })
    
    create_folder_request = api.model('CreateFolderRequest', {
        'name': fields.String(required=True, description='Folder name')
    })
    
    rename_request = api.model('RenameRequest', {
        'new_name': fields.String(required=True, description='New name')
    })
    
    fetch_file_response = api.model('FetchFileResponse', {
        'url': fields.String(description='Download URL'),
        'name': fields.String(description='File name'),
        'size': fields.Integer(description='File size')
    })
    
    archive_response = api.model('ArchiveResponse', {
        'archive_id': fields.String(description='Archive ID'),
        'url': fields.String(description='Archive download URL')
    })
    
    # Torrent Models
    add_torrent_request = api.model('AddTorrentRequest', {
        'magnet_link': fields.String(description='Magnet link (if not uploading file)'),
        'wishlist_id': fields.String(description='Wishlist ID (optional)'),
        'folder_id': fields.String(description='Destination folder ID (default: -1)')
    })
    
    scan_page_request = api.model('ScanPageRequest', {
        'url': fields.String(required=True, description='URL to scan for torrents')
    })
    
    torrent_response = api.model('TorrentResponse', {
        'result': fields.Boolean(description='Operation success'),
        'user_torrent_id': fields.String(description='Torrent ID'),
        'message': fields.String(description='Response message')
    })
    
    # Generic Models
    success_response = api.model('SuccessResponse', {
        'success': fields.Boolean(description='Operation success'),
        'message': fields.String(description='Response message')
    })
    
    error_response = api.model('ErrorResponse', {
        'error': fields.String(description='Error message'),
        'code': fields.Integer(description='Error code')
    })
    
    return {
        'device_code_response': device_code_response,
        'password_login_request': password_login_request,
        'device_code_login_request': device_code_login_request,
        'refresh_token_request': refresh_token_request,
        'token_response': token_response,
        'settings_response': settings_response,
        'memory_bandwidth_response': memory_bandwidth_response,
        'change_name_request': change_name_request,
        'change_password_request': change_password_request,
        'folder_contents_response': folder_contents_response,
        'create_folder_request': create_folder_request,
        'rename_request': rename_request,
        'fetch_file_response': fetch_file_response,
        'archive_response': archive_response,
        'add_torrent_request': add_torrent_request,
        'scan_page_request': scan_page_request,
        'torrent_response': torrent_response,
        'success_response': success_response,
        'error_response': error_response
    }
