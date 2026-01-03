from flask import request
from flask_restx import Namespace, Resource, fields
from seedrcc import Seedr
from seedrcc.exceptions import SeedrError
from utils import client_manager
from utils.serialization import to_dict


# Create namespace
auth_ns = Namespace('auth', description='Authentication operations')


@auth_ns.route('/device-code')
class DeviceCode(Resource):
    @auth_ns.doc('get_device_code')
    @auth_ns.response(200, 'Success')
    @auth_ns.response(500, 'Server Error')
    def post(self):
        """Get device code for authentication"""
        try:
            device_code_data = Seedr.get_device_code()
            return to_dict(device_code_data), 200
        except SeedrError as e:
            return {'error': str(e)}, 500
        except Exception as e:
            return {'error': f'Unexpected error: {str(e)}'}, 500


@auth_ns.route('/login/password')
class PasswordLogin(Resource):
    @auth_ns.doc('login_with_password')
    @auth_ns.expect(auth_ns.model('PasswordLoginRequest', {
        'username': fields.String(required=True, description='Seedr username/email'),
        'password': fields.String(required=True, description='Seedr password')
    }))
    @auth_ns.response(200, 'Success')
    @auth_ns.response(400, 'Validation Error')
    @auth_ns.response(401, 'Authentication Failed')
    @auth_ns.response(500, 'Server Error')
    def post(self):
        """Login with username and password"""
        try:
            data = request.get_json()
            username = data.get('username')
            password = data.get('password')
            
            if not username or not password:
                return {'error': 'Username and password are required'}, 400
            
            client = client_manager.create_client_from_password(username, password)
            
            # Get token info
            token_info = {
                'message': 'Login successful',
                'user_id': username
            }
            
            if hasattr(client, 'token') and client.token:
                token_info['token'] = to_dict(client.token)
            
            return token_info, 200
            
        except SeedrError as e:
            return {'error': f'Authentication failed: {str(e)}'}, 401
        except Exception as e:
            return {'error': f'Unexpected error: {str(e)}'}, 500


@auth_ns.route('/login/device-code')
class DeviceCodeLogin(Resource):
    @auth_ns.doc('login_with_device_code')
    @auth_ns.expect(auth_ns.model('DeviceCodeLoginRequest', {
        'device_code': fields.String(required=True, description='Device code from get_device_code'),
        'user_id': fields.String(description='Optional user identifier (default: "default")')
    }))
    @auth_ns.response(200, 'Success')
    @auth_ns.response(400, 'Validation Error')
    @auth_ns.response(401, 'Authentication Failed')
    @auth_ns.response(500, 'Server Error')
    def post(self):
        """Login with device code"""
        try:
            data = request.get_json()
            device_code = data.get('device_code')
            user_id = data.get('user_id', 'default')
            
            if not device_code:
                return {'error': 'Device code is required'}, 400
            
            client = client_manager.create_client_from_device_code(device_code, user_id)
            
            # Get token info
            token_info = {
                'message': 'Login successful',
                'user_id': user_id
            }
            
            if hasattr(client, 'token') and client.token:
                token_info['token'] = to_dict(client.token)
            
            return token_info, 200
            
        except SeedrError as e:
            return {'error': f'Authentication failed: {str(e)}'}, 401
        except Exception as e:
            return {'error': f'Unexpected error: {str(e)}'}, 500


@auth_ns.route('/login/refresh-token')
class RefreshTokenLogin(Resource):
    @auth_ns.doc('login_with_refresh_token')
    @auth_ns.expect(auth_ns.model('RefreshTokenRequest', {
        'refresh_token': fields.String(required=True, description='Refresh token'),
        'user_id': fields.String(description='Optional user identifier (default: "default")')
    }))
    @auth_ns.response(200, 'Success')
    @auth_ns.response(400, 'Validation Error')
    @auth_ns.response(401, 'Authentication Failed')
    @auth_ns.response(500, 'Server Error')
    def post(self):
        """Login with refresh token"""
        try:
            data = request.get_json()
            refresh_token = data.get('refresh_token')
            user_id = data.get('user_id', 'default')
            
            if not refresh_token:
                return {'error': 'Refresh token is required'}, 400
            
            client = client_manager.create_client_from_refresh_token(refresh_token, user_id)
            
            # Get token info
            token_info = {
                'message': 'Login successful',
                'user_id': user_id
            }
            
            if hasattr(client, 'token') and client.token:
                token_info['token'] = to_dict(client.token)
            
            return token_info, 200
            
        except SeedrError as e:
            return {'error': f'Authentication failed: {str(e)}'}, 401
        except Exception as e:
            return {'error': f'Unexpected error: {str(e)}'}, 500


@auth_ns.route('/refresh')
class RefreshToken(Resource):
    @auth_ns.doc('refresh_access_token')
    @auth_ns.param('user_id', 'User identifier (default: "default")', _in='query')
    @auth_ns.response(200, 'Success')
    @auth_ns.response(401, 'Not authenticated')
    @auth_ns.response(500, 'Server Error')
    def post(self):
        """Refresh access token"""
        try:
            user_id = request.args.get('user_id', 'default')
            client = client_manager.get_client(user_id)
            
            if not client:
                return {'error': 'Not authenticated. Please login first.'}, 401
            
            client.refresh_token()
            
            token_info = {
                'message': 'Token refreshed successfully',
                'user_id': user_id
            }
            
            client.refresh_token()
            
            token_info = {
                'message': 'Token refreshed successfully',
                'user_id': user_id
            }
            
            if hasattr(client, 'token') and client.token:
                token_info['token'] = to_dict(client.token)
            
            return token_info, 200
            
        except SeedrError as e:
            return {'error': f'Token refresh failed: {str(e)}'}, 401
        except Exception as e:
            return {'error': f'Unexpected error: {str(e)}'}, 500


@auth_ns.route('/logout')
class Logout(Resource):
    @auth_ns.doc('logout')
    @auth_ns.param('user_id', 'User identifier (default: "default")', _in='query')
    @auth_ns.response(200, 'Success')
    def post(self):
        """Logout and remove stored session"""
        try:
            user_id = request.args.get('user_id', 'default')
            client_manager.remove_client(user_id)
            return {'message': 'Logged out successfully'}, 200
        except Exception as e:
            return {'error': f'Unexpected error: {str(e)}'}, 500
