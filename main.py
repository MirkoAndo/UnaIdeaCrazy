import os
import wmi
import speedtest_cli

# Enable ANSI escape sequences in Windows console
os.system('')

# ANSI escape codes
RED = "\033[91m"
WHITE = "\033[97m"
RESET = "\033[0m"

os.system('cls' if os.name == 'nt' else 'clear')  # Clear the console for better readability
user_input = ""

def get_process_status(process_name):
    c = wmi.WMI()
    for process in c.Win32_Process(name=process_name):
        return "ONLINE", process.ProcessId
    return "OFFLINE", None

apachestatus = get_process_status("httpd.exe")
mysqlstatus = get_process_status("mysql.exe")

services_status = {

    "mission_control": {
        "status": "ONLINE",
        "pid": os.getpid()},

    "APACHE": {
        "status": apachestatus[0], 
        "pid": apachestatus[1]},

    "MYSQL": {
        "status": mysqlstatus[0],
        "pid": mysqlstatus[1]},
    }

 
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
    mysqlstatus = get_process_status("mysql.exe")
    cpu_usage = wmi.WMI().Win32_Processor()[0].LoadPercentage
    operating_system = wmi.WMI().Win32_OperatingSystem()[0]
    total_memory_mb = int(operating_system.TotalVisibleMemorySize) / 1024
    free_memory_mb = int(operating_system.FreePhysicalMemory) / 1024
    ram_usage = round(total_memory_mb - free_memory_mb, 2)

    



    Mission_control_table = rf"""
    ┌──────────────────────────────────────────────────────────────────
    │              MISSION CONTROL  ● ONLINE    PID {services_status['mission_control']['pid']}        
    ├──────────────────────────────────────────────────────────────────
    │                                             
    │  SERVICES                                   
    │                                             
    │  APACHE       ● {services_status['APACHE']['status']}    PID {services_status['APACHE']['pid']}   
    │  MYSQL        ● {services_status['MYSQL']['status']}   PID {services_status['MYSQL']['pid']}  
    │    
    │                                             
    ├──────────────────────────────────────────────────────────────────
    │                                             
    │  SYSTEM                                     
    │                                             
    │  CPU      {cpu_usage} %             
    │  RAM      {ram_usage/1024:.2f} GB   
    │                                             
    └──────────────────────────────────────────────────────────────────

    """
    services_status = {

    "mission_control": {
        "status": "ONLINE",
        "pid": os.getpid()},

    "APACHE": {
        "status": apachestatus[0], 
        "pid": apachestatus[1]},

    "MYSQL": {
        "status": mysqlstatus[0],
        "pid": mysqlstatus[1]},
    }

    print(f"{RED}{ASCII_logo_service}{RESET}")
    print(f"{WHITE}{Mission_control_table}{RESET}")

    if user_input.lower() == 'exit' or user_input.lower() == 'quit':
        print("Exiting the program.")
        os.system('cls' if os.name == 'nt' else 'clear')
        break

    custom_command = user_input.lower() in {
        'sv apache',
        'sv mysql',
        'stop apache',
        'stop mysql',
    }

    if user_input.lower() == 'sv apache':
        os.system(r'start Apache24\bin\httpd.exe')
        apachestatus = get_process_status("httpd.exe")


    if user_input.lower() == 'sv mysql':
        os.system(r'start MySQL\bin\mysqld.exe')
        mysqlstatus = get_process_status("mysql.exe")


    if user_input.lower() == 'stop apache':
        os.system('taskkill /F /IM  httpd.exe')
        apachestatus = get_process_status("httpd.exe")


    if user_input.lower() == 'stop mysql':
        os.system('taskkill /F /IM mysql.exe')
        mysqlstatus = get_process_status("mysql.exe")


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
    
