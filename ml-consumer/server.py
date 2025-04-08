from http.server import BaseHTTPRequestHandler, HTTPServer
import threading
from consumer import start_kafka_loop  # Assuming this is the correct import path

latest_prediction = {"status": "waiting for predictions..."}

def update_prediction(p):
    global latest_prediction
    latest_prediction = p

class StatusHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(str(latest_prediction).encode("utf-8"))

def run_http_server():
    print("🚀 HTTP server running on port 8080")
    server = HTTPServer(("", 8080), StatusHandler)
    server.serve_forever()

if __name__ == "__main__":
    print("🚀 server.py is running...")
    # Start Kafka loop in a separate thread and pass `update_prediction` as callback
    threading.Thread(target=lambda: start_kafka_loop(update_prediction), daemon=True).start()
    run_http_server()
