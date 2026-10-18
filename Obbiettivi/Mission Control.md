🛰️ MISSION CONTROL — Specifica progettuale V1

L'idea complessiva è una web application locale che unisce due funzioni:
<>
                         ┌───────────────────────┐
                         │   MISSION CONTROL     │
                         │      WEB APP          │
                         └───────────┬───────────┘
                                     │
                  ┌──────────────────┴──────────────────┐
                  │                                     │
                  ▼                                     ▼
          ┌───────────────┐                    ┌────────────────┐
          │   MY CLOUD    │                    │    MISSION     │
          │               │                    │    CONTROL     │
          └───────┬───────┘                    └───────┬────────┘
                  │                                    │
                  ▼                                    ▼
           File system                         Monitoring Engine
                  │                                    │
                  │                            ┌───────┼────────┐
                  │                            ▼       ▼        ▼
                  │                         Apache   DB      Python
                  │                                   
                  └──────────────┬─────────────────────┘
                                 ▼
                           MySQL / MariaDB

Il tutto gira direttamente sul laptop Windows portato all'esame.

1. 🖥️ Ambiente di esecuzione
┌─────────────────────────────────────────┐
│             WINDOWS LAPTOP              │
│                                         │
│  ┌──────────┐   ┌──────────┐            │
│  │  APACHE  │   │ MySQL /  │            │
│  │          │   │ MariaDB  │            │
│  └────┬─────┘   └────┬─────┘            │
│       │              │                  │
│       └──────┬───────┘                  │
│              ▼                          │
│       ┌──────────────┐                  │
│       │    PYTHON    │                  │
│       │ orchestrator │                  │
│       │ + monitoring │                  │
│       └──────────────┘                  │
│                                         │
└─────────────────────────────────────────┘
Stack previsto
Componente	Tecnologia
OS	Windows
Web server	Apache
Web application	PHP
Frontend	HTML + CSS + JavaScript
Database	MySQL / MariaDB
Monitoring / process management	Python
Comunicazione dati	da definire nell'implementazione, eventualmente JSON
Storage file	filesystem locale

Raspberry Pi è fuori dalla V1.
Potrà eventualmente diventare una versione futura/deployment alternativo.

2. 🔐 Accesso

Autenticazione volutamente minimale:

             BROWSER
                │
                ▼
          ┌───────────┐
          │  LOGIN    │
          │ password  │
          └─────┬─────┘
                │
                ▼
        ┌───────────────┐
        │ sessione PHP  │
        └───────┬───────┘
                │
         ┌──────┴──────┐
         ▼             ▼
     MY CLOUD     MISSION CONTROL
Solo password
Nessun username
Una sola utenza
Nessun sistema di ruoli
Password configurata nel file .env/configurazione
Sessione valida fino a Logout
Nessun timeout automatico
3. ☁️ MY CLOUD

La parte cloud è un vero file manager locale.

MY CLOUD
│
├── 📁 Documenti
│   ├── 📁 Scuola
│   │   ├── relazione.pdf
│   │   └── appunti.txt
│   │
│   └── 📁 Progetti
│
├── 📁 Immagini
│
└── file.zip
Funzioni V1
                    MY CLOUD
                       │
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
     UPLOAD         DOWNLOAD        DELETE
        │              │              │
        └──────────────┼──────────────┘
                       │
                 FILE SYSTEM
                       │
                 ┌─────┴─────┐
                 ▼           ▼
              FOLDER       FILE

Sono comprese:

creazione cartelle
sottocartelle
navigazione
upload
download
eliminazione
eliminazione cartelle
link temporanei
scelta della durata del link

Spostamento dei file tra cartelle: previsto, ma non prioritario nella V1.

4. 📂 Come vengono conservati i file

Abbiamo scelto la soluzione più semplice:

nome originale nel filesystem.

Esempio:

/storage/
│
├── documenti/
│   ├── scuola/
│   │   ├── relazione.pdf
│   │   └── appunti.txt
│   │
│   └── personali/
│
└── immagini/
    └── foto.jpg

Il database conserva i metadati necessari.

Fondamentale:

Browser
   │
   │ richiesta download
   ▼
Apache
   │
   ▼
PHP
   │
   ├── controllo sessione
   ├── controllo file
   ├── controllo sicurezza
   │
   ▼
Filesystem
   │
   ▼
PHP → Browser

Il file non viene esposto direttamente da Apache.

Verranno quindi gestiti anche i problemi di:

path traversal
nomi non validi
accesso a file fuori dallo storage
5. 🔗 Link temporanei

Il link non dà accesso diretto al file.

                    GENERAZIONE LINK
                           │
                           ▼
                    ┌─────────────┐
                    │   TOKEN     │
                    └──────┬──────┘
                           │
                  ┌────────┴────────┐
                  ▼                 ▼
                FILE              SCADENZA
                  │                 │
                  └────────┬────────┘
                           ▼
                       DATABASE

Quando qualcuno usa il link:

Link
 │
 ▼
PHP
 │
 ├── token valido?
 ├── non scaduto?
 └── file esistente?
        │
        ▼
      FILE

Il link:

è riutilizzabile
resta valido fino alla scadenza
ha una durata scelta dall'utente
non ha un limite di download
non viene invalidato dopo il primo utilizzo

Gli accessi al cloud non vengono registrati nel log eventi di Mission Control.

6. 🎛️ MISSION CONTROL

Questa è la parte più caratterizzante del progetto.

La dashboard controlla l'infrastruttura reale del programma.

┌─────────────────────────────────────────────┐
│              MISSION CONTROL                │
├─────────────────────────────────────────────┤
│                                             │
│  SERVICES                                   │
│                                             │
│  APACHE       ● ONLINE   PID 7316  [STOP]  │
│  MYSQL        ● ONLINE   PID 4820  [STOP]  │
│  PYTHON API   ○ OFFLINE  PID —     [START] │
│                                             │
├─────────────────────────────────────────────┤
│                                             │
│  SYSTEM                                     │
│                                             │
│  CPU       72%   ███████░░░                 │
│  RAM       48%   █████░░░░░                 │
│                                             │
│  DOWNLOAD  32 MB/s ███░░░░░░░               │
│  UPLOAD     8 MB/s █░░░░░░░░░               │
│                                             │
└─────────────────────────────────────────────┘
7. ⚙️ Process monitoring

I componenti sono processi realmente separati.

                 main.py
                   │
          ┌────────┼────────┐
          ▼        ▼        ▼
       APACHE     MYSQL    PYTHON
       PID 7316   PID 4820  PID 9132

Python conosce preventivamente i processi da controllare.

Il PID serve per identificare l'istanza attualmente in esecuzione, ma non è l'identità permanente del componente.

Quindi:

MYSQL
 │
 ├── processo muore
 │
 ├── nuovo avvio
 │
 └── PID cambia
       │
       ▼
MONITOR → riconosce comunque MYSQL
8. 🟢 Controlli manuali

Ogni componente ha il proprio controllo.

ONLINE
   │
   └── [STOP]

OFFLINE
   │
   └── [START]

Non ci saranno:

START ALL
STOP ALL
RESTART
Avvio
Dashboard
    │
    ▼
 richiesta START
    │
    ▼
  main.py
    │
    ▼
avvia processo
    │
    ▼
monitor trova PID
    │
    ▼
● ONLINE

Il sistema non dichiara ONLINE semplicemente perché ha inviato il comando: deve verificare che il processo esista davvero.

9. 💀 Processo terminato

Nessun auto-restart.

MYSQL ONLINE
     │
     X
     │
processo muore
     │
     ▼
monitor rileva
     │
     ├───────────────┐
     ▼               ▼
  ALERT             DB
CRITICAL         EVENT LOG
     │
     ▼
  POPUP

Quindi:

rilevazione → registrazione → notifica

e non:

rilevazione → riavvio automatico.

10. 🧠 main.py

main.py sarà il punto di ingresso dell'infrastruttura Python.

                 python main.py
                       │
                       ▼
              ┌─────────────────┐
              │   ORCHESTRATOR  │
              └────────┬────────┘
                       │
          ┌────────────┴────────────┐
          ▼                         ▼
     PROCESS CONTROL           MONITORING
          │                         │
          ▼                         ▼
 START / STOP                 CPU / RAM / NET
 APACHE / DB / PYTHON         PROCESS STATUS

Quando main.py viene chiuso:

si ferma il monitor/orchestratore, ma gli altri servizi rimangono in esecuzione.

11. 📊 Monitoraggio hardware

Il sistema raccoglie soltanto dati globali del laptop.

CPU
CPU
100% ┤
     │
 72% ┤███████░░░
     │
  0% └──────────

Scala sempre:

0 → 100%

RAM

Stessa logica:

0 → 100%

Rete

Due valori distinti:

DOWNLOAD   32 MB/s   ███░░░░░░░
UPLOAD      8 MB/s   █░░░░░░░░░

Nessun totale upload+download.

La scala visuale, ad esempio 100 MB/s, sarà configurabile.

12. ⏱️ Frequenza del monitor

Il monitor funziona autonomamente.

START
  │
  ▼
┌─────────────────────┐
│ rileva stato        │
│ CPU                 │
│ RAM                 │
│ NETWORK             │
│ PROCESSI            │
└──────────┬──────────┘
           │
        ~3 sec
           │
           └──────────────► ripeti

Target:

circa 2–5 secondi, con un valore predefinito intorno ai 3 secondi.

Quindi quasi real-time, senza pretendere un sistema hard-real-time.

13. 🚨 Sistema eventi

Qui abbiamo fatto una distinzione importante.

Il sistema non conserva lo storico continuo di CPU/RAM/rete.

Conserva invece gli eventi significativi.

┌────────────────────────────────────┐
│          EVENT LOG DATABASE        │
├────────────────────────────────────┤
│ 19:41:12 CRITICAL DATABASE OFFLINE │
│ 19:43:08 INFO     DATABASE ONLINE  │
│ 19:44:51 WARNING  CPU > 90%        │
│ 19:45:32 INFO     CPU NORMAL       │
└────────────────────────────────────┘

Il log è cronologico e append-only.

Un evento successivo non modifica quello precedente.

14. 🟡 Livelli evento
INFO

Eventi normali:

INFO
 ├── DATABASE ONLINE
 ├── APACHE ONLINE
 └── USCITA AUTORIZZATA DEL PROGRAMMA MYSQL

Salvati nel database, ma senza popup.

WARNING

Condizione anomala non necessariamente critica.

WARNING
 ├── CPU > soglia
 └── RAM > soglia

Popup.

CRITICAL

Problema grave:

CRITICAL
 ├── DATABASE OFFLINE
 ├── APACHE OFFLINE
 └── ...

Popup.

15. 📋 Regole degli alert

Le regole sono predefinite nel codice/configurazione.

Non saranno modificabili dalla dashboard.

Esempio concettuale:

CPU > 90%  → WARNING
CPU > 98%  → CRITICAL

RAM > 90%  → WARNING

DATABASE OFFLINE → CRITICAL
APACHE OFFLINE   → CRITICAL

Le soglie definitive verranno fissate durante l'implementazione.

16. 🔔 Popup

Gli eventi WARNING e CRITICAL vengono mostrati direttamente nella pagina.

╔══════════════════════════════════╗
║ ⚠ WARNING                        ║
║                                  ║
║ CPU USAGE > 90%                  ║
║                                  ║
║                  [ CHIUDI ]      ║
╚══════════════════════════════════╝

Caratteristiche:

nessun suono
rimane visibile fino a CHIUDI
chiusura automatica dopo 1 minuto
chiudere il popup non risolve l'evento
l'evento rimane nel database
17. 📬 Coda dei popup

Un evento alla volta.

EVENTI
 │
 ├── MYSQL OFFLINE
 ├── APACHE OFFLINE
 ├── CPU HIGH
 └── MYSQL OFFLINE
          │
          ▼
      POPUP QUEUE
          │
          ▼
      [ MYSQL OFFLINE ]
          │
        chiudi
          ▼
      [ APACHE OFFLINE ]
          │
        chiudi
          ▼
         ...

Eventi dello stesso tipo logico vengono consolidati nella coda visuale.

MYSQL OFFLINE
MYSQL OFFLINE
MYSQL OFFLINE
       ↓
  un solo popup

Mentre:

MYSQL OFFLINE
APACHE OFFLINE
CPU HIGH

sono tre tipi differenti.

Importante: questo vale soltanto per la visualizzazione.
Nel database vengono comunque registrati tutti gli eventi individualmente.

18. 🗄️ Database

Il DB reale sarà MySQL o MariaDB.

Non SQLite.

Concettualmente:

                 DATABASE
                    │
        ┌───────────┴───────────┐
        ▼                       ▼
   FILE METADATA             EVENTS
        │                       │
        │                 ┌─────┴─────┐
        │                 │           │
        ▼                 ▼           ▼
     files             WARNING     CRITICAL
     folders             INFO
     tokens

Dovrà quindi gestire almeno:

struttura/metadati dei file
cartelle
token dei link temporanei
scadenze
eventi Mission Control

La struttura SQL precisa la definiamo in fase di implementazione.

19. ⚙️ Configurazione

Un punto centrale sarà il file di configurazione.

Concettualmente:

                 .env / CONFIG
                       │
       ┌───────────────┼────────────────┐
       ▼               ▼                ▼
    PASSWORD       NETWORK LIMIT    THRESHOLDS
                       │
                       ▼
                   100 MB/s

Quindi niente:

NETWORK_LIMIT = 100

sparso casualmente dentro il codice.

Il progetto sarà parametrizzato.

20. 🧩 Separazione concettuale

La cosa che secondo me rende interessante il progetto è che non stiamo semplicemente facendo:

"un sito con qualche grafico."

Stiamo costruendo una piccola infrastruttura dove il sito osserva e controlla ciò che lo fa funzionare.

                  ┌─────────────────────┐
                  │      BROWSER        │
                  └──────────┬──────────┘
                             │
                             ▼
                  ┌─────────────────────┐
                  │       APACHE        │
                  │      WEB SERVER     │
                  └───────┬─────┬───────┘
                          │     │
                 ┌────────┘     └────────┐
                 ▼                       ▼
          ┌─────────────┐         ┌─────────────┐
          │     PHP     │         │     WEB     │
          │ APPLICATION │         │   ASSETS    │
          └──────┬──────┘         └─────────────┘
                 │
        ┌────────┴─────────┐
        ▼                  ▼
   ┌─────────┐       ┌─────────────┐
   │  FILES  │       │ MYSQL/      │
   │ SYSTEM  │       │ MARIADB     │
   └─────────┘       └──────┬──────┘
                             ▲
                             │
                     ┌───────┴───────┐
                     │    PYTHON     │
                     │               │
                     │ ORCHESTRATOR  │
                     │       +       │
                     │   MONITOR     │
                     └───────┬───────┘
                             │
                  ┌──────────┼──────────┐
                  ▼          ▼          ▼
               APACHE      MYSQL     PYTHON
               PROCESS     PROCESS   PROCESS

Ed è proprio qui che il progetto smette di essere soltanto web development e diventa anche sistemi, process management, monitoring, database, sicurezza e automazione.

21. 🎯 Cosa NON c'è nella V1

Questa lista è importante quasi quanto quella delle funzionalità.

Fuori scope:

Raspberry Pi
cloud remoto
multi-user
ruoli/permessi
RBAC
sincronizzazione
versioning dei file
cronologia CPU/RAM/rete
Task Manager per-processo
auto-restart
START ALL
STOP ALL
RESTART
alert configurabili dalla UI
funzionalità API esterne non necessarie
architetture distribuite
Kubernetes
Docker obbligatorio
microservizi inutili
qualsiasi cosa aggiunta solo per poter dire "guarda che roba complessa ho fatto".

Questa ultima è probabilmente la più importante. 😂

22. 🧪 Filosofia della V1

Il progetto deve poter essere portato all'esame e fatto partire sul laptop senza dipendere da Internet o da hardware esterno.

                    LAPTOP
                       │
             ┌─────────┴─────────┐
             │                   │
          PROJECT             DATABASE
             │                   │
             └─────────┬─────────┘
                       │
                    START
                       │
                       ▼
              ┌────────────────┐
              │ MISSION CONTROL│
              └────────────────┘
                       │
              ┌────────┴────────┐
              ▼                 ▼
           MY CLOUD          MONITOR

Il README dovrà documentare chiaramente:

REQUIREMENTS
│
├── Windows version
├── Python version
├── Python packages
├── Apache
├── PHP
├── MySQL/MariaDB
└── configuration

Non serve un installer magico.
Serve che tu sappia esattamente cosa deve esserci e perché. 