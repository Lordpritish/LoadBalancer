import SimpleHTTPServer
import SocketServer

class MyServer(SimpleHTTPServer.SimpleHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write("This is server response from: " + self.headers['Host'])

def run(handler_class=MyServer, port=80):
    server_address = ('', port)
    httpd = SocketServer.TCPServer(server_address, handler_class)
    print 'Starting httpd on port', port, '...'
    httpd.serve_forever()

if __name__ == '__main__':
    run()