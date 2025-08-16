#!/usr/bin/env python3
import asyncio
import json
import logging
import os
import signal
import sys
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
from threading import Thread
from urllib.parse import urlparse
import websockets

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from web.server import start_server

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RoundtableHTTPHandler(SimpleHTTPRequestHandler):
    """Custom HTTP handler that serves files from the web directory"""
    
    def __init__(self, *args, **kwargs):
        # Set the directory to serve files from
        super().__init__(*args, directory=str(Path(__file__).parent / 'web'), **kwargs)
    
    def end_headers(self):
        # Add CORS headers for development
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()
    
    def do_GET(self):
        """Handle GET requests"""
        parsed_path = urlparse(self.path)
        
        # Serve index.html for root path
        if parsed_path.path == '/' or parsed_path.path == '':
            self.path = '/index.html'
        
        return super().do_GET()

def run_http_server(port=8080):
    """Run the HTTP server to serve static files"""
    try:
        httpd = HTTPServer(('localhost', port), RoundtableHTTPHandler)
        logger.info(f"HTTP server running on http://localhost:{port}")
        httpd.serve_forever()
    except Exception as e:
        logger.error(f"HTTP server error: {e}")

async def run_websocket_server(port=8000):
    """Run the WebSocket server"""
    try:
        server = await start_server('localhost', port)
        await server.wait_closed()
    except Exception as e:
        logger.error(f"WebSocket server error: {e}")

async def main():
    """Main function to run both servers"""
    print("\n" + "="*80)
    print("🌐 ROUNDTABLE WEB INTERFACE")
    print("="*80)
    print()
    print("Starting Roundtable web interface...")
    print()
    
    # Start HTTP server in a separate thread
    http_thread = Thread(target=run_http_server, args=(8080,), daemon=True)
    http_thread.start()
    
    print(f"✓ HTTP Server: http://localhost:8080")
    print(f"✓ WebSocket Server: ws://localhost:8000/ws")
    print()
    print("🌐 Open http://localhost:8080 in your browser to access the terminal interface")
    print()
    print("Press Ctrl+C to stop the servers")
    print("="*80)
    print()
    
    # Handle graceful shutdown
    def signal_handler(signum, frame):
        logger.info("\nShutting down servers...")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Run WebSocket server
    try:
        await run_websocket_server(8000)
    except KeyboardInterrupt:
        logger.info("Servers stopped by user")

if __name__ == "__main__":
    asyncio.run(main())