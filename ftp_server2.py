import socket
import threading

HOST, PORT = "127.0.0.1", 2121

def handle_session(conn, addr):
    state = "CONNECTED"
    user_count = 0 

    try:
        # Initial Banner
        conn.sendall(b"220 Service Ready\r\n")
        
        while True:
            data = conn.recv(1024)
            if not data: break
            
            try:
                msg = data.decode().strip().split()
                if not msg: continue
                command = msg[0].upper()
            except: continue

            # Global QUIT command
            if command == "QUIT":
                conn.sendall(b"221 Goodbye\r\n")
                break

            # State Machine Logic
            if state == "CONNECTED":
                if command == "USER":
                    user_count += 1
                    if user_count < 2:
                        conn.sendall(b"331 More info needed\r\n")
                    else:
                        conn.sendall(b"331 Password required\r\n")
                        state = "WAIT_PASS"
                else:
                    conn.sendall(b"530 Please login with USER\r\n")

            elif state == "WAIT_PASS":
                if command == "PASS":
                    conn.sendall(b"230 Logged in\r\n")
                    state = "AUTH"
                else:
                    conn.sendall(b"503 Need PASS now\r\n")

            elif state == "AUTH":
                if command == "LIST":
                    conn.sendall(b"226 Listing done\r\n")
                else:
                    conn.sendall(b"502 Not implemented\r\n")
                    
    except Exception:
        pass
    finally:
        conn.close()

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen(5)
    print(f"FTP Server running on {PORT}...")
    while True:
        conn, addr = server.accept()
        threading.Thread(target=handle_session, args=(conn, addr), daemon=True).start()

if __name__ == "__main__":
    start_server()