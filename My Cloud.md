☁️ MY CLOUD — Specifica progettuale V1
1. 🎯 Obiettivo

My Cloud è il file manager personale integrato nella web application.

L'obiettivo è permettere all'utente autenticato di:

organizzare file e cartelle;
caricare file;
scaricarli;
eliminarli;
creare cartelle e sottocartelle;
generare link temporanei per condividere un file.

I file sono conservati fisicamente nel filesystem locale del laptop, mentre il database conserva le informazioni necessarie a gestirli.

                    MY CLOUD
                       │
          ┌────────────┼────────────┐
          ▼            ▼            ▼
       FILE           FOLDER       SHARE
          │            │            │
          ▼            ▼            ▼
     filesystem     filesystem    database
                                  + token
2. 🖥️ Dove risiedono i file

Il cloud non è un vero cloud remoto.

È uno storage locale accessibile tramite interfaccia web.

                    LAPTOP
┌──────────────────────────────────────────┐
│                                          │
│       Apache + PHP                      │
│             │                            │
│             ▼                            │
│        ┌───────────┐                     │
│        │ MY CLOUD  │                     │
│        └─────┬─────┘                     │
│              │                           │
│              ▼                           │
│        ┌─────────────┐                   │
│        │  STORAGE/   │                   │
│        │             │                   │
│        │ documenti/  │                   │
│        │ immagini/   │                   │
│        │ progetti/   │                   │
│        └─────────────┘                   │
│                                          │
└──────────────────────────────────────────┘

Il vantaggio è che il comportamento è quello di un cloud, ma l'infrastruttura rimane completamente sotto il controllo del progetto.

3. 📁 Struttura delle cartelle

Il filesystem rispecchia la struttura mostrata nella web app.

Esempio:

/storage
│
├── Documenti
│   │
│   ├── Scuola
│   │   ├── relazione.pdf
│   │   ├── appunti.txt
│   │   └── progetto.docx
│   │
│   └── Personali
│       └── documento.pdf
│
├── Immagini
│   ├── foto1.jpg
│   └── foto2.png
│
└── Progetti
    ├── progetto1.zip
    └── progetto2.pdf

Le cartelle possono avere profondità arbitraria.

Quindi:

Documenti
└── Scuola
    └── Informatica
        └── Esame
            └── progetto.pdf

è perfettamente valido.

4. 🗂️ File e cartelle nel database

Filesystem e database hanno ruoli diversi.

                    MY CLOUD
                       │
              ┌────────┴────────┐
              ▼                 ▼
        FILESYSTEM           DATABASE
              │                 │
              │                 ├── file
              │                 ├── folder
              │                 ├── metadata
              │                 └── share token
              │
              └──── file reale
Filesystem

Contiene il contenuto reale:

relazione.pdf
foto.jpg
progetto.zip
Database

Contiene le informazioni necessarie per sapere cosa sono e dove si trovano.

Ad esempio, concettualmente:

FILES
────────────────────────────
id
nome
percorso
cartella
dimensione
data
...

e:

FOLDERS
────────────────────────────
id
nome
parent_folder
...

Non è ancora la struttura SQL definitiva: quella verrà progettata durante l'implementazione.

5. 🏠 File browser

La schermata principale sarà un normale file browser.

┌──────────────────────────────────────────────┐
│ MY CLOUD                                     │
├──────────────────────────────────────────────┤
│                                              │
│  / Documenti / Scuola / Informatica          │
│                                              │
│  📁 5C                                       │
│  📁 Progetti                                 │
│  📄 relazione.pdf                            │
│  📄 appunti.txt                              │
│  📄 schema.docx                              │
│                                              │
├──────────────────────────────────────────────┤
│ [ + CARTELLA ]              [ ↑ UPLOAD ]     │
└──────────────────────────────────────────────┘

La navigazione avviene tramite cartelle, esattamente come in un file manager.

6. ⬆️ Upload

Il caricamento segue questo flusso:

                BROWSER
                   │
              seleziona file
                   │
                   ▼
                 PHP
                   │
          ┌────────┴─────────┐
          │                  │
     validazione          sicurezza
          │                  │
          └────────┬─────────┘
                   ▼
              FILESYSTEM
                   │
                   ▼
              file salvato

Il file viene salvato nella cartella attualmente visualizzata.

Esempio:

My Cloud
└── Documenti
    └── Scuola   ← utente si trova qui

         ↑ upload

Documenti/Scuola/nuovo_file.pdf
7. ⬇️ Download

Il download non espone direttamente il filesystem.

Browser
   │
   │ GET /download/...
   ▼
Apache
   │
   ▼
PHP
   │
   ├── utente autenticato?
   ├── file esistente?
   ├── percorso consentito?
   └── richiesta valida?
          │
          ▼
     FILESYSTEM
          │
          ▼
       Browser

Questa è una decisione importante della V1:

PHP controlla ogni download.

Non sarà quindi possibile raggiungere semplicemente qualcosa come:

/storage/Documenti/segreto.pdf

e bypassare l'applicazione.

8. 🗑️ Eliminazione

L'utente può eliminare:

file;
cartelle.

Per un file:

DELETE FILE
     │
     ▼
 controllo
     │
     ▼
 database
     │
     ▼
 filesystem
     │
     ▼
     ✓ eliminato

Per una cartella bisognerà definire durante l'implementazione il comportamento in presenza di contenuti.

La scelta progettuale prevista è comunque che la cartella rappresenti realmente una directory del filesystem.

9. 📂 Creazione cartella

L'utente può creare una nuova cartella dalla UI.

                [ + CARTELLA ]
                       │
                       ▼
                 "Informatica"
                       │
                       ▼
                     PHP
                       │
                ┌──────┴──────┐
                ▼             ▼
           filesystem       database
                │             │
                └──────┬──────┘
                       ▼
                 📁 Informatica

La nuova cartella viene creata nella directory corrente.

10. 🧭 Navigazione

La posizione corrente viene mostrata tramite breadcrumb.

HOME
 │
 └── Documenti
      │
      └── Scuola
           │
           └── Informatica

Esempio UI:

HOME / Documenti / Scuola / Informatica

Ogni elemento del percorso può essere utilizzato per tornare a una directory precedente.

11. ✏️ Nomi dei file

Abbiamo scelto volutamente:

nome originale del file nel filesystem.

Quindi:

relazione.pdf

rimane:

relazione.pdf

e non:

7f82a91c-9d32-....pdf

Questo rende il sistema più semplice da comprendere e da dimostrare.

Naturalmente il nome deve essere sanitizzato.

12. 🛡️ Sicurezza del filesystem

Questo è uno dei punti tecnicamente più importanti di My Cloud.

L'utente non deve poter manipolare arbitrariamente il percorso.

Per esempio, una richiesta del genere non deve mai permettere di uscire da /storage:

../../../../qualcosa

Il sistema dovrà quindi controllare:

             RICHIESTA
                 │
                 ▼
          normalizzazione
                 │
                 ▼
          controllo path
                 │
          ┌──────┴──────┐
          ▼             ▼
        VALID         INVALID
          │             │
          ▼             ▼
        FILE          DENY

Obiettivo:

/storage/...
     ✓

fuori da /storage
     ✗
13. 🔗 Condivisione tramite link

Ogni file può avere un link temporaneo.

                    FILE
                     │
                     ▼
             [ CREA LINK ]
                     │
                     ▼
              durata scelta
                     │
                     ▼
                   TOKEN
                     │
                     ▼
                 DATABASE

Il database associa:

TOKEN
  │
  ├── file
  └── scadenza
14. ⏳ Scadenza dei link

L'utente sceglie quanto deve durare il link.

Esempio:

CREA LINK

Durata:
○ 1 ora
○ 6 ore
○ 24 ore
○ 7 giorni
○ ...

          [ CREA ]

La durata esatta delle opzioni verrà definita nell'implementazione.

Il principio è:

creazione
    │
    ▼
validità
    │
    ├── valido → accesso
    │
    └── scaduto → accesso negato
15. 🔄 Link riutilizzabile

Il link non è monouso.

Esempio:

TOKEN ABC123
     │
     ├── download ✓
     ├── download ✓
     ├── download ✓
     └── download ✓
              │
           scadenza
              ▼
             ✗

Finché non scade, può essere utilizzato più volte.

Non viene registrato un contatore dei download.

16. 🔐 Accesso al link

Il link temporaneo passa comunque attraverso PHP.

        LINK TEMPORANEO
               │
               ▼
             PHP
               │
       ┌───────┼────────┐
       ▼       ▼        ▼
     token   scadenza   file
       │       │        │
       └───────┼────────┘
               ▼
          tutto valido?
          /          \
        SI            NO
        │              │
        ▼              ▼
      FILE            DENY
        │
        ▼
     DOWNLOAD

Questo permette di mantenere il filesystem non direttamente esposto.

17. 👤 Utente e permessi

V1 è volutamente single-user.

             LOGIN
               │
               ▼
             USER
               │
       ┌───────┴───────┐
       ▼               ▼
   MY CLOUD       MISSION CONTROL
       │
       ▼
   tutti i propri file

Non esistono:

altri utenti;
amministratori;
guest account;
gruppi;
ACL;
permessi per cartella;
condivisioni tra utenti autenticati.

Il link temporaneo è l'unica forma di condivisione prevista.

18. 🔄 Spostamento file

La possibilità di spostare file tra cartelle è prevista, ma non è una priorità della V1.

Quindi:

V1 CORE
├── Upload              ✓
├── Download            ✓
├── Delete              ✓
├── Create folder       ✓
├── Navigate folders    ✓
└── Temporary links     ✓

ESTENSIONE
└── Move file           → successivo

Questo permette di avere una V1 completa senza trasformare il file browser in un clone di Explorer.

19. 📊 Metadati

Informazioni come:

dimensione;
data caricamento;
tipo MIME;
data modifica;

non sono obbligatorie per la V1, ma possono essere presenti se risultano utili all'interfaccia.

Quindi non diventano un requisito che rischia di bloccare il progetto.

20. 🗄️ Cosa deve persistere

La persistenza può essere vista così:

                    MY CLOUD
                       │
             ┌─────────┴─────────┐
             │                   │
             ▼                   ▼
        FILESYSTEM            DATABASE
             │                   │
             │                   ├── file metadata
             │                   ├── folders
             │                   └── temporary links
             │
             └── contenuto reale

Il filesystem contiene i dati pesanti.

Il database contiene le informazioni strutturali e di gestione.

21. 🌐 Flusso completo

Una normale operazione può essere rappresentata così:

                         BROWSER
                            │
                            ▼
                     ┌─────────────┐
                     │   APACHE    │
                     └──────┬──────┘
                            │
                            ▼
                     ┌─────────────┐
                     │     PHP     │
                     │  MY CLOUD   │
                     └───┬─────┬───┘
                         │     │
                ┌────────┘     └────────┐
                ▼                       ▼
          ┌──────────┐            ┌──────────┐
          │ DATABASE │            │FILESYSTEM│
          └──────────┘            └──────────┘

PHP è quindi il punto di controllo tra browser, database e filesystem.

22. 🚫 Cosa NON fa My Cloud V1

Per mantenere il progetto realmente presentabile e affidabile:

MY CLOUD V1
│
├── ✗ Multi-user
├── ✗ RBAC
├── ✗ Sync desktop
├── ✗ Versioning
├── ✗ Cestino
├── ✗ Compressione automatica
├── ✗ Encryption-at-rest
├── ✗ Chunked upload
├── ✗ Resumable upload
├── ✗ Google Drive integration
├── ✗ Dropbox integration
├── ✗ Storage remoto
├── ✗ File preview avanzato
├── ✗ Collaborative editing
└── ✗ Raspberry Pi

Queste possono essere idee per una V2, non requisiti della demo.

23. 🧩 My Cloud + Mission Control

E qui arriva la parte interessante: non sono due programmi separati.

Sono due moduli della stessa applicazione.

                 ┌──────────────────────┐
                 │    WEB APPLICATION    │
                 │                      │
                 │  ┌────────┐ ┌──────┐ │
                 │  │MY CLOUD│ │MISSION│ │
                 │  │        │ │CONTROL│ │
                 │  └───┬────┘ └───┬──┘ │
                 │      │           │    │
                 └──────┼───────────┼────┘
                        │           │
                        ▼           ▼
                   FILESYSTEM    MONITOR
                                    │
                                    ▼
                                  DB

Un solo login.

Una sola applicazione.

Una navigazione comune.

24. 🏗️ Visione finale del progetto

Alla fine, la macchina avrà questa logica:

                         ┌───────────────────────┐
                         │       BROWSER         │
                         └───────────┬───────────┘
                                     │
                                     ▼
                         ┌───────────────────────┐
                         │        APACHE         │
                         │      WEB SERVER       │
                         └───────────┬───────────┘
                                     │
                                     ▼
                         ┌───────────────────────┐
                         │         PHP           │
                         │    WEB APPLICATION    │
                         └───────┬───────┬───────┘
                                 │       │
                    ┌────────────┘       └─────────────┐
                    ▼                                  ▼
             ┌──────────────┐                  ┌──────────────┐
             │   MY CLOUD   │                  │   MISSION    │
             │              │                  │   CONTROL    │
             └──────┬───────┘                  └──────┬───────┘
                    │                                 │
             ┌──────┴──────┐                    ┌─────┴──────┐
             ▼             ▼                    ▼            ▼
        FILESYSTEM     DATABASE             MONITOR       CONTROL
             │             ▲                    │            │
             │             │                    ▼            ▼
             │             └────────────── MySQL/MariaDB ────┘
             │
             ▼
        REAL FILES