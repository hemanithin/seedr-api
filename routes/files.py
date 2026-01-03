from flask import request
from flask_restx import Namespace, Resource, fields
from seedrcc.exceptions import SeedrError
from utils import client_manager
from utils.serialization import to_dict


# Create namespace
files_ns = Namespace('files', description='File and folder management operations')


@files_ns.route('/list')
class ListContents(Resource):
    @files_ns.doc('list_contents')
    @files_ns.param('user_id', 'User identifier (default: "default")', _in='query')
    @files_ns.param('folder_id', 'Folder ID to list (default: "0" for root)', _in='query')
    @files_ns.response(200, 'Success')
    @files_ns.response(401, 'Not authenticated')
    @files_ns.response(500, 'Server Error')
    def get(self):
        """List folder contents"""
        try:
            user_id = request.args.get('user_id', 'default')
            folder_id = request.args.get('folder_id', '0')
            
            client = client_manager.get_client(user_id)
            
            if not client:
                return {'error': 'Not authenticated. Please login first.'}, 401
            
            contents = client.list_contents(folder_id)
            return to_dict(contents), 200
            
        except SeedrError as e:
            return {'error': str(e)}, 500
        except Exception as e:
            return {'error': f'Unexpected error: {str(e)}'}, 500


@files_ns.route('/list-all')
class ListAllContents(Resource):
    @files_ns.doc('list_all_contents')
    @files_ns.param('user_id', 'User identifier (default: "default")', _in='query')
    @files_ns.response(200, 'Success')
    @files_ns.response(401, 'Not authenticated')
    @files_ns.response(500, 'Server Error')
    def get(self):
        """Recursively list all files and folders"""
        try:
            user_id = request.args.get('user_id', 'default')
            client = client_manager.get_client(user_id)
            
            if not client:
                return {'error': 'Not authenticated. Please login first.'}, 401
            
            all_folders = []
            all_files = []
            folders_to_process = ['0']  # Start with root
            
            while folders_to_process:
                current_folder_id = folders_to_process.pop(0)
                contents = client.list_contents(current_folder_id)
                
                # Add current folder items
                if hasattr(contents, 'folders') and contents.folders:
                    for folder in contents.folders:
                        all_folders.append(folder)
                        folders_to_process.append(str(folder.id))
                
                if hasattr(contents, 'files') and contents.files:
                    for file in contents.files:
                        all_files.append(file)
            
            return {
                'folders': to_dict(all_folders),
                'files': to_dict(all_files),
                'total_folders': len(all_folders),
                'total_files': len(all_files)
            }, 200
            
        except SeedrError as e:
            return {'error': str(e)}, 500
        except Exception as e:
            return {'error': f'Unexpected error: {str(e)}'}, 500


@files_ns.route('/folder')
class CreateFolder(Resource):
    @files_ns.doc('create_folder')
    @files_ns.param('user_id', 'User identifier (default: "default")', _in='query')
    @files_ns.expect(files_ns.model('CreateFolderRequest', {
        'name': fields.String(required=True, description='Folder name')
    }))
    @files_ns.response(200, 'Success')
    @files_ns.response(400, 'Validation Error')
    @files_ns.response(401, 'Not authenticated')
    @files_ns.response(500, 'Server Error')
    def post(self):
        """Create a new folder"""
        try:
            user_id = request.args.get('user_id', 'default')
            client = client_manager.get_client(user_id)
            
            if not client:
                return {'error': 'Not authenticated. Please login first.'}, 401
            
            data = request.get_json()
            name = data.get('name')
            
            if not name:
                return {'error': 'Folder name is required'}, 400
            
            result = client.add_folder(name)
            
            return {
                'success': True,
                'message': 'Folder created successfully',
                'result': to_dict(result)
            }, 200
            
        except SeedrError as e:
            return {'error': str(e)}, 500
        except Exception as e:
            return {'error': f'Unexpected error: {str(e)}'}, 500


@files_ns.route('/file/<string:file_id>/rename')
class RenameFile(Resource):
    @files_ns.doc('rename_file')
    @files_ns.param('user_id', 'User identifier (default: "default")', _in='query')
    @files_ns.expect(files_ns.model('RenameRequest', {
        'new_name': fields.String(required=True, description='New file name')
    }))
    @files_ns.response(200, 'Success')
    @files_ns.response(400, 'Validation Error')
    @files_ns.response(401, 'Not authenticated')
    @files_ns.response(500, 'Server Error')
    def put(self, file_id):
        """Rename a file"""
        try:
            user_id = request.args.get('user_id', 'default')
            client = client_manager.get_client(user_id)
            
            if not client:
                return {'error': 'Not authenticated. Please login first.'}, 401
            
            data = request.get_json()
            new_name = data.get('new_name')
            
            if not new_name:
                return {'error': 'New name is required'}, 400
            
            result = client.rename_file(file_id, rename_to=new_name)
            
            return {
                'success': True,
                'message': 'File renamed successfully',
                'result': to_dict(result)
            }, 200
            
        except SeedrError as e:
            return {'error': str(e)}, 500
        except Exception as e:
            return {'error': f'Unexpected error: {str(e)}'}, 500


@files_ns.route('/folder/<string:folder_id>/rename')
class RenameFolder(Resource):
    @files_ns.doc('rename_folder')
    @files_ns.param('user_id', 'User identifier (default: "default")', _in='query')
    @files_ns.expect(files_ns.model('RenameFolderRequest', {
        'new_name': fields.String(required=True, description='New folder name')
    }))
    @files_ns.response(200, 'Success')
    @files_ns.response(400, 'Validation Error')
    @files_ns.response(401, 'Not authenticated')
    @files_ns.response(500, 'Server Error')
    def put(self, folder_id):
        """Rename a folder"""
        try:
            user_id = request.args.get('user_id', 'default')
            client = client_manager.get_client(user_id)
            
            if not client:
                return {'error': 'Not authenticated. Please login first.'}, 401
            
            data = request.get_json()
            new_name = data.get('new_name')
            
            if not new_name:
                return {'error': 'New name is required'}, 400
            
            result = client.rename_folder(folder_id, rename_to=new_name)
            
            return {
                'success': True,
                'message': 'Folder renamed successfully',
                'result': to_dict(result)
            }, 200
            
        except SeedrError as e:
            return {'error': str(e)}, 500
        except Exception as e:
            return {'error': f'Unexpected error: {str(e)}'}, 500


@files_ns.route('/file/<string:file_id>')
class DeleteFile(Resource):
    @files_ns.doc('delete_file')
    @files_ns.param('user_id', 'User identifier (default: "default")', _in='query')
    @files_ns.response(200, 'Success')
    @files_ns.response(401, 'Not authenticated')
    @files_ns.response(500, 'Server Error')
    def delete(self, file_id):
        """Delete a file"""
        try:
            user_id = request.args.get('user_id', 'default')
            client = client_manager.get_client(user_id)
            
            if not client:
                return {'error': 'Not authenticated. Please login first.'}, 401
            
            result = client.delete_file(file_id)
            
            return {
                'success': True,
                'message': 'File deleted successfully',
                'result': to_dict(result)
            }, 200
            
        except SeedrError as e:
            return {'error': str(e)}, 500
        except Exception as e:
            return {'error': f'Unexpected error: {str(e)}'}, 500


@files_ns.route('/folder/<string:folder_id>')
class DeleteFolder(Resource):
    @files_ns.doc('delete_folder')
    @files_ns.param('user_id', 'User identifier (default: "default")', _in='query')
    @files_ns.response(200, 'Success')
    @files_ns.response(401, 'Not authenticated')
    @files_ns.response(500, 'Server Error')
    def delete(self, folder_id):
        """Delete a folder"""
        try:
            user_id = request.args.get('user_id', 'default')
            client = client_manager.get_client(user_id)
            
            if not client:
                return {'error': 'Not authenticated. Please login first.'}, 401
            
            result = client.delete_folder(folder_id)
            
            return {
                'success': True,
                'message': 'Folder deleted successfully',
                'result': to_dict(result)
            }, 200
            
        except SeedrError as e:
            return {'error': str(e)}, 500
        except Exception as e:
            return {'error': f'Unexpected error: {str(e)}'}, 500


@files_ns.route('/search')
class SearchFiles(Resource):
    @files_ns.doc('search_files')
    @files_ns.param('user_id', 'User identifier (default: "default")', _in='query')
    @files_ns.param('query', 'Search query', _in='query', required=True)
    @files_ns.response(200, 'Success')
    @files_ns.response(400, 'Validation Error')
    @files_ns.response(401, 'Not authenticated')
    @files_ns.response(500, 'Server Error')
    def get(self):
        """Search files by query"""
        try:
            user_id = request.args.get('user_id', 'default')
            query = request.args.get('query')
            
            if not query:
                return {'error': 'Search query is required'}, 400
            
            client = client_manager.get_client(user_id)
            
            if not client:
                return {'error': 'Not authenticated. Please login first.'}, 401
            
            results = client.search_files(query)
            
            return {'results': to_dict(results)}, 200
            
        except SeedrError as e:
            return {'error': str(e)}, 500
        except Exception as e:
            return {'error': f'Unexpected error: {str(e)}'}, 500


@files_ns.route('/fetch/<string:file_id>')
class FetchFile(Resource):
    @files_ns.doc('fetch_file')
    @files_ns.param('user_id', 'User identifier (default: "default")', _in='query')
    @files_ns.response(200, 'Success')
    @files_ns.response(401, 'Not authenticated')
    @files_ns.response(500, 'Server Error')
    def get(self, file_id):
        """Get file download URL"""
        try:
            user_id = request.args.get('user_id', 'default')
            client = client_manager.get_client(user_id)
            
            if not client:
                return {'error': 'Not authenticated. Please login first.'}, 401
            
            file_info = client.fetch_file(file_id)
            
            return to_dict(file_info), 200
            
        except SeedrError as e:
            error_msg = str(e)
            if "Invalid JSON" in error_msg:
                return {
                    'error': 'Seedr API returned an invalid response. This usually happens if the file ID is incorrect, it belongs to a folder, or download limits are reached.',
                    'suggestion': 'If you are trying to download a folder, please use the Archive/Download Folder feature.'
                }, 400
            return {'error': error_msg}, 500
        except Exception as e:
            return {'error': f'Unexpected error: {str(e)}'}, 500


@files_ns.route('/archive/<string:folder_id>')
class CreateArchive(Resource):
    @files_ns.doc('create_archive')
    @files_ns.param('user_id', 'User identifier (default: "default")', _in='query')
    @files_ns.response(200, 'Success')
    @files_ns.response(401, 'Not authenticated')
    @files_ns.response(500, 'Server Error')
    def post(self, folder_id):
        """Create archive from folder"""
        try:
            user_id = request.args.get('user_id', 'default')
            client = client_manager.get_client(user_id)
            
            if not client:
                return {'error': 'Not authenticated. Please login first.'}, 401
            
            # Get folder contents and return download links for all files
            folder_contents = client.list_contents(folder_id)
            
            files_with_links = []
            
            # Iterate through all files in the folder
            if hasattr(folder_contents, 'files') and folder_contents.files:
                for file in folder_contents.files:
                    try:
                        # Get download URL for each file
                        file_info = client.fetch_file(str(file.folder_file_id))
                        files_with_links.append({
                            'file_id': file.folder_file_id,
                            'name': file.name,
                            'size': file.size,
                            'download_url': file_info.url
                        })
                    except Exception as e:
                        files_with_links.append({
                            'file_id': file.folder_file_id,
                            'name': file.name,
                            'size': file.size,
                            'error': f'Could not get download link: {str(e)}'
                        })
            
            return {
                'success': True,
                'message': f'Found {len(files_with_links)} files in folder',
                'folder_id': folder_id,
                'files': files_with_links,
                'total_files': len(files_with_links)
            }, 200
            
        except SeedrError as e:
            return {'error': str(e)}, 500
        except Exception as e:
            return {'error': f'Unexpected error: {str(e)}'}, 500


@files_ns.route('/archive/<string:archive_id>/status')
class ArchiveStatus(Resource):
    @files_ns.doc('archive_status')
    @files_ns.param('user_id', 'User identifier (default: "default")', _in='query')
    @files_ns.response(200, 'Success')
    @files_ns.response(202, 'In Progress')
    @files_ns.response(401, 'Not authenticated')
    @files_ns.response(500, 'Server Error')
    def get(self, archive_id):
        """Check status of a folder archive and get download URL if ready"""
        try:
            user_id = request.args.get('user_id', 'default')
            client = client_manager.get_client(user_id)
            
            if not client:
                return {'error': 'Not authenticated. Please login first.'}, 401
            
            try:
                # We use fetch_file to check if the archive is ready
                file_info = client.fetch_file(archive_id)
                
                # Note: Even if fetch_file returns a URL, it might 404 for a few seconds 
                # while Seedr is physically zipping the file on their storage.
                
                return {
                    'status': 'ready',
                    'message': 'Archive link generated. Note: If you get a 404, please wait 5-10 seconds for Seedr to finish zipping.',
                    'download_url': file_info.url,
                    'name': file_info.name,
                    'file_id': archive_id
                }, 200
            except SeedrError as e:
                error_str = str(e)
                if "Invalid JSON" in error_str or "Not Found" in error_str:
                    return {
                        'status': 'in_progress',
                        'message': 'Archive is still being created or registered by Seedr. Please wait a moment and check again.',
                        'archive_id': archive_id
                    }, 202
                raise e
                
        except SeedrError as e:
            return {'error': str(e)}, 500
        except Exception as e:
            return {'error': f'Unexpected error: {str(e)}'}, 500
