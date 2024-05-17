import pygetwindow as gw
import keyboard
from pywinauto import Application
import time

def interagir_com_uac():
    # Substitua pelo caminho real do executável que aciona o UAC
    caminho_aplicativo_uac = r'C:\Users\usuario\Downloads\dbvis_windows-x64_24_1_jre.exe'

    # Inicia o aplicativo que aciona o UAC
    app = Application(backend='uia').start(caminho_aplicativo_uac)

    # Aguarda a janela do prompt do UAC aparecer
    dialogo_uac = app.window(title='Controle de Conta de Usuário')

    # Aguarda a janela do UAC estar pronta (ajuste o tempo de espera conforme necessário)
    time.sleep(2)

    # Interage com o prompt do UAC (por exemplo, clicando no botão 'Sim')
    dialogo_uac['BotaoSim'].click()

def capturar_digitacao():
    # Obter a janela ativa
    janela_ativa = gw.getActiveWindow()

    # Verificar se a janela está ativa
    if janela_ativa is not None:
        print(f"Capturando digitacao na janela: {janela_ativa.title}")

        # Chamar a função para interagir com o UAC
        interagir_com_uac()

        # Função de callback para lidar com os eventos de teclado
        def callback(e):
            if e.event_type == keyboard.KEY_DOWN:
                print(f"Tecla pressionada: {e.name}")

        # Adicionar um manipulador de eventos de teclado
        keyboard.hook(callback)

        # Aguardar até que o usuário pressione Esc para encerrar
        keyboard.wait("esc")

        # Remover o manipulador de eventos de teclado
        keyboard.unhook_all()

    else:
        print("Nenhuma janela ativa encontrada.")

if __name__ == "__main__":
    capturar_digitacao()

