import socket
import threading
import hashlib

# A simple in-memory cache.
# The key is a hash of the request URL, and the value is the response data.
cache = {}

# get_cache_key() generates a unique cache key based on the URL of the request.
def get_cache_key(url):
    return hashlib.sha256(url).hexdigest()

# handle_client handles the client request, each client connection is processed in it
def handle_client(client_socket):
    #Receive the request from the client
    request = client_socket.recv(1024)
    print("[*] Received: ", request)

    # Extract the first line of the request to get the URL
    first_line = request.split(b'\n')[0]
    url = first_line.split(b' ')[1]

    # Generate the cache key for the URL
    cache_key = get_cache_key(url)

    # Check if the response for the URL is in cache
    if cache_key in cache:
        print("[*] Cache hit. Request is in the proxy server")
        client_socket.send(cache[cache_key]) #Cache hit, send the response from the cache to the client
        client_socket.close()
        return

    # If not in cache, process the request
    if cache_key not in cache:
        print("[*] request not in cache, requesting to the original server.")
    
    #Parse the URL to extract the webserver and port
    http_pos = url.find(b"://")
    if http_pos == -1:
        temp = url
    else:
        temp = url[(http_pos+3):]

    port_pos = temp.find(b":")
    webserver_pos = temp.find(b"/")
    if webserver_pos == -1:
        webserver_pos = len(temp)
    webserver = ""
    port = -1
    if port_pos == -1 or webserver_pos < port_pos:
        port = 80
        webserver = temp[:webserver_pos]
    else:
        port = int((temp[(port_pos+1):])[:webserver_pos-port_pos-1])
        webserver = temp[:port_pos]

    try:
        # Create a socket to connect to the web server
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((webserver, port))
        s.sendall(request)

        response_data = b''
        while True:
            # Receive data from the web server
            data = s.recv(4096)
            if len(data) > 0:
                response_data += data
                client_socket.send(data)
            else:
                break
        
        # Store the response in the cache
        cache[cache_key] = response_data

    except socket.error as e:
        print("Runtime Error:", e)
    finally:
        # Close the client socket and server socket
        s.close()
        client_socket.close()

# Starts the proxy server, listens for the incoming connections and spawn a new thread for each connection.
def start_proxy():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(("0.0.0.0", 9999))
    server_socket.listen(5)

    print("Proxy Server Running on port 9999")

    while True:
        #Accept a new connection
        client_socket, addr = server_socket.accept()
        print("Accepted connection from: ", addr)
        
        #Start a new thread to handle the client
        client_handler = threading.Thread(target=handle_client, args=(client_socket,))
        client_handler.start()

if __name__ == "__main__":
    start_proxy()