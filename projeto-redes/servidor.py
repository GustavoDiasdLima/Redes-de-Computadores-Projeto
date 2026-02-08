import socket
import threading
import time
import json
import csv

BROADCAST_PORT = 50000


class ClientInfo:
    def __init__(self, ip, tcp_port):
        self.ip = ip
        self.tcp_port = tcp_port
        self.last_seen = time.time()
        self.last_msg = ""
        self.mac = None
        self.inventory = {}

    def update(self, msg):
        self.last_msg = msg
        self.last_seen = time.time()

    def status(self):
        return "ONLINE" if time.time() - self.last_seen <= 30 else "OFFLINE"

    def __repr__(self):
        return f"{self.ip}:{self.tcp_port} | {self.status()}"


class DiscoveryServer:
    def __init__(self):
        self.clients = {}
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(("", BROADCAST_PORT))

    # ======================================================
    # DISCOVERY
    # ======================================================
    def listen_broadcasts(self):

        print(f"[Servidor] Ouvindo broadcasts {BROADCAST_PORT}")

        while True:
            data, addr = self.sock.recvfrom(1024)
            msg = data.decode()
            ip = addr[0]

            if msg.startswith("DISCOVER_REQUEST"):
                tcp_port = int(msg.split("=")[1])
                key = (ip, tcp_port)

                if key not in self.clients:
                    self.clients[key] = ClientInfo(ip, tcp_port)
                    print(f"[Novo cliente] {ip}:{tcp_port}")

                self.clients[key].update(msg)

    # ======================================================
    # TCP REQUESTS
    # ======================================================
    def tcp_request(self, key, command):

        ip, port = key

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((ip, port))

            sock.send(command.encode())
            response = sock.recv(4096).decode()
            sock.close()

            return response

        except Exception as e:
            print(f"Erro TCP {ip}: {e}")
            return None

    def ask_mac(self, key):

        resp = self.tcp_request(key, "GET_MAC")

        if resp and resp.startswith("MAC_ADDRESS"):
            mac = resp.split(";")[1]
            self.clients[key].mac = mac

    def ask_inventory(self, key):

        resp = self.tcp_request(key, "GET_INVENTORY")

        if resp:
            self.clients[key].inventory = json.loads(resp)

    # ======================================================
    # DASHBOARD
    # ======================================================
    def dashboard(self):

        print("\n=== DASHBOARD ===")

        online = 0
        offline = 0

        for key, c in self.clients.items():

            status = c.status()

            if status == "ONLINE":
                online += 1
            else:
                offline += 1

            so = c.inventory.get("sistema_operacional", "N/A")

            print(f"{c.ip}:{c.tcp_port} | {status} | {so}")

        print(f"\nOnline: {online} | Offline: {offline}")

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

        print("CSV exportado")

    # ======================================================
    # MENU
    # ======================================================
    def menu(self):

        while True:
            print("\n1- Clientes")
            print("2- Dashboard")
            print("3- Coletar inventário")
            print("4- Consolidado")
            print("5- Exportar CSV")
            print("0- Sair")

            op = input("> ")

            match op:

                case "1":
                    for k in self.clients:
                        print(k)

                case "2":
                    self.dashboard()

                case "3":
                    for k in self.clients:
                        self.ask_inventory(k)

                case "4":
                    self.consolidado()

                case "5":
                    self.export_csv()

                case "0":
                    exit()

    def start(self):
        threading.Thread(target=self.listen_broadcasts, daemon=True).start()
        self.menu()


if __name__ == "__main__":
    DiscoveryServer().start()
