import logging
from flask import request
from flask_restx import Namespace, Resource, fields
from werkzeug.datastructures import FileStorage
from seedrcc.exceptions import SeedrError
from utils import client_manager
from utils.serialization import to_dict
import requests
import subprocess
import os
from config import Config


# Create namespace
# Create namespace
torrents_ns = Namespace('torrents', description='Torrent management operations')
logger = logging.getLogger(__name__)

# File upload parser
upload_parser = torrents_ns.parser()
upload_parser.add_argument('file', location='files', type=FileStorage, required=False, help='Torrent file')
upload_parser.add_argument('folder_id', location='form', type=str, default='-1', help='Destination folder ID')
upload_parser.add_argument('wishlist_id', location='form', type=str, required=False, help='Wishlist ID')


@torrents_ns.route('/add')
class AddTorrent(Resource):
    @torrents_ns.doc('add_torrent_magnet')
    @torrents_ns.param('user_id', 'User identifier (default: "default")', _in='query')
    @torrents_ns.expect(torrents_ns.model('AddTorrentRequest', {
        'magnet_link': fields.String(description='Magnet link'),
        'wishlist_id': fields.String(description='Wishlist ID (optional)'),
        'folder_id': fields.String(description='Destination folder ID (default: -1)', default='-1')
    }))
    @torrents_ns.response(200, 'Success')
    @torrents_ns.response(400, 'Validation Error')
    @torrents_ns.response(401, 'Not authenticated')
    @torrents_ns.response(500, 'Server Error')
    def post(self):
        """Add torrent via magnet link"""
        logger.info("Processing add torrent request")
        try:
            user_id = request.args.get('user_id', 'default')
            client = client_manager.get_client(user_id)
            
            if not client:
                return {'error': 'Not authenticated. Please login first.'}, 401
            
            data = request.get_json()
            magnet_link = data.get('magnet_link')
            wishlist_id = data.get('wishlist_id')
            folder_id = data.get('folder_id', '-1')
            
            if not magnet_link:
                return {'error': 'Magnet link is required'}, 400
            
            result = client.add_torrent(
                magnet_link=magnet_link,
                wishlist_id=wishlist_id,
                folder_id=folder_id
            )
            
            logger.info("Torrent added successfully via magnet link")
            return {
                'success': True,
                'message': 'Torrent added successfully',
                'result': to_dict(result)
            }, 200
            
        except SeedrError as e:
            logger.error(f"SeedrError in add torrent: {e}")
            return {'error': str(e)}, 500
        except Exception as e:
            logger.exception("Unexpected error in add torrent")
            return {'error': f'Unexpected error: {str(e)}'}, 500


# Helper functions for smart add
def _get_torrent_size(magnet_link):
    """Get torrent size from TorrentMeta API"""
    logger.debug(f"Fetching torrent size for magnet: {magnet_link[:50]}...")
    try:
        torrentmeta_url = 'https://torrentmeta.fly.dev'
        headers = {'Content-Type': 'application/json'}
        payload = {'query': magnet_link}
        
        response = requests.post(
            torrentmeta_url,
            json=payload,
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            metadata = result.get('data', {})
            
            # Extract total size from files array
            if 'files' in metadata and isinstance(metadata['files'], list):
                total_size = sum(file.get('size', 0) for file in metadata['files'])
                return total_size
        
        return 0  # Return 0 if size cannot be determined
        
    except Exception as e:
        logger.error(f"Error fetching torrent size: {str(e)}")
        return 0


def _get_available_space(client):
    """Get available space in bytes from Seedr account"""
    try:
        memory_bandwidth = client.get_memory_bandwidth()
        space_used = getattr(memory_bandwidth, 'space_used', 0)
        space_max = getattr(memory_bandwidth, 'space_max', 0)
        available_space = space_max - space_used
        return available_space, space_used, space_max
    except Exception as e:
        print(f"Error fetching available space: {str(e)}")
        return 0, 0, 0


def _format_size(size_bytes):
    """Format bytes to human-readable size"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"


@torrents_ns.route('/smartAdd')
class SmartAddTorrent(Resource):
    @torrents_ns.doc('smart_add_torrent')
    @torrents_ns.param('user_id', 'User identifier (default: "default")', _in='query')
    @torrents_ns.expect(torrents_ns.model('SmartAddTorrentRequest', {
        'magnet_link': fields.String(required=True, description='Magnet link'),
        'folder_id': fields.String(description='Destination folder ID (default: -1)', default='-1'),
        'skip_space_check': fields.Boolean(description='Skip space validation (default: false)', default=False)
    }))
    @torrents_ns.response(200, 'Success - Torrent added')
    @torrents_ns.response(400, 'Validation Error')
    @torrents_ns.response(401, 'Not authenticated')
    @torrents_ns.response(507, 'Insufficient Storage - Torrent rejected')
    @torrents_ns.response(500, 'Server Error')
    def post(self):
        """Smart add torrent with space validation - rejects if insufficient space"""
        logger.info("Processing smart add torrent request")
        try:
            user_id = request.args.get('user_id', 'default')
            client = client_manager.get_client(user_id)
            
            if not client:
                return {'error': 'Not authenticated. Please login first.'}, 401
            
            data = request.get_json()
            magnet_link = data.get('magnet_link')
            folder_id = data.get('folder_id', '-1')
            skip_space_check = data.get('skip_space_check', False)
            
            if not magnet_link:
                return {'error': 'Magnet link is required'}, 400
            
            # Perform space check unless explicitly skipped
            if not skip_space_check:
                # Get torrent size
                torrent_size = _get_torrent_size(magnet_link)
                
                # Get available space
                available_space, space_used, space_max = _get_available_space(client)
                
                # Check if there's enough space
                if torrent_size > 0 and available_space > 0:
                    if torrent_size > available_space:
                        # Insufficient space - reject the torrent
                        space_needed = torrent_size - available_space
                        
                        return {
                            'success': False,
                            'error': 'Insufficient storage space',
                            'message': 'Cannot add torrent - not enough space available',
                            'space_check': {
                                'torrent_size': torrent_size,
                                'torrent_size_formatted': _format_size(torrent_size),
                                'available_space': available_space,
                                'available_space_formatted': _format_size(available_space),
                                'space_used': space_used,
                                'space_used_formatted': _format_size(space_used),
                                'space_max': space_max,
                                'space_max_formatted': _format_size(space_max),
                                'space_needed': space_needed,
                                'space_needed_formatted': _format_size(space_needed),
                                'sufficient': False
                            }
                        }, 507  # HTTP 507 Insufficient Storage
            
            # Sufficient space or space check skipped - add torrent
            result = client.add_torrent(
                magnet_link=magnet_link,
                folder_id=folder_id
            )
            
            response_data = {
                'success': True,
                'message': 'Torrent added successfully',
                'result': to_dict(result)
            }
            
            # Include space check info if check was performed
            if not skip_space_check:
                torrent_size = _get_torrent_size(magnet_link) if 'torrent_size' not in locals() else torrent_size
                available_space, space_used, space_max = _get_available_space(client) if 'available_space' not in locals() else (available_space, space_used, space_max)
                
                response_data['space_check'] = {
                    'torrent_size': torrent_size,
                    'torrent_size_formatted': _format_size(torrent_size) if torrent_size > 0 else 'Unknown',
                    'available_space': available_space,
                    'available_space_formatted': _format_size(available_space),
                    'space_used': space_used,
                    'space_used_formatted': _format_size(space_used),
                    'space_max': space_max,
                    'space_max_formatted': _format_size(space_max),
                    'sufficient': True
                }
            
            return response_data, 200
            
        except SeedrError as e:
            return {'error': str(e)}, 500
        except Exception as e:
            return {'error': f'Unexpected error: {str(e)}'}, 500


@torrents_ns.route('/addAndDownload')
class AddAndDownloadTorrent(Resource):
    @torrents_ns.doc('add_and_download_torrent')
    @torrents_ns.param('user_id', 'User identifier (default: "default")', _in='query')
    @torrents_ns.expect(torrents_ns.model('AddAndDownloadRequest', {
        'magnet_link': fields.String(required=True, description='Magnet link'),
        'folder_id': fields.String(description='Destination folder ID (default: -1)', default='-1'),
        'skip_space_check': fields.Boolean(description='Skip space validation (default: false)', default=False),
        'wait_for_completion': fields.Boolean(description='Wait for download to complete (default: true)', default=True),
        'max_wait_seconds': fields.Integer(description='Maximum seconds to wait (default: 300, max: 600)', default=300),
        'poll_interval': fields.Integer(description='Seconds between status checks (default: 5)', default=5),
        'play_in_vlc': fields.Boolean(description='Play in VLC after download (default: false). Single file plays directly, multiple files are enqueued.', default=False)
    }))
    @torrents_ns.response(200, 'Success - Torrent added and download URLs retrieved')
    @torrents_ns.response(202, 'Accepted - Torrent added but still downloading')
    @torrents_ns.response(400, 'Validation Error')
    @torrents_ns.response(401, 'Not authenticated')
    @torrents_ns.response(507, 'Insufficient Storage')
    @torrents_ns.response(500, 'Server Error')
    def post(self):
        """Add torrent with space validation and get download URLs (with optional polling)"""
        logger.info("Processing add and download torrent request")
        try:
            import time
            
            user_id = request.args.get('user_id', 'default')
            client = client_manager.get_client(user_id)
            
            if not client:
                return {'error': 'Not authenticated. Please login first.'}, 401
            
            data = request.get_json()
            magnet_link = data.get('magnet_link')
            folder_id = data.get('folder_id', '-1')
            skip_space_check = data.get('skip_space_check', False)
            wait_for_completion = data.get('wait_for_completion', True)
            max_wait_seconds = min(data.get('max_wait_seconds', 300), 600)  # Cap at 10 minutes
            poll_interval = max(data.get('poll_interval', 5), 2)  # Minimum 2 seconds
            play_in_vlc = data.get('play_in_vlc', False)
            
            if not magnet_link:
                return {'error': 'Magnet link is required'}, 400
            
            # Perform space check unless explicitly skipped
            if not skip_space_check:
                torrent_size = _get_torrent_size(magnet_link)
                available_space, space_used, space_max = _get_available_space(client)
                
                if torrent_size > 0 and available_space > 0:
                    if torrent_size > available_space:
                        space_needed = torrent_size - available_space
                        return {
                            'success': False,
                            'error': 'Insufficient storage space',
                            'message': 'Cannot add torrent - not enough space available',
                            'space_check': {
                                'torrent_size': torrent_size,
                                'torrent_size_formatted': _format_size(torrent_size),
                                'available_space': available_space,
                                'available_space_formatted': _format_size(available_space),
                                'space_needed': space_needed,
                                'space_needed_formatted': _format_size(space_needed),
                                'sufficient': False
                            }
                        }, 507
            
            # Add torrent
            add_result = client.add_torrent(
                magnet_link=magnet_link,
                folder_id=folder_id
            )
            
            response_data = {
                'success': True,
                'message': 'Torrent added successfully',
                'torrent_info': to_dict(add_result),
                'files': []
            }
            
            # If not waiting, return immediately
            if not wait_for_completion:
                response_data['message'] = 'Torrent added. Set wait_for_completion=true to get download URLs.'
                response_data['status'] = 'added'
                return response_data, 202
            
            # Polling loop to wait for completion
            start_time = time.time()
            torrent_title = getattr(add_result, 'title', '')
            torrent_hash = getattr(add_result, 'torrent_hash', '')
            
            while (time.time() - start_time) < max_wait_seconds:
                try:
                    contents = client.list_contents(folder_id if folder_id != '-1' else '0')
                    
                    # Check if torrent is still downloading
                    is_downloading = False
                    current_progress = 0
                    
                    if hasattr(contents, 'torrents') and contents.torrents:
                        for torrent in contents.torrents:
                            if (hasattr(torrent, 'hash') and torrent.hash == torrent_hash) or \
                               (hasattr(torrent, 'title') and torrent.title == torrent_title):
                                progress = getattr(torrent, 'progress', 0)
                                try:
                                    current_progress = int(float(progress)) if isinstance(progress, str) else int(progress)
                                except:
                                    current_progress = 0
                                
                                if current_progress >= 100:
                                    is_downloading = False
                                    break
                                
                                is_downloading = True
                                break
                    
                    # If not downloading, check for completed folder
                    if not is_downloading:
                        matching_folder = None
                        
                        # Normalize torrent title for matching (Seedr replaces special chars)
                        normalized_title = torrent_title.replace('&', '_').replace(':', ' ').replace('?', '')
                        
                        if hasattr(contents, 'folders') and contents.folders:
                            for folder in contents.folders:
                                folder_name = getattr(folder, 'name', '')
                                # Try exact match first, then normalized match
                                if folder_name == torrent_title or \
                                   folder_name == normalized_title or \
                                   folder_name.replace('&', '_') == torrent_title.replace('&', '_'):
                                    matching_folder = folder
                                    break
                        
                        if matching_folder:
                            # Get files from the folder
                            folder_contents = client.list_contents(str(matching_folder.id))
                            
                            if hasattr(folder_contents, 'files') and folder_contents.files:
                                for file in folder_contents.files:
                                    try:
                                        file_info = client.fetch_file(str(file.folder_file_id))
                                        response_data['files'].append({
                                            'file_id': file.folder_file_id,
                                            'name': file.name,
                                            'size': file.size,
                                            'size_formatted': _format_size(file.size),
                                            'download_url': file_info.url
                                        })
                                    except Exception as e:
                                        response_data['files'].append({
                                            'file_id': file.folder_file_id,
                                            'name': file.name,
                                            'size': file.size,
                                            'error': f'Could not get download link: {str(e)}'
                                        })
                                
                                response_data['folder_id'] = matching_folder.id
                                response_data['message'] = f'Torrent completed! {len(response_data["files"])} file(s) ready for download'
                                response_data['status'] = 'completed'
                                response_data['wait_time_seconds'] = int(time.time() - start_time)
                                
                                # Play in VLC if requested
                                if play_in_vlc:
                                    vlc_results = []
                                    vlc_path = Config.VLC_PATH
                                    
                                    # Check if VLC exists
                                    if not os.path.exists(vlc_path):
                                        response_data['vlc_error'] = f'VLC not found at: {vlc_path}'
                                    else:
                                        # Get files with valid download URLs
                                        valid_files = [f for f in response_data['files'] if 'download_url' in f]
                                        
                                        if valid_files:
                                            # Single file: play directly (no enqueue)
                                            # Multiple files: enqueue all
                                            enqueue = len(valid_files) > 1
                                            
                                            for file in valid_files:
                                                try:
                                                    if enqueue:
                                                        # Enqueue for multiple files
                                                        vlc_command = [vlc_path, "--one-instance", "--playlist-enqueue", file['download_url']]
                                                    else:
                                                        # Play directly for single file
                                                        vlc_command = [vlc_path, file['download_url']]
                                                    
                                                    subprocess.Popen(vlc_command)
                                                    vlc_results.append({
                                                        'file': file['name'],
                                                        'status': 'enqueued' if enqueue else 'playing',
                                                        'success': True
                                                    })
                                                except Exception as e:
                                                    vlc_results.append({
                                                        'file': file['name'],
                                                        'status': 'error',
                                                        'error': str(e),
                                                        'success': False
                                                    })
                                            
                                            response_data['vlc_playback'] = {
                                                'attempted': True,
                                                'mode': 'enqueued' if enqueue else 'playing',
                                                'total_files': len(valid_files),
                                                'results': vlc_results
                                            }
                                        else:
                                            response_data['vlc_error'] = 'No valid download URLs available for VLC playback'
                                
                                return response_data, 200
                    
                    # Still downloading, wait and retry
                    if is_downloading:
                        elapsed = int(time.time() - start_time)
                        logger.debug(f"Torrent downloading: {current_progress}% (elapsed: {elapsed}s)")
                    
                    time.sleep(poll_interval)
                    
                except Exception as e:
                    logger.error(f"Error during polling: {str(e)}")
                    time.sleep(poll_interval)
            
            # Timeout reached
            response_data['message'] = f'Timeout: Torrent still downloading after {max_wait_seconds} seconds. Try again later or check /files/list'
            response_data['status'] = 'timeout'
            response_data['wait_time_seconds'] = int(time.time() - start_time)
            return response_data, 202
            
        except SeedrError as e:
            return {'error': str(e)}, 500
        except Exception as e:
            return {'error': f'Unexpected error: {str(e)}'}, 500


@torrents_ns.route('/add/file')
class AddTorrentFile(Resource):
    @torrents_ns.doc('add_torrent_file')
    @torrents_ns.param('user_id', 'User identifier (default: "default")', _in='query')
    @torrents_ns.expect(upload_parser)
    @torrents_ns.response(200, 'Success')
    @torrents_ns.response(400, 'Validation Error')
    @torrents_ns.response(401, 'Not authenticated')
    @torrents_ns.response(500, 'Server Error')
    def post(self):
        """Add torrent via file upload"""
        logger.info("Processing add torrent file request")
        try:
            user_id = request.args.get('user_id', 'default')
            client = client_manager.get_client(user_id)
            
            if not client:
                return {'error': 'Not authenticated. Please login first.'}, 401
            
            args = upload_parser.parse_args()
            torrent_file = args['file']
            folder_id = args.get('folder_id', '-1')
            wishlist_id = args.get('wishlist_id')
            
            if not torrent_file:
                return {'error': 'Torrent file is required'}, 400
            
            # Read file content
            file_content = torrent_file.read()
            
            result = client.add_torrent(
                torrent_file=file_content,
                wishlist_id=wishlist_id,
                folder_id=folder_id
            )
            
            return {
                'success': True,
                'message': 'Torrent added successfully',
                'result': to_dict(result)
            }, 200
            
        except SeedrError as e:
            return {'error': str(e)}, 500
        except Exception as e:
            return {'error': f'Unexpected error: {str(e)}'}, 500


@torrents_ns.route('/<string:torrent_id>')
class DeleteTorrent(Resource):
    @torrents_ns.doc('delete_torrent')
    @torrents_ns.param('user_id', 'User identifier (default: "default")', _in='query')
    @torrents_ns.response(200, 'Success')
    @torrents_ns.response(401, 'Not authenticated')
    @torrents_ns.response(500, 'Server Error')
    def delete(self, torrent_id):
        """Delete a torrent"""
        logger.info(f"Processing delete torrent request for ID: {torrent_id}")
        try:
            user_id = request.args.get('user_id', 'default')
            client = client_manager.get_client(user_id)
            
            if not client:
                return {'error': 'Not authenticated. Please login first.'}, 401
            
            result = client.delete_torrent(torrent_id)
            
            return {
                'success': True,
                'message': 'Torrent deleted successfully',
                'result': to_dict(result)
            }, 200
            
        except SeedrError as e:
            return {'error': str(e)}, 500
        except Exception as e:
            return {'error': f'Unexpected error: {str(e)}'}, 500




@torrents_ns.route('/wishlist/<string:wishlist_id>')
class DeleteWishlist(Resource):
    @torrents_ns.doc('delete_wishlist')
    @torrents_ns.param('user_id', 'User identifier (default: "default")', _in='query')
    @torrents_ns.response(200, 'Success')
    @torrents_ns.response(401, 'Not authenticated')
    @torrents_ns.response(500, 'Server Error')
    def delete(self, wishlist_id):
        """Delete a wishlist item"""
        try:
            user_id = request.args.get('user_id', 'default')
            client = client_manager.get_client(user_id)
            
            if not client:
                return {'error': 'Not authenticated. Please login first.'}, 401
            
            result = client.delete_wishlist(wishlist_id)
            
            return {
                'success': True,
                'message': 'Wishlist item deleted successfully',
                'result': to_dict(result)
            }, 200
            
        except SeedrError as e:
            return {'error': str(e)}, 500
        except Exception as e:
            return {'error': f'Unexpected error: {str(e)}'}, 500


@torrents_ns.route('/list')
class ListTorrents(Resource):
    @torrents_ns.doc('list_torrents')
    @torrents_ns.param('user_id', 'User identifier (default: "default")', _in='query')
    @torrents_ns.response(200, 'Success')
    @torrents_ns.response(401, 'Not authenticated')
    @torrents_ns.response(500, 'Server Error')
    def get(self):
        """List all active torrents with progress"""
        logger.info("Processing list torrents request")
        try:
            user_id = request.args.get('user_id', 'default')
            client = client_manager.get_client(user_id)
            
            if not client:
                return {'error': 'Not authenticated. Please login first.'}, 401
            
            # Get root folder contents which includes torrents
            contents = client.list_contents()
            
            torrents_list = []
            if hasattr(contents, 'torrents') and contents.torrents:
                for torrent in contents.torrents:
                    torrents_list.append(to_dict(torrent))
            
            return {
                'success': True,
                'torrents': torrents_list,
                'total': len(torrents_list)
            }, 200
            
        except SeedrError as e:
            return {'error': str(e)}, 500
        except Exception as e:
            return {'error': f'Unexpected error: {str(e)}'}, 500


@torrents_ns.route('/metadata')
class TorrentMetadata(Resource):
    @torrents_ns.doc('get_torrent_metadata')
    @torrents_ns.expect(torrents_ns.model('TorrentMetadataRequest', {
        'query': fields.String(required=True, description='Magnet link or torrent file URL')
    }))
    @torrents_ns.response(200, 'Success')
    @torrents_ns.response(400, 'Validation Error')
    @torrents_ns.response(500, 'Server Error')
    def post(self):
        """Get torrent metadata from magnet link or torrent file URL"""
        try:
            data = request.get_json()
            query = data.get('query')
            
            if not query:
                return {'error': 'Query parameter (magnet link or torrent URL) is required'}, 400
            
            # Call TorrentMeta API
            torrentmeta_url = 'https://torrentmeta.fly.dev'
            headers = {'Content-Type': 'application/json'}
            payload = {'query': query}
            
            response = requests.post(
                torrentmeta_url,
                json=payload,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                metadata = response.json()
                return {
                    'success': True,
                    'metadata': metadata
                }, 200
            else:
                return {
                    'error': 'Failed to fetch torrent metadata',
                    'status_code': response.status_code,
                    'details': response.text
                }, 500
                
        except requests.exceptions.Timeout:
            return {'error': 'Request to TorrentMeta API timed out'}, 500
        except requests.exceptions.RequestException as e:
            return {'error': f'Request error: {str(e)}'}, 500
        except Exception as e:
            return {'error': f'Unexpected error: {str(e)}'}, 500

