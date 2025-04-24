from http.server import BaseHTTPRequestHandler, HTTPServer
import threading
import json
from consumer import MLConsumer
import logging

logger = logging.getLogger('ml-consumer-server')

class ConsumerServer(BaseHTTPRequestHandler):
    consumer = None

    def send_json_response(self, data, status=200):
        """Helper method to send JSON responses"""
        self.send_response(status)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        # Use json.dumps to ensure proper JSON formatting with double quotes
        response = json.dumps(data, ensure_ascii=False)
        self.wfile.write(response.encode('utf-8'))

    def do_GET(self):
        """Handle GET requests - return health status"""
        if self.path == '/health' or self.path == '/':
            health_data = {
                "service": "ml-consumer",
                "status": "healthy",
                **(self.consumer.health_status if self.consumer else {"status": "not_running"})
            }
            self.send_json_response(health_data)
        else:
            self.send_json_response({"error": "Not found"}, status=404)

def run_server(port=8080):
    """Run the HTTP server"""
    server_address = ('', port)
    httpd = HTTPServer(server_address, ConsumerServer)
    logger.info(f"Starting server on port {port}")
    return httpd

def main():
    # Initialize consumer
    consumer = MLConsumer()
    ConsumerServer.consumer = consumer
    
    # Start consumer in a separate thread
    consumer_thread = threading.Thread(target=consumer.run)
    consumer_thread.daemon = True
    consumer_thread.start()
    
    # Start HTTP server
    try:
        server = run_server()
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Shutting down server...")
        server.shutdown()
        consumer.running = False
        consumer_thread.join()
        logger.info("Server and consumer stopped")

if __name__ == "__main__":
    main()
