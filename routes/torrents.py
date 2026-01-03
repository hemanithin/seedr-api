from flask import request
from flask_restx import Namespace, Resource, fields
from werkzeug.datastructures import FileStorage
from seedrcc.exceptions import SeedrError
from utils import client_manager
from utils.serialization import to_dict


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
