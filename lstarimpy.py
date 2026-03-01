from pyftpdlib.authorizers import DummyAuthorizer
from pyftpdlib.handlers import FTPHandler
from pyftpdlib.servers import FTPServer

def start_ftp_server():
    # Create user manager
    authorizer = DummyAuthorizer()

    # Add a user: username, password, home directory, permissions
    authorizer.add_user(
        "user", 
        "12345", 
        ".",                # current directory as FTP root
        perm="elradfmw"     # full permissions
    )

    # Add anonymous user (optional)
    # authorizer.add_anonymous(".", perm="elr")

    # Create FTP handler
    handler = FTPHandler
    handler.authorizer = authorizer

    # Server address
    address = ("127.0.0.1", 2121)

    # Create server
    server = FTPServer(address, handler)

    print("FTP Server running on port 2121...")
    server.serve_forever()

if __name__ == "__main__":
    start_ftp_server()