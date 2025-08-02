#!/usr/bin/env python3
"""
Simple HTTP server to serve the Funded Folk Chatbot website
"""

import http.server
import socketserver
import os
import webbrowser
from pathlib import Path

PORT = 3000

class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        # Add CORS headers for development
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

def main():
    # Change to the directory containing this script
    os.chdir(Path(__file__).parent)
    
    # Check if required files exist
    required_files = ['index.html', 'styles.css', 'chatbot.js']
    missing_files = [f for f in required_files if not os.path.exists(f)]
    
    if missing_files:
        print(f"❌ Missing required files: {missing_files}")
        print("Please make sure all files are in the same directory.")
        return
    
    print("🚀 Starting Funded Folk Chatbot Website Server")
    print("=" * 50)
    print(f"📁 Serving files from: {os.getcwd()}")
    print(f"🌐 Website URL: http://localhost:{PORT}")
    print(f"🔗 API Server: http://localhost:8000")
    print()
    print("📋 Files being served:")
    for file in required_files:
        print(f"   ✅ {file}")
    print()
    print("💡 Make sure your API server is running:")
    print("   python api_server.py")
    print()
    print("🎯 Opening website in browser...")
    
    # Open browser
    try:
        webbrowser.open(f'http://localhost:{PORT}')
    except:
        print("⚠️  Could not open browser automatically.")
        print(f"   Please open: http://localhost:{PORT}")
    
    print()
    print("🛑 Press Ctrl+C to stop the server")
    print("=" * 50)
    
    # Start server
    with socketserver.TCPServer(("", PORT), CustomHTTPRequestHandler) as httpd:
        print(f"✅ Server started on port {PORT}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n🛑 Server stopped by user")
            httpd.shutdown()

if __name__ == "__main__":
    main() 