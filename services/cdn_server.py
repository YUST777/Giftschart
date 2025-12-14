#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
CDN Server for Telegram Bot Assets
Serves files directly like: https://test.asadffastest.store/api/new_gift_cards/Electric_Skull_card.webp
"""

from flask import Flask, jsonify, send_from_directory, request
import os
import logging
from datetime import datetime
import mimetypes

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Base directory - use script_dir for Docker compatibility
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


# Define the folders to serve
FOLDERS = {
    "sticker_price_cards": "Sticker_Price_Cards",
    "new_gift_cards": "new_gift_cards", 
    "sticker_collections": "sticker_collections",
    "downloaded_images": "downloaded_images",
    "assets": "assets"
}

def get_file_info(file_path):
    """Get file information including size and modification time"""
    try:
        stat = os.stat(file_path)
        return {
            "size": stat.st_size,
            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "exists": True
        }
    except OSError:
        return {"exists": False}

def list_files_recursive(folder_path, base_path=""):
    """Recursively list all files in a folder and its subfolders"""
    files = []
    try:
        for item in os.listdir(folder_path):
            item_path = os.path.join(folder_path, item)
            relative_path = os.path.join(base_path, item) if base_path else item
            
            if os.path.isfile(item_path):
                file_info = get_file_info(item_path)
                files.append({
                    "name": item,
                    "path": relative_path,
                    "size": file_info.get("size", 0),
                    "modified": file_info.get("modified"),
                    "url": f"/api/sticker_collections/{relative_path}"
                })
            elif os.path.isdir(item_path):
                # Recursively get files from subdirectories
                subfiles = list_files_recursive(item_path, relative_path)
                files.extend(subfiles)
    except Exception as e:
        logger.error(f"Error listing files in {folder_path}: {e}")
    
    return files

@app.route("/")
def index():
    """Main endpoint showing available folders and API info"""
    return jsonify({
        "cdn_name": "Telegram Bot Assets CDN",
        "version": "1.0.0",
        "description": "Direct file serving CDN",
        "available_endpoints": list(FOLDERS.keys()),
        "api_endpoints": {
            "list_files": "/api/<folder_key>",
            "serve_file": "/api/<folder_key>/<filename>",
            "file_info": "/api/<folder_key>/<filename>/info",
            "search": "/api/<folder_key>/search_files?q=<query>",
            "sticker_collections": "/api/sticker_collections/<collection>/<pack>/<filename>"
        },
        "total_folders": len(FOLDERS),
        "server_time": datetime.now().isoformat(),
        "base_url": "https://giftschart.the01studio.xyz"
    })

@app.route("/api/<folder_key>")
def list_folder(folder_key):
    """List all files in a specific folder"""
    folder_name = FOLDERS.get(folder_key)
    if not folder_name:
        return jsonify({"error": "Invalid folder key"}), 404
    
    folder_path = os.path.join(BASE_DIR, folder_name)
    if not os.path.exists(folder_path):
        return jsonify({"error": "Folder not found"}), 404
    
    try:
        # Special handling for sticker_collections (recursive)
        if folder_key == "sticker_collections":
            files = list_files_recursive(folder_path)
        else:
            # Regular flat folder listing
            files = []
            for item in os.listdir(folder_path):
                item_path = os.path.join(folder_path, item)
                if os.path.isfile(item_path):
                    file_info = get_file_info(item_path)
                    files.append({
                        "name": item,
                        "path": item,
                        "size": file_info.get("size", 0),
                        "modified": file_info.get("modified"),
                        "url": f"/api/{folder_key}/{item}"
                    })
        
        return jsonify({
            "folder": folder_key,
            "folder_name": folder_name,
            "total_files": len(files),
            "files": files
        })
    except Exception as e:
        logger.error(f"Error listing folder {folder_key}: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route("/api/<folder_key>/<path:filename>")
def serve_file(folder_key, filename):
    """Serve a specific file from a folder - DIRECT FILE SERVING"""
    folder_name = FOLDERS.get(folder_key)
    if not folder_name:
        return jsonify({"error": "Invalid folder key"}), 404
    
    folder_path = os.path.join(BASE_DIR, folder_name)
    
    # Special handling for sticker_collections (nested paths)
    if folder_key == "sticker_collections":
        file_path = os.path.join(folder_path, filename)
        # Extract the directory part for send_from_directory
        file_dir = os.path.dirname(file_path)
        file_name = os.path.basename(file_path)
        
        if not os.path.exists(file_path) or not os.path.isfile(file_path):
            return jsonify({"error": "File not found"}), 404
        
        try:
            # Set appropriate headers for different file types
            mime_type, _ = mimetypes.guess_type(filename)
            
            # Handle _png files as PNG images
            if filename.endswith('_png'):
                mime_type = 'image/png'
            elif filename.endswith('.webp'):
                mime_type = 'image/png'
            elif filename.endswith('.jpg') or filename.endswith('.jpeg'):
                mime_type = 'image/jpeg'
            elif filename.endswith('.gif'):
                mime_type = 'image/gif'
            elif filename.endswith('.webp'):
                mime_type = 'image/webp'
            
            response = send_from_directory(file_dir, file_name)
            if mime_type:
                response.headers['Content-Type'] = mime_type
            response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'  # No caching - always fresh
            response.headers['Pragma'] = 'no-cache'  # HTTP/1.0 compatibility
            response.headers['Expires'] = '0'  # Expire immediately
            response.headers['Content-Disposition'] = 'inline'  # Display in browser, don't download
            return response
        except Exception as e:
            logger.error(f"Error serving file {filename} from {folder_key}: {e}")
            return jsonify({"error": "Internal server error"}), 500
    else:
        # Regular flat folder serving
        file_path = os.path.join(folder_path, filename)
        
        if not os.path.exists(file_path) or not os.path.isfile(file_path):
            return jsonify({"error": "File not found"}), 404
        
        try:
            # Set appropriate headers for different file types
            mime_type, _ = mimetypes.guess_type(filename)
            
            # Handle _png files as PNG images
            if filename.endswith('_png'):
                mime_type = 'image/png'
            elif filename.endswith('.webp'):
                mime_type = 'image/png'
            elif filename.endswith('.jpg') or filename.endswith('.jpeg'):
                mime_type = 'image/jpeg'
            elif filename.endswith('.gif'):
                mime_type = 'image/gif'
            elif filename.endswith('.webp'):
                mime_type = 'image/webp'
            
            response = send_from_directory(folder_path, filename)
            if mime_type:
                response.headers['Content-Type'] = mime_type
            response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'  # No caching - always fresh
            response.headers['Pragma'] = 'no-cache'  # HTTP/1.0 compatibility
            response.headers['Expires'] = '0'  # Expire immediately
            response.headers['Content-Disposition'] = 'inline'  # Display in browser, don't download
            return response
        except Exception as e:
            logger.error(f"Error serving file {filename} from {folder_key}: {e}")
            return jsonify({"error": "Internal server error"}), 500

@app.route("/api/<folder_key>/<path:filename>/info")
def file_info(folder_key, filename):
    """Get information about a specific file"""
    folder_name = FOLDERS.get(folder_key)
    if not folder_name:
        return jsonify({"error": "Invalid folder key"}), 404
    
    folder_path = os.path.join(BASE_DIR, folder_name)
    
    # Special handling for sticker_collections (nested paths)
    if folder_key == "sticker_collections":
        file_path = os.path.join(folder_path, filename)
    else:
        file_path = os.path.join(folder_path, filename)
    
    if not os.path.exists(file_path):
        return jsonify({"error": "File not found"}), 404
    
    try:
        file_info = get_file_info(file_path)
        if not file_info["exists"]:
            return jsonify({"error": "File not accessible"}), 500
        
        mime_type, encoding = mimetypes.guess_type(filename)
        
        return jsonify({
            "filename": os.path.basename(filename),
            "path": filename,
            "folder": folder_key,
            "size": file_info["size"],
            "modified": file_info["modified"],
            "mime_type": mime_type,
            "encoding": encoding,
            "url": f"https://giftschart.the01studio.xyz/api/{folder_key}/{filename}",
            "info_url": f"https://giftschart.the01studio.xyz/api/{folder_key}/{filename}/info"
        })
    except Exception as e:
        logger.error(f"Error getting file info for {filename} from {folder_key}: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route("/api/<folder_key>/search_files")
def search_files(folder_key):
    """Search for files in a folder"""
    folder_name = FOLDERS.get(folder_key)
    if not folder_name:
        return jsonify({"error": "Invalid folder key"}), 404
    
    query = request.args.get('q', '').lower()
    if not query:
        return jsonify({"error": "Search query required"}), 400
    
    folder_path = os.path.join(BASE_DIR, folder_name)
    if not os.path.exists(folder_path):
        return jsonify({"error": "Folder not found"}), 404
    
    try:
        matching_files = []
        
        # Special handling for sticker_collections (recursive search)
        if folder_key == "sticker_collections":
            all_files = list_files_recursive(folder_path)
            for file_info in all_files:
                if query in file_info["name"].lower() or query in file_info["path"].lower():
                    matching_files.append(file_info)
        else:
            # Regular flat folder search
            for item in os.listdir(folder_path):
                if query in item.lower():
                    item_path = os.path.join(folder_path, item)
                    if os.path.isfile(item_path):
                        file_info = get_file_info(item_path)
                        matching_files.append({
                            "name": item,
                            "path": item,
                            "size": file_info.get("size", 0),
                            "modified": file_info.get("modified"),
                            "url": f"/api/{folder_key}/{item}"
                        })
        
        return jsonify({
            "folder": folder_key,
            "query": query,
            "total_matches": len(matching_files),
            "files": matching_files
        })
    except Exception as e:
        logger.error(f"Error searching in folder {folder_key}: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route("/api/sticker_collections/<collection>")
def list_collection(collection):
    """List all packs in a specific sticker collection"""
    folder_path = os.path.join(BASE_DIR, "sticker_collections", collection)
    if not os.path.exists(folder_path):
        return jsonify({"error": "Collection not found"}), 404
    
    try:
        packs = []
        for item in os.listdir(folder_path):
            item_path = os.path.join(folder_path, item)
            if os.path.isdir(item_path):
                # Count files in this pack
                pack_files = list_files_recursive(item_path, item)
                packs.append({
                    "name": item,
                    "total_files": len(pack_files),
                    "url": f"/api/sticker_collections/{collection}/{item}"
                })
        
        return jsonify({
            "collection": collection,
            "total_packs": len(packs),
            "packs": packs
        })
    except Exception as e:
        logger.error(f"Error listing collection {collection}: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route("/api/sticker_collections/<collection>/<pack>")
def list_pack(collection, pack):
    """List all files in a specific sticker pack"""
    pack_path = os.path.join(BASE_DIR, "sticker_collections", collection, pack)
    if not os.path.exists(pack_path):
        return jsonify({"error": "Pack not found"}), 404
    
    try:
        files = list_files_recursive(pack_path, f"{collection}/{pack}")
        
        return jsonify({
            "collection": collection,
            "pack": pack,
            "total_files": len(files),
            "files": files
        })
    except Exception as e:
        logger.error(f"Error listing pack {collection}/{pack}: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route("/health")
def health_check():
    """Health check endpoint"""
    try:
        # Check if all folders exist
        folder_status = {}
        for key, folder_name in FOLDERS.items():
            folder_path = os.path.join(BASE_DIR, folder_name)
            folder_status[key] = {
                "exists": os.path.exists(folder_path),
                "path": folder_path
            }
        
        return jsonify({
            "status": "healthy",
            "server_time": datetime.now().isoformat(),
            "folders": folder_status
        })
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({"status": "unhealthy", "error": str(e)}), 500

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return jsonify({"error": "Internal server error"}), 500

if __name__ == "__main__":
    # Configuration
    HOST = "0.0.0.0"  # Listen on all interfaces
    PORT = 4000       # Changed to port 4000 as requested
    
    # Check if folders exist
    missing_folders = []
    for key, folder_name in FOLDERS.items():
        folder_path = os.path.join(BASE_DIR, folder_name)
        if not os.path.exists(folder_path):
            missing_folders.append(folder_name)
    
    if missing_folders:
        logger.warning(f"Missing folders: {missing_folders}")
        logger.warning("CDN will start but these folders will return 404 errors")
    
    logger.info(f"Starting CDN server on {HOST}:{PORT}")
    logger.info(f"Base directory: {BASE_DIR}")
    logger.info(f"Available folders: {list(FOLDERS.keys())}")
    
    # IMPORTANT: This script should ONLY be run via Gunicorn (managed by PM2)
    # Do NOT run this directly - use: gunicorn --bind 0.0.0.0:8081 cdn_server:app
    import os
    if os.environ.get('GUNICORN_CMD_ARGS') or 'gunicorn' in os.environ.get('_', ''):
        # Running under Gunicorn - don't start Flask dev server
        logger.info("Running under Gunicorn - Flask app ready")
    else:
        # Only allow direct execution if explicitly needed (not recommended for production)
        logger.warning("WARNING: Running Flask development server directly. Use Gunicorn for production!")
        app.run(host=HOST, port=PORT, debug=False, threaded=True) 