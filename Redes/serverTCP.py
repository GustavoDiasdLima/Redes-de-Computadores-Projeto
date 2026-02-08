#servidor tcp
import socket
import json
import time
from interface import Dashboard
from cryptography.fernet import Fernet

porta = 6000 
Chave = b'8_S0bC8x0e_oGz1_v4d6d6-fD2_X7xQz5y1wZ3_v4d0=' 
cipher = Fernet(Chave) 

class servidorTCP:
    def __init__(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind(('0.0.0.0', porta)) 
        self.socket.listen() 
        self.socket.settimeout(1.0) 
        self.clientes = {} 
        self.tela = Dashboard() 
        print(f"Ponto de conexão do servidor inicializado com sucesso no protocolo TCP!")

    def listen(self):
        print(f"Aguardando conexão TCP... (Pressione CTRL+C para acessar o menu!)")
        while True: 
            try: 
                while True: 
                        conexao, endereco = self.socket.accept() 
                        print(f"Conexão TCP feita com sucesso com: {endereco[0]}")
                        self.processar_dados_cliente(conexao, endereco) 
                    except socket.timeout:
                        pass

            except KeyboardInterrupt: 
                self.tela.clean() 
                print("--- MENU DO SERVIDOR ---")
                print("1. Detalhar um cliente")
                print("2. Voltar ao monitoramento")
                print("0. Sair")

                opcao = input("Escolha: ")

                if opcao == "1":

                    self.tela.clean() #
                    print("Clientes disponíveis :D :")
                    print("-" * 30)
                    if len(self.clientes) == 0: 
                        print("Nenhum cliente conectado ainda ;(")
                        input("Pressione ENTER para voltar ao monitoramento...")
                        self.tela.desenharDashboard(self.clientes)
                        continue

                    for ips in self.clientes: 
                        print(f"-> {ips}")
                    print("-" * 30)

                    ip_alvo = input("Digite o IP do cliente: ")
                    dados_cliente = self.clientes.get(ip_alvo) 
                    self.tela.detalharCliente(ip_alvo, dados_cliente) # 
                    self.tela.desenharDashboard(self.clientes) #
                elif opcao == "2": 

                    print("Retornando...")
                    self.tela.desenharDashboard(self.clientes) 
                    continue

                elif opcao == "0": 
                    print("Encerrando servidor...")
                    break 


    def processar_dados_cliente(self, conexao, endereco):
        ip_cliente = endereco[0] 
        try:
            dados = conexao.recv(4096) 
            if len(dados)>0: 
                try:
                    decodificado = cipher.decrypt(dados) 

                    relatorio = json.loads(decodificado.decode('utf-8')) 

                    relatorio['visibilidade'] = time.time() 

                    ip_cliente = endereco[0] 
                    self.clientes[ip_cliente] = relatorio 
                    self.tela.desenharDashboard(self.clientes) 
                except Exception as e_crypto: 
                    print(f"Falha de criptografia de {ip_cliente}")
                    return

        except Exception as e: 
            print(f"Erro no processamento de dados do cliente: {e} ")


        finally:
            conexao.close() 


if __name__ == "__main__":
    servidorTCP = servidorTCP()
    servidorTCP.listen()