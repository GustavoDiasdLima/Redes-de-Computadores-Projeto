import socket
import threading
import time
import json
import psutil
import platform
import uuid

BROADCAST_PORT = 50000
TCP_PORT = 50010   # Porta TCP do cliente


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


# ==========================================================
# MAIN
# ==========================================================
if __name__ == "__main__":

    threading.Thread(target=tcp_server, daemon=True).start()

    broadcast_loop()
