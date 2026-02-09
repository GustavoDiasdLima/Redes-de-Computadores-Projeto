import socket
import threading
import random
import time
import uuid
import psutil
import json
from pynput.keyboard import Controller, Key
from pynput.mouse import Controller as MouseController, Button
import platform

BROADCAST_PORT = 50000
BROADCAST_ADDR = "<broadcast>"
BROADCAST_DELAY = 5


class Client:
    def __init__(self):
        self.tcp_port = random.randint(20000, 40000)
        self.running = True
        self.mac = self.get_local_mac()

    def get_local_mac(self):
        mac_int = uuid.getnode()
        return ":".join(f"{(mac_int >> 8*i) & 0xff:02x}" for i in reversed(range(6)))

    # -----------------------------------------------------------
    # UDP: broadcast de descoberta
    # -----------------------------------------------------------
    def send_broadcast(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        while self.running:
            msg = f"DISCOVER_REQUEST;PORT={self.tcp_port}"
            sock.sendto(msg.encode(), (BROADCAST_ADDR, BROADCAST_PORT))
            time.sleep(BROADCAST_DELAY)

    # -----------------------------------------------------------
    # TCP: servidor interno para responder comandos
    # -----------------------------------------------------------
    def tcp_server(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(("", self.tcp_port))
        sock.listen(5)
        print(f"[Querido e gentil cliente] Servidor TCP escutando na portinha {self.tcp_port}...")

        while self.running:
            conn, addr = sock.accept()
            threading.Thread(
                target=self.handle_tcp_connection,
                args=(conn, addr),
                daemon=True
            ).start()

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

                    # ---------- INVENTÁRIO ----------
                    if line == "GET_INVENTORY":
                        inventario = self.coletar_dados()
                        payload = json.dumps(inventario)
                        conn.send(f"INVENTORY;{payload}\n".encode())
                        continue

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
                            print("ERROOOO ao processar tecla:", e)

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
                            print("ERRO mouse:", e)

            except Exception as k:
                print(f"[TCP] ERRO na conexão :( ) {addr}: {k}")
                break

        conn.close()
        print(f"[TCP] Conexão encerrada!! {addr}")

    #NO CLIENTE.py
    # ==========================================================
    # COLETA DE INVENTÁRIO
    # ==========================================================
    

    def coletar_dados(self):
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
                        "tipo": self.identificar_tipo(nome)
                    })

        so = platform.system() + " " + platform.release()

        return {
            "cpu_cores": cpu_cores,
            "ram_livre_gb": round(ram_livre, 2),
            "disco_livre_gb": round(disco_livre, 2),
            "interfaces": interfaces_info,
            "sistema_operacional": so
        }


    def identificar_tipo(self, nome):
        nome = nome.lower()
        if "loopback" in nome or nome == "lo":
            return "loopback"
        if "wi" in nome or "wlan" in nome:
            return "wifi"
        return "ethernet"

    # --------------------------------------------------------
    # Main
    # --------------------------------------------------------
    def start(self):
        threading.Thread(target=self.send_broadcast, daemon=True).start()
        threading.Thread(target=self.tcp_server, daemon=True).start()
        print(f"[Cliente] TCP_PORT={self.tcp_port} | MAC={self.mac}")
        while self.running:
            time.sleep(5)


if __name__ == "__main__":
    Client().start()