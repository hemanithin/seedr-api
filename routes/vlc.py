from flask import request
from flask_restx import Namespace, Resource, fields
import subprocess
import os

# Create namespace
vlc_ns = Namespace('vlc', description='VLC media player operations')

# VLC path configuration - Windows default
VLC_PATH = r"C:\Program Files\VideoLAN\VLC\vlc.exe"
# For Linux: VLC_PATH = "/usr/bin/vlc"
# For macOS: VLC_PATH = "/Applications/VLC.app/Contents/MacOS/VLC"


@vlc_ns.route('/play')
class PlayInVLC(Resource):
    @vlc_ns.doc('play_in_vlc')
    @vlc_ns.expect(vlc_ns.model('PlayRequest', {
        'url': fields.String(required=True, description='Download URL to play in VLC'),
        'enqueue': fields.Boolean(description='Add to playlist instead of playing immediately (default: false)', default=False)
    }))
    @vlc_ns.response(200, 'Success - VLC opened')
    @vlc_ns.response(400, 'Validation Error')
    @vlc_ns.response(404, 'VLC not found')
    @vlc_ns.response(500, 'Server Error')
    def post(self):
        """Play a download URL in VLC media player"""
        try:
            data = request.json
            url = data.get('url')
            enqueue = data.get('enqueue', False)

            if not url:
                return {'error': 'URL is required'}, 400

            # Check if VLC exists
            if not os.path.exists(VLC_PATH):
                return {
                    'error': 'VLC not found',
                    'message': f'VLC media player not found at: {VLC_PATH}',
                    'suggestion': 'Please install VLC or update VLC_PATH in routes/vlc.py'
                }, 404

            # Build VLC command
            if enqueue:
                # Add to playlist without starting playback immediately
                vlc_command = [VLC_PATH, "--one-instance", "--playlist-enqueue", url]
            else:
                # Play immediately
                vlc_command = [VLC_PATH, url]

            # Launch VLC
            subprocess.Popen(vlc_command)

            return {
                'success': True,
                'message': 'VLC opened successfully',
                'url': url,
                'mode': 'enqueued' if enqueue else 'playing'
            }, 200

        except FileNotFoundError:
            return {
                'error': 'VLC executable not found',
                'message': f'Could not find VLC at: {VLC_PATH}'
            }, 404
        except Exception as e:
            return {'error': f'Unexpected error: {str(e)}'}, 500


@vlc_ns.route('/config')
class VLCConfig(Resource):
    @vlc_ns.doc('get_vlc_config')
    @vlc_ns.response(200, 'Success')
    def get(self):
        """Get current VLC configuration"""
        return {
            'vlc_path': VLC_PATH,
            'vlc_exists': os.path.exists(VLC_PATH),
            'platform': os.name
        }, 200
