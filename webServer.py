import socket
import os
import time
from datetime import datetime
from email.utils import parsedate_to_datetime

#for response to client
def generate_http_response(status_code, body=''):
    """ Generate an HTTP response with given status code and body. """
    reason_phrases = {
        200: 'OK',
        304: 'Not Modified',
        400: 'Bad Request',
        403: 'Forbidden',
        404: 'Not Found',
        411: 'Length Required'
    }

    response_line = f'HTTP/1.1 {status_code} {reason_phrases.get(status_code, "Unknown")}\r\n'
    headers = 'Content-Type: text/html; charset=UTF-8\r\n'
    content_length = f'Content-Length: {len(body)}\r\n'
    return (response_line + headers + content_length + '\r\n' + body).encode()

def handle_request(request):
    #HTTP request from client and parse
    lines = request.splitlines()
    if len(lines) == 0:
        return generate_http_response(400)

    request_line = lines[0].split()
    if len(request_line) < 3:
        return generate_http_response(400)

    method, path, _ = request_line
    if method != 'GET':
        return generate_http_response(400)

    # Check Content-Length 
    
    count = 0
    
    # Check for If-Modified-Since 
    for line in lines:
        if line.startswith("If-Modified-Since:"):
            count = count + 1
            file_mod_time = os.path.getmtime('test.html')
            if_modified_since = parsedate_to_datetime(line.split(": ", 1)[1])
            if file_mod_time <= time.mktime(if_modified_since.timetuple()):
                return generate_http_response(304)
            

    if path in ['/', '/test.html']:
        try:
            with open('test.html', 'r') as file:
                return generate_http_response(200, file.read())
        except FileNotFoundError:
            count = count + 1
            return generate_http_response(404)
        except PermissionError:
            count = count + 1
            return generate_http_response(403)
    else:
        return generate_http_response(404)
    
    
    if "Content-Length:" not in request and count == 0:
        return generate_http_response(411)

def main():
    host = '127.0.0.1'
    port = 8080

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((host, port))
        s.listen()

        print(f'Serving HTTP on {host} port {port}...')

        while True:
            conn, addr = s.accept()
            with conn:
                request = conn.recv(1024).decode('utf-8')
                response = handle_request(request)
                conn.sendall(response)

if __name__ == "__main__":
    main()
