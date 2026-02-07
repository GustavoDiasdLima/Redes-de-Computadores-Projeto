import psutil
import platform
import socket

class dadosCliente:

    def __init__(self):
        self.sistema = platform.system() + " " + platform.release() # Inicializa a variável sistema com uma string contendo o SO do cliente e a versão atual.


    def tipo_interface(self, nome): # Função auxiliar para coletar o tipo de interface de rede
        nome = nome.lower() # converte todas as strings para minúsculo para formatação
        if "loopback" in nome or "lo" == nome:
            return "Loopback"
        elif "wifi" in nome or "wlan" in nome or "wireless" in nome or "wi-fi" in nome:
            return "Wi-Fi"
        elif "eth" in nome or "en" in nome or "ethernet" in nome:
            return "Ethernet"
        return "Desconhecido"


    def coletarDados(self): # Função que coleta os dados do sistema do cliente

        cpu = { # Dicionário contendo informações da CPU
            "fisico" : psutil.cpu_count(logical=False),
            "logico" : psutil.cpu_count(logical=True),
            "uso" : psutil.cpu_percent(1)
        }

        ram = { # Dicionário contendo informações da RAM
            "total" : round(psutil.virtual_memory().total/1024**3, 2),
            "livre" : round(psutil.virtual_memory().available/1024**3, 2)
        }

        hd = { # Dicionário contendo informações do HD/SSD
            "total" : round(psutil.disk_usage('/').total/1024**3, 2),
            "livre" : round(psutil.disk_usage('/').free/1024**3, 2)
        }

        info_interface = [] # Cria uma lista com as informações da interface de rede
        endereco = psutil.net_if_addrs() # Pega os IPs da interface da rede do cliente
        status = psutil.net_if_stats() # Pega o status da interface da rede do cliente

        for nome_interface, enderecos_interface in endereco.items(): # nome_interface recebe o rótulo do dicionário endereco e enderecos_interface a lista com objetos dos dados das interfaces de rede

            ip_v4 = "" # Variável para receber o ip_v4 da interface atual de rede do loop
            ip_v6 = "" # Variável para receber o ip_v6 da interface atual de rede do loop
            mac = "" # Variável para receber o mac da interface atual de rede do loop

            for addr in enderecos_interface: # Percorre os objetos com os dados das interfaces de rede para coletar seus IPs lógicos/físico
                if addr.family == socket.AF_INET:
                    ip_v4 = addr.address
                elif addr.family == socket.AF_INET6:
                    ip_v6 = addr.address
                elif addr.family == psutil.AF_LINK:
                    mac = addr.address

            if nome_interface in status: # Se o rotulo atual (Wi-Fi, Ethernet, Loopback) da interface de rede existe no status, pegamos se ele tá ativo ou não
                up_ou_down = status[nome_interface].isup
            else: # Caso contrário, pressupomos que não está ativo.
                up_ou_down = False

            status_string = "UP" if up_ou_down else "DOWN" # Se up_ou_down é true, retorna "UP", caso contrário, "FALSE"
            tipo_interface= self.tipo_interface(nome_interface) # Enviamos o rótulo do tipo da interface para o transformar em uma string apropriada para o nosso projeto

            # Adicionamos na lista um dicionário com os dados da interface de rede coletados
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