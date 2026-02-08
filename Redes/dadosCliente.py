#Funcionalidade 2.1
import psutil
import platform
import socket

class dadosCliente:

    def __init__(self):
        self.sistema = platform.system() + " " + platform.release() 


    def tipo_interface(self, nome): 
        nome = nome.lower() 
        if "loopback" in nome or "lo" == nome:
            return "Loopback"
        elif "wifi" in nome or "wlan" in nome or "wireless" in nome or "wi-fi" in nome:
            return "Wi-Fi"
        elif "eth" in nome or "en" in nome or "ethernet" in nome:
            return "Ethernet"
        return "Desconhecido"


    def coletarDados(self): #coleta os dados do cliente

        cpu = { 
            "fisico" : psutil.cpu_count(logical=False),
            "logico" : psutil.cpu_count(logical=True),
            "uso" : psutil.cpu_percent(1)
        }

        ram = { 
            "total" : round(psutil.virtual_memory().total/1024**3, 2),
            "livre" : round(psutil.virtual_memory().available/1024**3, 2)
        }

        hd = { 
            "total" : round(psutil.disk_usage('/').total/1024**3, 2),
            "livre" : round(psutil.disk_usage('/').free/1024**3, 2)
        }

        info_interface = []
        endereco = psutil.net_if_addrs() # Vai pegar os ips da interface da rede do cliente
        status = psutil.net_if_stats() # Vai pega o status da interface da rede do cliente

        for nome_interface, enderecos_interface in endereco.items(): 

            ip_v4 = "" 
            ip_v6 = "" 
            mac = "" 

            for addr in enderecos_interface: 
                if addr.family == socket.AF_INET:
                    ip_v4 = addr.address
                elif addr.family == socket.AF_INET6:
                    ip_v6 = addr.address
                elif addr.family == psutil.AF_LINK:
                    mac = addr.address

            if nome_interface in status: 
                up_ou_down = status[nome_interface].isup
            else: 
                up_ou_down = False

            status_string = "UP" if up_ou_down else "DOWN" 
            tipo_interface= self.tipo_interface(nome_interface) 

          
            info_interface.append({
                "nome_interface" : nome_interface,
                "ipv4" : ip_v4,
                "ipv6" : ip_v6,
                "mac" : mac,
                "status_interface": status_string,
                "tipo_interface" : tipo_interface
            })

        return{ # Retorna para quem chamou a função dicionários com os dados do sistema
            "so" : self.sistema,
            "processador" : cpu,
            "memoria" : ram,
            "disco" : hd,
            "rede" : info_interface
        }