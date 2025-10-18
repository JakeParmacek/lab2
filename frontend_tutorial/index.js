var server_port = 65432;
var server_addr = "192.168.88.204";   // the IP address of your Raspberry PI

function sendMovementCommand(command) {
    // Update the current command display
    document.getElementById("current_command").innerHTML = command;
    document.getElementById("server_response").innerHTML = "Sending command...";
    
    const net = require('net');
    
    const client = net.createConnection({ port: server_port, host: server_addr }, () => {
        console.log('Connected to server!');
        // Send the movement command
        client.write(`${command}\r\n`);
    });
    
    // Handle data from the server
    client.on('data', (data) => {
        const response = data.toString().trim();
        console.log('Server response:', response);
        
        // Parse the response to extract velocity information
        try {
            const responseData = JSON.parse(response);
            if (responseData.velocity) {
                document.getElementById("velocity_info").innerHTML = 
                    `X: ${responseData.velocity.x || 0}, Y: ${responseData.velocity.y || 0}, Z: ${responseData.velocity.z || 0}`;
            }
            if (responseData.status) {
                document.getElementById("server_response").innerHTML = responseData.status;
            }
        } catch (e) {
            // If not JSON, display as plain text
            document.getElementById("server_response").innerHTML = response;
        }
        
        client.end();
        client.destroy();
    });

    client.on('error', (err) => {
        console.error('Connection error:', err);
        document.getElementById("server_response").innerHTML = "Connection failed: " + err.message;
    });

    client.on('end', () => {
        console.log('Disconnected from server');
    });
}

// Legacy function for backward compatibility
function client(){
    const net = require('net');
    var input = document.getElementById("myName").value;

    const client = net.createConnection({ port: server_port, host: server_addr }, () => {
        console.log('connected to server!');
        client.write(`${input}\r\n`);
    });
    
    client.on('data', (data) => {
        document.getElementById("greet_from_server").innerHTML = data;
        console.log(data.toString());
        client.end();
        client.destroy();
    });

    client.on('end', () => {
        console.log('disconnected from server');
    });
}

function greeting(){
    var name = document.getElementById("myName").value;
    document.getElementById("greet").innerHTML = "Hello " + name + " !";
    client();
}
