from flask import request
from flask_restx import Namespace, Resource, fields
from seedrcc.exceptions import SeedrError
from utils import client_manager
from utils.serialization import to_dict


# Create namespace
account_ns = Namespace('account', description='Account management operations')


@account_ns.route('/settings')
class Settings(Resource):
    @account_ns.doc('get_settings')
    @account_ns.param('user_id', 'User identifier (default: "default")', _in='query')
    @account_ns.response(200, 'Success')
    @account_ns.response(401, 'Not authenticated')
    @account_ns.response(500, 'Server Error')
    def get(self):
        """Get account settings"""
        try:
            user_id = request.args.get('user_id', 'default')
            client = client_manager.get_client(user_id)
            
            if not client:
                return {'error': 'Not authenticated. Please login first.'}, 401
            
            settings = client.get_settings()
            
            return to_dict(settings), 200
            
        except SeedrError as e:
            return {'error': str(e)}, 500
        except Exception as e:
            return {'error': f'Unexpected error: {str(e)}'}, 500


@account_ns.route('/memory-bandwidth')
class MemoryBandwidth(Resource):
    @account_ns.doc('get_memory_bandwidth')
    @account_ns.param('user_id', 'User identifier (default: "default")', _in='query')
    @account_ns.response(200, 'Success')
    @account_ns.response(401, 'Not authenticated')
    @account_ns.response(500, 'Server Error')
    def get(self):
        """Get memory and bandwidth usage"""
        try:
            user_id = request.args.get('user_id', 'default')
            client = client_manager.get_client(user_id)
            
            if not client:
                return {'error': 'Not authenticated. Please login first.'}, 401
            
            memory_bandwidth = client.get_memory_bandwidth()
            
            return to_dict(memory_bandwidth), 200
            
        except SeedrError as e:
            return {'error': str(e)}, 500
        except Exception as e:
            return {'error': f'Unexpected error: {str(e)}'}, 500


@account_ns.route('/devices')
class Devices(Resource):
    @account_ns.doc('get_devices')
    @account_ns.param('user_id', 'User identifier (default: "default")', _in='query')
    @account_ns.response(200, 'Success')
    @account_ns.response(401, 'Not authenticated')
    @account_ns.response(500, 'Server Error')
    def get(self):
        """Get list of authorized devices"""
        try:
            user_id = request.args.get('user_id', 'default')
            client = client_manager.get_client(user_id)
            
            if not client:
                return {'error': 'Not authenticated. Please login first.'}, 401
            
            devices = client.get_devices()
            
            return {'devices': to_dict(devices)}, 200
            
        except SeedrError as e:
            return {'error': str(e)}, 500
        except Exception as e:
            return {'error': f'Unexpected error: {str(e)}'}, 500


@account_ns.route('/name')
class ChangeName(Resource):
    @account_ns.doc('change_name')
    @account_ns.param('user_id', 'User identifier (default: "default")', _in='query')
    @account_ns.expect(account_ns.model('ChangeNameRequest', {
        'name': fields.String(required=True, description='New account name'),
        'password': fields.String(required=True, description='Current password for verification')
    }))
    @account_ns.response(200, 'Success')
    @account_ns.response(400, 'Validation Error')
    @account_ns.response(401, 'Not authenticated')
    @account_ns.response(500, 'Server Error')
    def put(self):
        """Change account name"""
        try:
            user_id = request.args.get('user_id', 'default')
            client = client_manager.get_client(user_id)
            
            if not client:
                return {'error': 'Not authenticated. Please login first.'}, 401
            
            data = request.get_json()
            name = data.get('name')
            password = data.get('password')
            
            if not name or not password:
                return {'error': 'Name and password are required'}, 400
            
            result = client.change_name(name, password)
            
            return {
                'success': True,
                'message': 'Name changed successfully',
                'result': to_dict(result)
            }, 200
            
        except SeedrError as e:
            return {'error': str(e)}, 500
        except Exception as e:
            return {'error': f'Unexpected error: {str(e)}'}, 500


@account_ns.route('/password')
class ChangePassword(Resource):
    @account_ns.doc('change_password')
    @account_ns.param('user_id', 'User identifier (default: "default")', _in='query')
    @account_ns.expect(account_ns.model('ChangePasswordRequest', {
        'old_password': fields.String(required=True, description='Current password'),
        'new_password': fields.String(required=True, description='New password')
    }))
    @account_ns.response(200, 'Success')
    @account_ns.response(400, 'Validation Error')
    @account_ns.response(401, 'Not authenticated')
    @account_ns.response(500, 'Server Error')
    def put(self):
        """Change account password"""
        try:
            user_id = request.args.get('user_id', 'default')
            client = client_manager.get_client(user_id)
            
            if not client:
                return {'error': 'Not authenticated. Please login first.'}, 401
            
            data = request.get_json()
            old_password = data.get('old_password')
            new_password = data.get('new_password')
            
            if not old_password or not new_password:
                return {'error': 'Old password and new password are required'}, 400
            
            result = client.change_password(old_password, new_password)
            
            return {
                'success': True,
                'message': 'Password changed successfully',
                'result': to_dict(result)
            }, 200
            
        except SeedrError as e:
            return {'error': str(e)}, 500
        except Exception as e:
            return {'error': f'Unexpected error: {str(e)}'}, 500
