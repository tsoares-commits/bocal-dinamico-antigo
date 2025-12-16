import RPi.GPIO as GPIO
import sys
import threading
import time
import PythonLibMightyZap_Rasp_FC_V1_3 as MightyZap
import serial
import glob
import select

# =========================== CONFIGURAÇÃO MIGHTYZAP ================================

Actuator_ID = 0
Actuator_ID_1 = 2
Actuator_ID_2 = 2

CONVERSAO_MM_PARA_POSICAO = 136.518518519
OFFSET_POSICAO_MM_MIGHTYZAP = 7.0
UPPER_MIGHTYZAP_MM = 1.01
LOWER_MIGHTYZAP_MM = -2.01

MIN_Position_Lente = 5.3    #rever essa config
MAX_Position_Lente = 95.8  

Limite_INFERIOR_LENTE = int(round((OFFSET_POSICAO_MM_MIGHTYZAP + MIN_Position_Lente) * CONVERSAO_MM_PARA_POSICAO))
Limite_SUPERIOR_LENTE = int(round((OFFSET_POSICAO_MM_MIGHTYZAP + MAX_Position_Lente) * CONVERSAO_MM_PARA_POSICAO))

LIMITE_INFERIOR_MIGHTYZAP = int(round((OFFSET_POSICAO_MM_MIGHTYZAP + LOWER_MIGHTYZAP_MM) * CONVERSAO_MM_PARA_POSICAO))
LIMITE_SUPERIOR_MIGHTYZAP = int(round((OFFSET_POSICAO_MM_MIGHTYZAP + UPPER_MIGHTYZAP_MM) * CONVERSAO_MM_PARA_POSICAO))

OFFSET_POSICAO_MIGHTYZAP = int(round(OFFSET_POSICAO_MM_MIGHTYZAP * CONVERSAO_MM_PARA_POSICAO))

MAX_VELOCIDADE_MIGTHYZAP = 1024



# =========================== FUNÇÃO IDENTIFICAR PORTAS =============================

def serial_ports():
    if sys.platform.startswith('win'):
        ports = ['COM%s' % (i + 1) for i in range(256)]
    elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
        ports = glob.glob('/dev/ttyUSB*') + glob.glob('/dev/ttyS*')
    else:
        return []

    result = []
    for port in ports:
        try:
            s = serial.Serial(port)
            s.close()
            result.append(port)
        except Exception:
            pass
    return result

PortalSerialConectadas = serial_ports()


# ============================= CONECTAR Lente =================================

def conectar_mightyzap_Lente(porta_lente):
    if porta_lente not in PortalSerialConectadas:
        print("erro")
        return False
    MightyZap.OpenMightyZap(porta_lente,57600)
    time.sleep(0.01)

    MightyZap.GoalSpeed(Actuator_ID_2, 400)

    #Varredura descendo Lente
    for pos_lent in range  (Limite_INFERIOR_LENTE, Limite_SUPERIOR_LENTE, 10):
        MightyZap.GoalPosition(Actuator_ID_2, pos_lent)
        time.sleep(0.01)

    #Volta para offset Lente
    for pos_lent in range (LIMITE_SUPERIOR_LENTE, OFFSET_POSICAO_MIGHTYZAP, -10):
        MightyZap.GoalPosition(Actuator_ID_2, pos_lent)
        time.sleep(0.01)

        print("✅ Motores Lentes Posicionados.")
    return True

#================================ Conectar Bocal=======================================

def conectar_mightyzap(porta):
    if porta not in PortalSerialConectadas:
        print("Erro: porta inválida.")
        return False

    print(f"\n🔌 Conectando ao MightyZap pela porta {porta} ...")
    MightyZap.OpenMightyZap(porta, 57600)
    time.sleep(0.01)

    MightyZap.GoalSpeed(Actuator_ID, 400)    
    MightyZap.GoalSpeed(Actuator_ID_1, 400)
    

    

    # Varredura descendo bocal
    for pos in range(LIMITE_INFERIOR_MIGHTYZAP, LIMITE_SUPERIOR_MIGHTYZAP, 10):
        MightyZap.GoalPosition(Actuator_ID, pos)
        MightyZap.GoalPosition(Actuator_ID_1, pos)
        time.sleep(0.01)
        

    # Voltando para o offset Bocal 
    for pos_bocal in range(LIMITE_SUPERIOR_MIGHTYZAP, OFFSET_POSICAO_MIGHTYZAP, -10):
        MightyZap.GoalPosition(Actuator_ID, pos_bocal)
        MightyZap.GoalPosition(Actuator_ID_1, pos_bocal)
        time.sleep(0.01)


    print("✅ Motores Bocal Posicionados.")
    return True


# =============================== DEFINIR VELOCIDADE ===============================

def definir_velocidade(nova_velocidade):
    global velocidade_percentual

    try:
        nova_velocidade = float(nova_velocidade)
    except:
        print("Velocidade inválida!")
        return

    if nova_velocidade < 0: nova_velocidade = 0
    if nova_velocidade > 100: nova_velocidade = 100

    speed = int((nova_velocidade / 100) * MAX_VELOCIDADE_MIGTHYZAP)
    

    MightyZap.GoalSpeed(Actuator_ID, speed)
    MightyZap.GoalSpeed(Actuator_ID_1, speed)
    MightyZap.GoalSpeed(Actuator_ID_2, speed)
    
#================================ DEFINIR POSIÇÃO BOCAL===================================

def definir_posicao_Bocal(nova_posicao):
    try:
        nova_posicao = float(nova_posicao)
    except ValueError:
        print(" Valor inválido")
        return

    if nova_posicao < LOWER_MIGHTYZAP_MM or nova_posicao > UPPER_MIGHTYZAP_MM:
        print("Fora dos limites do bocal")
        return

    pos_int = int(round(
        nova_posicao * CONVERSAO_MM_PARA_POSICAO
        + OFFSET_POSICAO_MIGHTYZAP
    ))

    if pos_int < LIMITE_INFERIOR_MIGHTYZAP or pos_int > LIMITE_SUPERIOR_MIGHTYZAP:
        print("Posição fora da calibração")
        return

    print(f"Movendo BOCAL para {nova_posicao:.2f} mm (pos={pos_int})")

    MightyZap.GoalPosition(Actuator_ID, pos_int)
    MightyZap.GoalPosition(Actuator_ID_1, pos_int)

#================================DEFINIR POSIÇÃO Lente ===================================    

def definir_posicao_Lentes(nova_posicao_lente):
    try:
        nova_posicao_lente = float(nova_posicao_lente)
    except ValueError:
        print("Valor inválido")
        return

    if nova_posicao_lente < MIN_Position_Lente or nova_posicao_lente > MAX_Position_Lente:
        print("Fora dos limites da lente")
        return

    pos_int = int(round(nova_posicao_lente))

    print(" Movendo LENTE para {nova_posicao_lente:.1f} mm")

    MightyZap.GoalPosition(Actuator_ID_2, pos_int)


# =============================== MODO TERMINAL ===================================

def menu_terminal():
    while True:
        try:
            print("\n---------------- MENU ----------------")
            print("1 → Definir velocidade (%)")
            print("2 → Ajustar posição motor Bocal")
            print("3 → Ajustar posição motor Lente")
            print("4 → Sair")

            opc = input("Escolha: ").strip()

            if opc == "1":
                v = input("Digite nova velocidade (%): ").strip()
                definir_velocidade(v)

            elif opc == "2":
                p = input("Digite a extensão em mm do Bocal: ").strip()
                definir_posicao_Bocal(p)

            elif opc == "3":
                t = input ("Digite a extensão em mm da Lente").strip()
                definir_posicao_Lentes(t)
                
            
            elif opc == "4":
                print("Programa Encerrado")
                return

            else:
                print("❌ Opção inválida.")

        except KeyboardInterrupt:
            print("\nInterrompido pelo usuário.")
            return


# =============================== INÍCIO DO PROGRAMA ===============================

if __name__ == "__main__":

    print("\n===============================================")
    print("       CONTROLE DO BOCAL VIA TERMINAL")
    print("===============================================\n")

    print("Portas encontradas:")
    for p in PortalSerialConectadas:
        print("  -", p)

    porta = input("\nDigite a porta para conectar: ") 

    if not conectar_mightyzap(porta):
        sys.exit()

    menu_terminal()
    GPIO.cleanup()



