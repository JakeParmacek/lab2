from flask import Flask
from flask import render_template
from flask import request, jsonify
import socket
import threading
import json
import time
import random

def greet(name):
    return "Hi " + name + " . Python server sends its regards."

def process_movement_command(command):
    """Process movement command and return velocity information"""
    # Simulate velocity based on movement command
    velocity = {"x": 0, "y": 0, "z": 0}
    status = "Command received"
    
    if command.lower() == "forward":
        velocity = {"x": 0, "y": 1.0, "z": 0}
        status = "Moving forward"
    elif command.lower() == "backward":
        velocity = {"x": 0, "y": -1.0, "z": 0}
        status = "Moving backward"
    elif command.lower() == "left":
        velocity = {"x": -1.0, "y": 0, "z": 0}
        status = "Turning left"
    elif command.lower() == "right":
        velocity = {"x": 1.0, "y": 0, "z": 0}
        status = "Turning right"
    elif command.lower() == "stop":
        velocity = {"x": 0, "y": 0, "z": 0}
        status = "Stopped"
    else:
        status = f"Unknown command: {command}"
    
    # Add some random variation to simulate real sensor data
    velocity["x"] += random.uniform(-0.1, 0.1)
    velocity["y"] += random.uniform(-0.1, 0.1)
    velocity["z"] += random.uniform(-0.1, 0.1)
    
    return {
        "status": status,
        "velocity": velocity,
        "timestamp": time.time()
    }

def handle_client_connection(client_socket, client_address):
    """Handle individual client connections"""
    print(f"Connection from {client_address}")
    
    try:
        while True:
            # Receive data from client
            data = client_socket.recv(1024)
            if not data:
                break
                
            command = data.decode().strip()
            print(f"Received command: {command}")
            
            # Process the movement command
            response = process_movement_command(command)
            
            # Send response back to client
            response_json = json.dumps(response)
            client_socket.send(response_json.encode())
            
            # For single command mode, break after one command
            break
            
    except Exception as e:
        print(f"Error handling client {client_address}: {e}")
    finally:
        client_socket.close()
        print(f"Connection with {client_address} closed")

def start_socket_server():
    """Start the socket server for movement commands"""
    HOST = "192.168.88.204"  # IP address of your Raspberry PI
    PORT = 65432
    
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((HOST, PORT))
    server_socket.listen(5)
    
    print(f"Socket server listening on {HOST}:{PORT}")
    
    try:
        while True:
            client_socket, client_address = server_socket.accept()
            # Handle each client in a separate thread
            client_thread = threading.Thread(
                target=handle_client_connection, 
                args=(client_socket, client_address)
            )
            client_thread.daemon = True
            client_thread.start()
    except KeyboardInterrupt:
        print("Shutting down socket server...")
    finally:
        server_socket.close()

app = Flask(__name__)
greeting = " "

@app.route('/', methods=["GET", "POST"])
def index():
    global greeting

    # receive message from electron app
    if request.method == "POST":
        json_message = request.get_json()
        print(json_message)
        greeting = greet(json_message)
        return jsonify(server_greet = greeting)        

    # return 'Iot is fun!'
    return jsonify(server_greet = greeting)

if __name__ == '__main__':
    # Start socket server in a separate thread
    socket_thread = threading.Thread(target=start_socket_server)
    socket_thread.daemon = True
    socket_thread.start()
    
    # Start Flask app
    app.run(host='192.168.88.52', port=5000, debug=True)
