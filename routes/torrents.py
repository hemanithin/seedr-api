from flask import request
from flask_restx import Namespace, Resource, fields
from werkzeug.datastructures import FileStorage
from seedrcc.exceptions import SeedrError
from utils import client_manager
from utils.serialization import to_dict
import requests


# Create namespace
torrents_ns = Namespace('torrents', description='Torrent management operations')

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
            
            return {
                'success': True,
                'message': 'Torrent added successfully',
                'result': to_dict(result)
            }, 200
            
        except SeedrError as e:
            return {'error': str(e)}, 500
        except Exception as e:
            return {'error': f'Unexpected error: {str(e)}'}, 500


# Helper functions for smart add
def _get_torrent_size(magnet_link):
    """Get torrent size from TorrentMeta API"""
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
        print(f"Error fetching torrent size: {str(e)}")
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

