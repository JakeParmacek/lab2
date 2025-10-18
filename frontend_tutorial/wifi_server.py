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
        
        # Distance tracking
        self.total_distance = 0.0
        self.distance_x = 0.0
        self.distance_y = 0.0
        self.last_update_time = time.time()
        self.is_moving = False
        
    def process_movement_command(self, command):
        """Process movement command using PiCar-X library"""
        try:
            command = command.lower().strip()
            current_time = time.time()
            
            # Update distance before processing new command
            self._update_distance(current_time)
            
            if command == "forward":
                self.px.forward(50)  # Move forward at 50% speed
                self.current_direction = "forward"
                self.current_speed = 50
                self.is_moving = True
                status = "Moving forward"
                
            elif command == "backward":
                self.px.backward(50)  # Move backward at 50% speed
                self.current_direction = "backward"
                self.current_speed = 50
                self.is_moving = True
                status = "Moving backward"
                
            elif command == "left":
                self.px.set_dir_servo_angle(-30)  # Turn left 30 degrees
                self.px.forward(50)  # Continue moving forward
                self.current_direction = "left"
                self.current_speed = 50
                self.is_moving = True
                status = "Turning left"
                
            elif command == "right":
                self.px.set_dir_servo_angle(30)  # Turn right 30 degrees
                self.px.forward(50)  # Continue moving forward
                self.current_direction = "right"
                self.current_speed = 50
                self.is_moving = True
                status = "Turning right"
                
            elif command == "stop":
                self.px.stop()  # Stop the car
                self.px.set_dir_servo_angle(0)  # Reset steering to center
                self.current_direction = "stop"
                self.current_speed = 0
                self.is_moving = False
                status = "Stopped"
                
            elif command == "reset_distance":
                # Reset distance tracking
                self.total_distance = 0.0
                self.distance_x = 0.0
                self.distance_y = 0.0
                status = "Distance reset"
                
            else:
                status = f"Unknown command: {command}"
                return {
                    "status": status,
                    "distance": self.get_distance_info(),
                    "direction": self.current_direction,
                    "speed": self.current_speed,
                    "timestamp": time.time()
                }
            
            # Get current distance information
            distance = self.get_distance_info()
            
            return {
                "status": status,
                "distance": distance,
                "direction": self.current_direction,
                "speed": self.current_speed,
                "timestamp": time.time()
            }
            
        except Exception as e:
            print(f"Error processing movement command: {e}")
            return {
                "status": f"Error: {str(e)}",
                "distance": self.get_distance_info(),
                "direction": "error",
                "speed": 0,
                "timestamp": time.time()
            }
    
    def _update_distance(self, current_time):
        """Update distance traveled based on movement"""
        if self.is_moving and self.current_speed > 0:
            dt = current_time - self.last_update_time
            if dt > 0:
                # Calculate distance based on speed and time
                # Speed is in percentage (0-100), convert to meters per second
                speed_ms = (self.current_speed / 100.0) * 0.5  # Adjust multiplier based on your car
                distance_increment = speed_ms * dt
                
                # Update distance based on direction
                if self.current_direction == "forward":
                    self.distance_y += distance_increment
                elif self.current_direction == "backward":
                    self.distance_y -= distance_increment
                elif self.current_direction == "left":
                    self.distance_x -= distance_increment * 0.5  # Diagonal movement
                    self.distance_y += distance_increment * 0.5
                elif self.current_direction == "right":
                    self.distance_x += distance_increment * 0.5  # Diagonal movement
                    self.distance_y += distance_increment * 0.5
                
                # Update total distance
                self.total_distance += distance_increment
        
        self.last_update_time = current_time
    
    def get_distance_info(self):
        """Get current distance traveled information"""
        try:
            return {
                "total": round(self.total_distance, 3),
                "x": round(self.distance_x, 3),
                "y": round(self.distance_y, 3),
                "units": "meters"
            }
        except Exception as e:
            print(f"Error getting distance info: {e}")
            return {
                "total": 0.0,
                "x": 0.0,
                "y": 0.0,
                "units": "meters"
            }
    
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