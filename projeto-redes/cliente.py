import socket
import threading
import time
import json
import psutil
import platform
import uuid
from pynput.keyboard import Controller, Key
from pynput.mouse import Controller as MouseController, Button


BROADCAST_PORT = 50000
TCP_PORT = 50010   # Porta TCP do cliente
BROADCAST_ADDR = "255.255.255.255"
HELLO_INTERVAL = 5   # segundos


#NO CLIENTE.py
# ==========================================================
# COLETA DE INVENTÁRIO
# ==========================================================
def coletar_dados():

    cpu_cores = psutil.cpu_count(logical=True)

    ram_livre = psutil.virtual_memory().available / (1024**3)

    disco_livre = psutil.disk_usage('/').free / (1024**3)

    interfaces_info = []

    addrs = psutil.net_if_addrs()
    stats = psutil.net_if_stats()

    for nome, enderecos in addrs.items():
        for addr in enderecos:
            if addr.family == socket.AF_INET:
                interfaces_info.append({
                    "interface": nome,
                    "ip": addr.address,
                    "status": "UP" if stats[nome].isup else "DOWN",
                    "tipo": identificar_tipo(nome)
                })

    so = platform.system() + " " + platform.release()

    return {
        "cpu_cores": cpu_cores,
        "ram_livre_gb": round(ram_livre, 2),
        "disco_livre_gb": round(disco_livre, 2),
        "interfaces": interfaces_info,
        "sistema_operacional": so
    }


def identificar_tipo(nome):
    nome = nome.lower()

    if "loopback" in nome or nome == "lo":
        return "loopback"
    if "wi" in nome or "wlan" in nome:
        return "wifi"
    return "ethernet"


# ==========================================================
# MAC ADDRESS
# ==========================================================
def get_mac():
    mac = uuid.getnode()
    mac = ':'.join(f"{(mac >> ele) & 0xff:02x}" for ele in range(40, -1, -8))
    return mac


# ==========================================================
# SERVIDOR TCP DO CLIENTE
# ==========================================================
def tcp_server():

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("", TCP_PORT))
    s.listen()

    print(f"[Cliente] Servidor TCP ouvindo na porta {TCP_PORT}")

    while True:
        conn, addr = s.accept()
        cmd = conn.recv(1024).decode()

        if cmd == "GET_MAC":
            mac = get_mac()
            conn.send(f"MAC_ADDRESS;{mac}".encode())

        elif cmd == "GET_INVENTORY":
            inventario = coletar_dados()
            conn.send(json.dumps(inventario).encode())

        conn.close()


# ==========================================================
# BROADCAST DISCOVERY
# ==========================================================
def broadcast_loop():

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    while True:
        msg = f"DISCOVER_REQUEST;TCP_PORT={TCP_PORT}"
        sock.sendto(msg.encode(), ("255.255.255.255", BROADCAST_PORT))

        time.sleep(10)


#===============
def enviar_hello():

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    while True:

        msg = f"HELLO;PORT={TCP_PORT}"

        sock.sendto(msg.encode(), (BROADCAST_ADDR, BROADCAST_PORT))

        print("[HELLO ( from the other side) enviado ao servidor]")

        time.sleep(HELLO_INTERVAL)

#===========================

# --------------------------------------------------------
    # Handle do TCP
    # --------------------------------------------------------
    def handle_tcp_connection(self, conn, addr):
        keyboard_ctl = Controller()
        keyboard_active = False

        mouse_ctl = MouseController()
        mouse_active = False

        buffer = ""
        while True:
            try:
                data = conn.recv(1024)
                if not data:
                    break
                buffer += data.decode()
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    line = line.strip()
                    if not line:
                        continue

                    # ---------- MAC ----------
                    if line == "GET_MAC":
                        conn.send(f"MAC_ADDRESS;{self.mac}\n".encode())
                        continue

                    # ---------- CONEXÃO DO TECLADO ----------
                    if line == "KEYBOARD_START":
                        keyboard_active = True
                        continue
                    if line == "KEYBOARD_STOP":
                        keyboard_active = False
                        continue
                    
                    # ---------- CONEXÃO DO MOUSE ----------

                    if line == "MOUSE_START":
                        mouse_active = True
                        continue

                    if line == "MOUSE_STOP":
                        mouse_active = False
                        continue

                    if line == "SESSION_END":
                        keyboard_active = False
                        mouse_active = False
                        conn.close()
                        return

                    if keyboard_active and line.startswith("KEY;"):
                        try:
                            _, action, key = line.split(";", 2)
                            if key.startswith("Key."):
                                try:
                                    k = getattr(Key, key.replace("Key.", ""))
                                except AttributeError:
                                    continue  # tecla especial desconhecida
                            else:
                                k = key

                            if action == "DOWN":
                                keyboard_ctl.press(k)
                            elif action == "UP":
                                keyboard_ctl.release(k)
                        except Exception as e:
                            print("Erro ao processar tecla:", e)

                    if mouse_active and line.startswith("MOUSE;"):
                        try:
                            parts = line.split(";")

                            if parts[1] == "MOVE":
                                dx = int(parts[2])
                                dy = int(parts[3])
                                mouse_ctl.move(dx, dy)

                            elif parts[1] == "CLICK":
                                btn = Button.left if parts[2] == "left" else Button.right
                                if parts[3] == "DOWN":
                                    mouse_ctl.press(btn)
                                else:
                                    mouse_ctl.release(btn)

                            elif parts[1] == "SCROLL":
                                dx = int(parts[2])
                                dy = int(parts[3])
                                mouse_ctl.scroll(dx, dy)

                        except Exception as e:
                            print("Erro mouse:", e)

            except Exception as k:
                print(f"[TCP] Erro na conexão {addr}: {k}")
                break

        conn.close()
        print(f"[TCP] Conexão encerrada {addr}")


# ==========================================================
# MAIN
# ==========================================================
if __name__ == "__main__":

    threading.Thread(target=tcp_server, daemon=True).start()

    threading.Thread(target=broadcast_loop, daemon=True).start()

    threading.Thread(target=enviar_hello, daemon=True).start()

    while True:
        time.sleep(1)
