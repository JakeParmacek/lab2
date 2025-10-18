import socket
import json
import time
import threading
from picarx import Picarx

class PiCarXServer:
    def __init__(self, host="192.168.88.204", port=65432):
        self.host = host
        self.port = port
        self.px = Picarx()
        self.current_speed = 0
        self.current_direction = "stop"
        
    def process_movement_command(self, command):
        """Process movement command using PiCar-X library"""
        try:
            command = command.lower().strip()
            
            if command == "forward":
                self.px.forward(50)  # Move forward at 50% speed
                self.current_direction = "forward"
                self.current_speed = 50
                status = "Moving forward"
                
            elif command == "backward":
                self.px.backward(50)  # Move backward at 50% speed
                self.current_direction = "backward"
                self.current_speed = 50
                status = "Moving backward"
                
            elif command == "left":
                self.px.set_dir_servo_angle(-30)  # Turn left 30 degrees
                self.px.forward(50)  # Continue moving forward
                self.current_direction = "left"
                self.current_speed = 50
                status = "Turning left"
                
            elif command == "right":
                self.px.set_dir_servo_angle(30)  # Turn right 30 degrees
                self.px.forward(50)  # Continue moving forward
                self.current_direction = "right"
                self.current_speed = 50
                status = "Turning right"
                
            elif command == "stop":
                self.px.stop()  # Stop the car
                self.px.set_dir_servo_angle(0)  # Reset steering to center
                self.current_direction = "stop"
                self.current_speed = 0
                status = "Stopped"
                
            else:
                status = f"Unknown command: {command}"
                return {
                    "status": status,
                    "velocity": {"x": 0, "y": 0, "z": 0},
                    "direction": self.current_direction,
                    "speed": self.current_speed,
                    "timestamp": time.time()
                }
            
            # Get current velocity information
            velocity = self.get_velocity_info()
            
            return {
                "status": status,
                "velocity": velocity,
                "direction": self.current_direction,
                "speed": self.current_speed,
                "timestamp": time.time()
            }
            
        except Exception as e:
            print(f"Error processing movement command: {e}")
            return {
                "status": f"Error: {str(e)}",
                "velocity": {"x": 0, "y": 0, "z": 0},
                "direction": "error",
                "speed": 0,
                "timestamp": time.time()
            }
    
    def get_velocity_info(self):
        """Get current velocity information from PiCar-X"""
        try:
            # Get speed from PiCar-X (if available)
            speed = self.px.get_speed() if hasattr(self.px, 'get_speed') else self.current_speed
            
            # Calculate velocity components based on direction
            if self.current_direction == "forward":
                return {"x": 0, "y": speed, "z": 0}
            elif self.current_direction == "backward":
                return {"x": 0, "y": -speed, "z": 0}
            elif self.current_direction == "left":
                return {"x": -speed * 0.5, "y": speed * 0.5, "z": 0}  # Diagonal movement
            elif self.current_direction == "right":
                return {"x": speed * 0.5, "y": speed * 0.5, "z": 0}  # Diagonal movement
            else:
                return {"x": 0, "y": 0, "z": 0}
                
        except Exception as e:
            print(f"Error getting velocity info: {e}")
            return {"x": 0, "y": 0, "z": 0}
    
    def handle_client_connection(self, client_socket, client_address):
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
                response = self.process_movement_command(command)
                
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
    
    def start_server(self):
        """Start the server"""
        print(f"Starting PiCar-X server on {self.host}:{self.port}")
        
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((self.host, self.port))
            s.listen(5)
            
            print(f"PiCar-X server listening on {self.host}:{self.port}")
            
            try:
                while True:
                    client_socket, client_address = s.accept()
                    # Handle each client in a separate thread
                    client_thread = threading.Thread(
                        target=self.handle_client_connection,
                        args=(client_socket, client_address)
                    )
                    client_thread.daemon = True
                    client_thread.start()
                    
            except KeyboardInterrupt:
                print("Shutting down PiCar-X server...")
                self.px.stop()  # Ensure car stops when server shuts down
            except Exception as e:
                print(f"Server error: {e}")
            finally:
                s.close()

if __name__ == "__main__":
    # Initialize and start the PiCar-X server
    server = PiCarXServer()
    server.start_server()    