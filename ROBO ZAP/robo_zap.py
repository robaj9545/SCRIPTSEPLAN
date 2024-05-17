import pywhatkit
import time

# Função para responder automaticamente às mensagens recebidas
def auto_responder():
    print("Aguardando mensagens...")
    while True:
        # Verifica se há novas mensagens a cada 10 segundos
        pywhatkit.sendwhatmsg_instantly("+5586995601319", "Olá! Esta é uma mensagem automática em resposta à sua mensagem.", wait_time=5)
        time.sleep(5)

# Chama a função principal
if __name__ == "__main__":
    auto_responder()

