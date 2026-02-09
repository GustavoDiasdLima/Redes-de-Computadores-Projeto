import socket
import threading
import time
import json
import csv
from pynput import keyboard, mouse

BROADCAST_PORT = 50000


class ClientInfo:
    def __init__(self, ip, tcp_port):
        self.ip = ip
        self.tcp_port = tcp_port
        self.last_seen = time.time()
        self.last_msg = ""
        self.mac = None
        self.inventory = None

    def update(self, msg):
        self.last_msg = msg
        self.last_seen = time.time()

    def __repr__(self):
        age = round(time.time() - self.last_seen, 1)
        return f"{self.ip}:{self.tcp_port} | MAC={self.mac} | UltimaMsg='{self.last_msg}' | {age}s atrás"


class DiscoveryServer:
    def __init__(self):
        self.clients = {}  # chave: (ip, tcp_port)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(("", BROADCAST_PORT))

    # ----------------------------------------------------------------
    # ESCUTA BROADCASTS
    # ----------------------------------------------------------------
    def listen_broadcasts(self):
        print(f"[Magnífico e inderrubável Servidor] Ouvindo broadcasts na portinha {BROADCAST_PORT}...")
        while True:
            data, addr = self.sock.recvfrom(1024)
            msg = data.decode()
            ip = addr[0]

            print(f"[Broadcast de {ip}] {msg}")

            if msg.startswith("DISCOVER_REQUEST"):
                tcp_port = int(msg.split("=")[1])
                key = (ip, tcp_port)

                if key not in self.clients:
                    self.clients[key] = ClientInfo(ip, tcp_port)
                    print(f"[Novo cliente] {ip}:{tcp_port}")

                self.clients[key].update(msg)
                self.sock.sendto("DISCOVER_RESPONSE".encode(), addr)

    # ----------------------------------------------------------------
    # SOLICITA MAC via TCP
    # ----------------------------------------------------------------
    def ask_mac_tcp(self, key):
        if key not in self.clients:
            print("Infelizmente cliente não encontrado :/ !")
            return

        ip, port = key
        print(f"[Servidor] Conectando via TCP em {ip}:{port} ...")
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((ip, port))
            sock.send(b"GET_MAC\n")
            response = sock.recv(1024).decode().strip()
            sock.close()

            if response.startswith("MAC_ADDRESS;"):
                mac = response.split(";")[1]
                self.clients[key].mac = mac
                print(f"[MAC recebido via TCP] {ip}:{port} => {mac}")

        except Exception as e:
            print(f"ERRO ao conectar via TCP: {e}")

    # ----------------------------------------------------------------
    # CONTROLE REMOTO DE TECLADO
    # ----------------------------------------------------------------
    def control_keyboard(self, key):
        if key not in self.clients:
            print("Infelizmente cliente não encontrado :/ !")
            return

        ip, port = key
        print(f"[Servidor] Conectando ao cliente {ip}:{port} para controle de teclado gamer")
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((ip, port))
            sock.send(b"KEYBOARD_START\n")

            def on_press(k):
                try:
                    msg = f"KEY;DOWN;{k.char}\n"
                except AttributeError:
                    msg = f"KEY;DOWN;{k}\n"
                sock.send(msg.encode())

            def on_release(k):
                try:
                    msg = f"KEY;UP;{k.char}\n"
                except AttributeError:
                    msg = f"KEY;UP;{k}\n"
                sock.send(msg.encode())

                if k == keyboard.Key.esc:
                    sock.send(b"KEYBOARD_STOP\n")
                    sock.send(b"SESSION_END\n")
                    return False

            print(">>> Controle de teclado ativo EBAA xD (ESC para sair)")
            listener = keyboard.Listener(on_press=on_press, on_release=on_release)
            listener.start()
            listener.join()

            sock.close()
            print("[Servidor] Sessão de teclado encerrada")

        except Exception as e:
            print(f"ERRO no controle de teclado '0' : {e}")

    # ----------------------------------------------------------
    # Mouse
    # ----------------------------------------------------------

    def control_mousepad(self, key):
        if key not in self.clients:
            print("Infelizmente cliente não encontrado :/ !")
            return

        ip, port = key
        print(f"[Servidor] Conectando ao cliente {ip}:{port} para controle de mouse")

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((ip, port))
            sock.send(b"MOUSE_START\n")

            last_pos = None

            def on_move(x, y):
                nonlocal last_pos
                if last_pos is None:
                    last_pos = (x, y)
                    return
                dx = x - last_pos[0]
                dy = y - last_pos[1]
                last_pos = (x, y)
                sock.send(f"MOUSE;MOVE;{dx};{dy}\n".encode())

            def on_click(x, y, button, pressed):
                # botão do meio encerra sessão
                if button == mouse.Button.middle and pressed:
                    sock.send(b"MOUSE_STOP\n")
                    sock.send(b"SESSION_END\n")
                    return False  # encerra o mouse.Listener

                action = "DOWN" if pressed else "UP"
                sock.send(f"MOUSE;CLICK;{button.name};{action}\n".encode())

            def on_scroll(x, y, dx, dy):
                sock.send(f"MOUSE;SCROLL;{dx};{dy}\n".encode())

            print(">>> Controle de mouse ativo (BOTÃO DO MEIO para sair)")
            with mouse.Listener(
                on_move=on_move,
                on_click=on_click,
                on_scroll=on_scroll
            ) as listener:
                listener.join()

            sock.close()
            print("[Servidor] Sessão de mouse encerrada :/ ")

        except Exception as e:
            print(f"ERRO no controle de mouse ;-; : {e}")
    
    # ======================================================
    # CONSOLIDADO
    # ======================================================
    def consolidado(self):

        total_cpu = total_ram = total_disco = count = 0

        for c in self.clients.values():
            inv = c.inventory
            if inv:
                total_cpu += inv["cpu_cores"]
                total_ram += inv["ram_livre_gb"]
                total_disco += inv["disco_livre_gb"]
                count += 1

        if count == 0:
            print("Sem dados")
            return

        print("\n=== MÉDIAS ===")
        print("CPU:", total_cpu / count)
        print("RAM:", total_ram / count)
        print("Disco:", total_disco / count)

    # ======================================================
    # EXPORTAÇÃO
    # ======================================================
    def export_csv(self):

        with open("relatorio.csv", "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["IP", "CPU", "RAM", "Disco", "SO"])

            for c in self.clients.values():
                inv = c.inventory
                if inv:
                    writer.writerow([
                        c.ip,
                        inv["cpu_cores"],
                        inv["ram_livre_gb"],
                        inv["disco_livre_gb"],
                        inv["sistema_operacional"]
                    ])

        print("CSV exportado! Confira as informações!")

    def ask_inventory_tcp(self, key):
        if key not in self.clients:
            return

        ip, port = key
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((ip, port))
            sock.send(b"GET_INVENTORY\n")

            data = sock.recv(4096).decode().strip()
            sock.close()

            if data.startswith("INVENTORY;"):
                json_data = data.split(";", 1)[1]
                inventory = json.loads(json_data)
                self.clients[key].inventory = inventory
                print(f"[Inventário recebido] {ip}:{port}")

        except Exception as e:
            print("ERRO inventário:", e)



    # ----------------------------------------------------------------
    # MENU INTERATIVO
    # ----------------------------------------------------------------
    def menu(self):
        while True:
            print("\n=== Seja bem-vindo(a) ao MENU do  SERVIDOR ===")
            print("1 - Listar clientes")
            print("2 - Solicitar MAC de um cliente")
            print("3 - Solicitar MAC de todos os clientes")
            print("4 - Controlar teclado de um cliente")
            print("5 - Controlar mouse de um cliente")
            print("6 - Coletar inventário de todos")
            print("7 - Consolidado")
            print("8 - Exportar CSV")
            print("0 - Sair")
            op = input("> ")

            match op:
                case "1":
                    print("\n--- CLIENTES ---")
                    for key, info in self.clients.items():
                        print(f"{key} -> {info}")

                case "2":
                    ip = input("Digite o IP: ")
                    port = int(input("Digite a porta TCP do cliente: "))
                    self.ask_mac_tcp((ip, port))

                case "3":
                    for key in self.clients:
                        self.ask_mac_tcp(key)

                case "4":
                    ip = input("Digite o IP do cliente: ")
                    port = int(input("Digite a porta TCP do cliente: "))
                    self.control_keyboard((ip, port))

                case "5":
                    ip = input("Digite o IP do cliente: ")
                    port = int(input("Digite a porta TCP do cliente: "))
                    self.control_mousepad((ip, port))

                case "6":
                    for key in self.clients:
                        self.ask_inventory_tcp(key)

                case "7":
                    self.consolidado()

                case "8":
                    self.export_csv()


                case "0":
                    print("Saindo...")
                    exit()

                case _:
                    print("Opção inválida!")

    # ----------------------------------------------------------------
    # START
    # ----------------------------------------------------------------
    def start(self):
        threading.Thread(target=self.listen_broadcasts, daemon=True).start()
        self.menu()


if __name__ == "__main__":
    DiscoveryServer().start()