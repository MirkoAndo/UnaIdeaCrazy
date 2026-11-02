import os
import subprocess
import wmi

# Enable ANSI escape sequences in Windows console
os.system('')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CMD_COMMANDS_DIR = os.path.join(BASE_DIR, "CmdCommands")

# ANSI escape codes
RED = "\033[91m"
WHITE = "\033[97m"
GREEN = "\033[92m"
BLUE = "\033[94m"
LIGHTYELLOW = "\033[93m"
RESET = "\033[0m"

os.system('cls' if os.name == 'nt' else 'clear')  # Clear the console for better readability
user_input = ""

def get_process_status(process_name):
    c = wmi.WMI()
    for process in c.Win32_Process(name=process_name):
        # Keep the rendered status width equal to OFFLINE so the links stay aligned.
        return f"{GREEN}ONLINE  {RESET}", process.ProcessId
    return f"{RED}OFFLINE {RESET}", None

apachestatus = get_process_status("httpd.exe")
mysqlstatus = get_process_status("mysqld.exe")

services_status = {

    "mission_control": {
        "status": f"{GREEN}ONLINE {RESET}",
        "pid": os.getpid(),
        "position": "localset"},

    "APACHE": {
        "status": apachestatus[0], 
        "pid": apachestatus[1],
        "position": "../Servizi_UnaIdeaCrazy/Apache24"},


    "MYSQL": {
        "status": mysqlstatus[0],
        "pid": mysqlstatus[1],
        "position": "../Servizi_UnaIdeaCrazy/mysql-26.10.0"
        },
    
    "PHP": {
        "status": None,
        "pid": None,
        "position": "../Servizi_UnaIdeaCrazy/php-8.5.12x64"
        }

    }

CUSTOM_COMMANDS = {
    'sv apache': {
        'service': 'APACHE', 
        'desc': 'avvia Apache', 
        'process': 'httpd.exe'
        },
    
    'sv mysql': {
        'service': 'MYSQL', 
        'desc': 'avvia MySQL', 
        'process': 'mysqld.exe'
        },
    
    'stop apache': {
        'service': 'APACHE', 
        'desc': 'ferma Apache', 
        'process': 'httpd.exe'},
    
    'stop mysql': {
        'service': 'MYSQL', 
        'desc': 'ferma MySQL', 
        'process': 'mysqld.exe'
        },
    }

def execute_batch_command(cmd_name, service_key, services):
    bat_filename = f"{cmd_name.replace(' ', '_')}.bat"
    bat_path = os.path.join(CMD_COMMANDS_DIR, bat_filename)

    if not os.path.exists(bat_path):
        print(f"{RED}File di comando non trovato: {bat_path}{RESET}")
        return False

    service_info = services.get(service_key, {})
    service_pos = service_info.get("position", "")
    service_pos_abs = os.path.abspath(os.path.join(BASE_DIR, service_pos)) if service_pos else ""

    # Prepariamo le variabili d'ambiente per il .bat
    env = os.environ.copy()
    if service_pos_abs:
        env["SERVICE_POSITION"] = service_pos_abs
    if service_key:
        env["SERVICE_NAME"] = service_key

    try:
        # Passiamo la posizione del file come argomento (%1)
        subprocess.run([bat_path, service_pos_abs], env=env, shell=True)
        return True
    except Exception as e:
        print(f"{RED}Errore durante l'esecuzione di {bat_filename}: {e}{RESET}")
        return False

ASCII_logo_service = r"""
 __       __  __            __                         ______                   __           __        _______    ______          ______    ______    ______    ______  
/  \     /  |/  |          /  |                       /      \                 /  |         /  |      /       |  /      \        /      \  /      \  /      \  /      \ 
$$  \   /$$ |$$/   ______  $$ |   __   ______        /$$$$$$  | _______    ____$$ |  ______ $$/       $$$$$$$/  /$$$$$$  |      /$$$$$$  |/$$$$$$  |/$$$$$$  |/$$$$$$  |
$$$  \ /$$$ |/  | /      \ $$ |  /  | /      \       $$ |__$$ |/       \  /    $$ | /      \$/        $$ |____  $$ |  $$/       $$____$$ |$$$  \$$ |$$____$$ |$$ \__$$/ 
$$$$  /$$$$ |$$ |/$$$$$$  |$$ |_/$$/ /$$$$$$  |      $$    $$ |$$$$$$$  |/$$$$$$$ |/$$$$$$  |         $$      \ $$ |             /    $$/ $$$$  $$ | /    $$/ $$      \ 
$$ $$ $$/$$ |$$ |$$ |  $$/ $$   $$<  $$ |  $$ |      $$$$$$$$ |$$ |  $$ |$$ |  $$ |$$ |  $$ |         $$$$$$$  |$$ |   __       /$$$$$$/  $$ $$ $$ |/$$$$$$/  $$$$$$$  |
$$ |$$$/ $$ |$$ |$$ |      $$$$$$  \ $$ \__$$ |      $$ |  $$ |$$ |  $$ |$$ \__$$ |$$ \__$$ |         /  \__$$ |$$ \__/  |      $$ |_____ $$ \$$$$ |$$ |_____ $$ \__$$ |
$$ | $/  $$ |$$ |$$ |      $$ | $$  |$$    $$/       $$ |  $$ |$$ |  $$ |$$    $$ |$$    $$/          $$    $$/ $$    $$/       $$       |$$   $$$/ $$       |$$    $$/ 
$$/      $$/ $$/ $$/       $$/   $$/  $$$$$$/        $$/   $$/ $$/   $$/  $$$$$$$/  $$$$$$/            $$$$$$/   $$$$$$/        $$$$$$$$/  $$$$$$/  $$$$$$$$/  $$$$$$/  
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         
"""


while True:
    apachestatus = get_process_status("httpd.exe")
    mysqlstatus = get_process_status("mysqld.exe")
    cpu_usage = 0
    total_memory_mb = 0
    free_memory_mb = 0
    ram_usage = 0
    operating_system = None
    #cpu_usage = wmi.WMI().Win32_Processor()[0].LoadPercentage
    #operating_system = wmi.WMI().Win32_OperatingSystem()[0]
    #total_memory_mb = int(operating_system.TotalVisibleMemorySize) / 1024
    #free_memory_mb = int(operating_system.FreePhysicalMemory) / 1024
    #ram_usage = round(total_memory_mb - free_memory_mb, 2)

    services_status = {

        "mission_control": {
            "status": f"{GREEN}ONLINE {RESET}",
            "pid": os.getpid(),
            "position": "localset"},

        "APACHE": {
            "status": apachestatus[0], 
            "pid": apachestatus[1],
            "position": "../Servizi_UnaIdeaCrazy/Apache24"},

        "MYSQL": {
            "status": mysqlstatus[0],
            "pid": mysqlstatus[1],
            "position": "../Servizi_UnaIdeaCrazy/mysql-26.10.0"},

        "PHP": {
            "status": None,
            "pid": None,
            "position": "../Servizi_UnaIdeaCrazy/php-8.5.12x64"
        }
    }

    Mission_control_table = rf"""
    ┌──────────────────────────────────────────────────────────────────
    │              MISSION CONTROL  ● {services_status['mission_control']['status']}     PID {services_status['mission_control']['pid']}
    ├──────────────────────────────────────────────────────────────────
    │         
    │  SERVIZI
    │
    │  {'SERVICE':<12}{'STATUS':<12}{'PID':<10}LINK
    │  {'APACHE':<12}● {services_status['APACHE']['status']:<12}  {str(services_status['APACHE']['pid']):<10}{BLUE}http://127.0.0.1/{RESET}
    │  {'MYSQL':<12}● {services_status['MYSQL']['status']:<12}  {str(services_status['MYSQL']['pid']):<10}{BLUE}http://127.0.0.1/{RESET}{LIGHTYELLOW}phpmyadmin{RESET}
    |
    ├──────────────────────────────────────────────────────────────────
    │ /help  - lista comandi custom                                            
    ├──────────────────────────────────────────────────────────────────
    │                                             
    │  SISTEMA                                     
    │                                             
    │  CPU      {cpu_usage} %             
    │  RAM      {ram_usage/1024:.2f} GB   
    │                                             
    └──────────────────────────────────────────────────────────────────

    """

    print(f"{RED}{ASCII_logo_service}{RESET}")
    print(f"{WHITE}{Mission_control_table}{RESET}")

    clean_input = user_input.strip().lower()

    if clean_input in ('exit', 'quit'):
        print("Exiting the program.")
        os.system('cls' if os.name == 'nt' else 'clear')
        break

    if clean_input == '/help':
        print("Lista comandi custom:")
        print("  /help - mostra questa lista")
        for cmd, info in CUSTOM_COMMANDS.items():
            print(f"  {cmd} - {info['desc']}")

    custom_command = clean_input == '/help' or clean_input in CUSTOM_COMMANDS

    if clean_input in CUSTOM_COMMANDS:
        # esegue il custom command
        cmd_info = CUSTOM_COMMANDS[clean_input]
        execute_batch_command(clean_input, cmd_info['service'], services_status)
        if cmd_info['service'] == 'APACHE':
            apachestatus = get_process_status("httpd.exe")
        elif cmd_info['service'] == 'MYSQL':
            mysqlstatus = get_process_status("mysqld.exe")

    if not custom_command:
        try:
            # Execute the command entered by the user
            if user_input.strip():
                os.system(user_input)
        except Exception as e:
            print(f"{RED}Error executing command: {e}{RESET}")
        
    user_input = input(f"{WHITE} \n Enter a command (or 'exit' || 'quit' to quit): ")

    print(RESET, end="")
    os.system('cls' if os.name == 'nt' else 'clear')
