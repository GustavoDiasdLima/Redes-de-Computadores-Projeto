#Servidor/Consolidação 2.2 / incompleto
import os
import time

class Dashboard:
    def __init__(self):
        pass

    def clean(self): #limpar a tela
        if os.name == "nt": 
            os.system("cls") 
        else: 
            os.system("clear") 

    def desenharDashboard(self, listaClientes): 
        self.clean() 

        tempo = time.time() 

        online = 0;
        offline = 0; 

        for ip, dados in listaClientes.items(): 
            ultimo_visto = dados.get('visibilidade') 

            diferenca = tempo - ultimo_visto  

            if diferenca < 30: 
                online+=1
                dados['visibilidade_temp'] = "ONLINEEEEE" 
            else: 
                offline+=1
                dados['visibilidade_temp'] = "OFFLINEEEEEE" 

        
        print("-" * 75)
        print("PAINEL COM CLIENTES QUE ESTÃO CONECTADOS A ESTE SERVIDOR")
        print("-" * 75)
        print(f"Clientes que estão online: {online} | Clientes que estão offline: {offline}")
        print("-" * 75)
        print(f"{'IP':<20} | {'SISTEMA OPERACIONAL':<30} | {'STATUS'}")
        print("-" * 75)

        for ip, dados in listaClientes.items():
            status = dados.get('visibilidade_temp', '?')

            print(f"{ip:<20} | {dados['so']:<30} | {status}")

        print("-" * 75)

    def detalharCliente(self, ip, dados):
        self.clean() 
        if dados is None: 
            print(f"Erro!!!: Cliente com IP {ip} não encontrado.")
            input("Pressione enter para voltar...")
            return

        print("=" * 75)
        print(f"Detalhes do cliente: {ip}")
        print("=" * 75)

        print(f"Sistema Operacional: {dados['so']}")

        cpu = dados['processador']
        ram = dados['memoria']
        disco = dados['disco']

        print("-" * 75)
        print(f"CPU: {cpu['fisico']} Núcleos Físicos / {cpu['logico']} Lógicos (Uso: {cpu['uso']}%)")
        print(f"RAM: {ram['livre']} GB Livres / {ram['total']} GB Total")
        print(f"Disco: {disco['livre']} GB Livres / {disco['total']} GB Total")

        print("-" * 75)
        print("Interfaces de rede:")
        print(f"{'NOME':<30} | {'TIPO':<10} | {'STATUS'}\n")

        for item in dados['rede']:
            nome = item['nome_interface']
            tipo = item['tipo_interface']
            status = item['status_interface']

            print(f"{nome[:30]:<30} | {tipo:<10} | {status}")

            print(f"   -> IPv4: {item['ipv4']}")
            print(f"   -> IPv6: {item['ipv6']}")
            print(f"   -> MAC:  {item['mac']}")
            print("." * 75)

        print("=" * 75)
        input("Pressione ENTER para voltar ao Dashboard...")