<?php
declare(strict_types=1);

/**
 * UnaIdeaCrazy — OcchioDiFalco Web Server
 * Landing Page principale per l'accesso ai 3 servizi:
 * 1. Health Checker & OcchioDiFalco (/occhio-di-falco/)
 * 2. My Cloud / FTP File Server (/my-cloud/)
 * 3. Discovery Server / Web Server Provider (/discovery-server/)
 */

// -------------------------------------------------------------------------
// Rilevamento rapido stato sistema e servizi locali
// -------------------------------------------------------------------------
$hostname     = gethostname() ?: 'localhost';
$serverIp     = $_SERVER['SERVER_ADDR'] ?? '127.0.0.1';
$serverPort   = $_SERVER['SERVER_PORT'] ?? '80';
$phpVersion   = PHP_VERSION;
$phpSapi      = PHP_SAPI;
$osFamily     = PHP_OS_FAMILY;
$osVersion    = php_uname('s') . ' ' . php_uname('r');
$serverSoft   = $_SERVER['SERVER_SOFTWARE'] ?? 'Apache/2.4 (Win64)';
$currentTime  = date('d/m/Y H:i:s');

// Controllo stato porta TCP (es. MySQL 3306) con timeout ridotto per non bloccare il rendering
function checkTcpPort(string $host, int $port, float $timeout = 0.15): bool {
    $errno = 0;
    $errstr = '';
    $conn = @fsockopen($host, $port, $errno, $errstr, $timeout);
    if (is_resource($conn)) {
        fclose($conn);
        return true;
    }
    return false;
}

$mysqlOnline = checkTcpPort('127.0.0.1', 3306);

// Verifica se le sottocartelle dei servizi sono già presenti
$odfDirExists       = is_dir(__DIR__ . DIRECTORY_SEPARATOR . 'occhio-di-falco');
$cloudDirExists     = is_dir(__DIR__ . DIRECTORY_SEPARATOR . 'my-cloud');
$discoveryDirExists = is_dir(__DIR__ . DIRECTORY_SEPARATOR . 'discovery-server');
$pmaDirExists       = is_dir(__DIR__ . DIRECTORY_SEPARATOR . 'phpmyadmin');
?>
<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>UnaIdeaCrazy — OcchioDiFalco Portal</title>
    <link rel="stylesheet" href="style-root/landing.css">
</head>
<body>

    <!-- Top Navigation & Live Service Badges -->
    <header class="topbar">
        <div class="brand">
            <div class="brand-logo" aria-hidden="true">🦅</div>
            <div class="brand-text">
                <h1>UnaIdeaCrazy · OcchioDiFalco</h1>
                <span>Host: <?= htmlspecialchars($hostname) ?> (<?= htmlspecialchars($serverIp . ':' . $serverPort) ?>)</span>
            </div>
        </div>

        <div class="status-pills">
            <div class="pill pill-online" title="Apache HTTP Server è attivo e sta servendo questa pagina">
                <span class="dot dot-green"></span>
                Apache HTTP · ONLINE
            </div>

            <?php if ($mysqlOnline): ?>
                <div class="pill pill-online" title="Connessione socket su 127.0.0.1:3306 riuscita">
                    <span class="dot dot-green"></span>
                    MySQL :3306 · ONLINE
                </div>
            <?php else: ?>
                <div class="pill pill-offline" title="Porta 127.0.0.1:3306 non raggiungibile">
                    <span class="dot dot-red"></span>
                    MySQL :3306 · OFFLINE
                </div>
            <?php endif; ?>

            <div class="pill" title="Versione PHP caricata in Apache">
                🐘 PHP <?= htmlspecialchars($phpVersion) ?>
            </div>
        </div>
    </header>

    <!-- Main Content -->
    <main class="container">
        <section class="hero">
            <span class="hero-badge">Portale Servizi Locali</span>
            <h2>Seleziona il Servizio</h2>
            <p>
                Accedi agli strumenti di diagnostica e monitoraggio hardware della macchina ospitante,
                gestisci i tuoi file tramite lo storage cloud locale oppure esplora i siti ospitati dal Discovery Server.
            </p>
        </section>

        <!-- Three Distinct Services Grid -->
        <section class="services-grid">

            <!-- SERVIZIO 1: HEALTH CHECKER / OCCHIO DI FALCO -->
            <a href="/occhio-di-falco/" class="service-card card-health">
                <div>
                    <div class="card-header">
                        <div class="card-icon icon-health" aria-hidden="true">🩺</div>
                        <span class="card-tag">
                            <?= $odfDirExists ? 'Servizio #1 · Attivo' : 'Servizio #1 · Health Monitor' ?>
                        </span>
                    </div>

                    <div class="card-body">
                        <h3>Server Health Checker</h3>
                        <p>
                            Pannello di controllo e telemetria hardware della macchina ospitante.
                            Verifica in tempo reale lo stato dei processi, l'utilizzo di CPU, RAM, rete e il registro eventi.
                        </p>

                        <ul class="feature-list">
                            <li>
                                <span class="bullet">📊</span>
                                <span>Telemetria real-time CPU, RAM e banda di rete (Download / Upload)</span>
                            </li>
                            <li>
                                <span class="bullet">⚙️</span>
                                <span>Controllo stato processi e PID di Apache, MySQL e orchestratore Python</span>
                            </li>
                            <li>
                                <span class="bullet">🚨</span>
                                <span>Log eventi cronologico e notifiche per anomalie o servizi offline</span>
                            </li>
                        </ul>
                    </div>
                </div>

                <div class="card-footer">
                    <code class="route-code">/occhio-di-falco/</code>
                    <span class="btn-launch btn-blue">
                        Apri Health Checker →
                    </span>
                </div>
            </a>

            <!-- SERVIZIO 2: FTP / MY CLOUD -->
            <a href="/my-cloud/" class="service-card card-cloud">
                <div>
                    <div class="card-header">
                        <div class="card-icon icon-cloud" aria-hidden="true">☁️</div>
                        <span class="card-tag">
                            <?= $cloudDirExists ? 'Servizio #2 · Attivo' : 'Servizio #2 · Cloud & FTP' ?>
                        </span>
                    </div>

                    <div class="card-body">
                        <h3>My Cloud · File Server</h3>
                        <p>
                            Spazio di archiviazione e file server locale per il trasferimento,
                            l'organizzazione in cartelle e la condivisione sicura dei file ospitati sul server.
                        </p>

                        <ul class="feature-list">
                            <li>
                                <span class="bullet">📁</span>
                                <span>Esplorazione directory, creazione cartelle e sottocartelle</span>
                            </li>
                            <li>
                                <span class="bullet">⬆️</span>
                                <span>Upload, download protetto da PHP ed eliminazione rapida dei file</span>
                            </li>
                            <li>
                                <span class="bullet">🔗</span>
                                <span>Generazione di link temporanei di condivisione con scadenza configurabile</span>
                            </li>
                        </ul>
                    </div>
                </div>

                <div class="card-footer">
                    <code class="route-code">/my-cloud/</code>
                    <span class="btn-launch btn-green">
                        Accedi al Cloud →
                    </span>
                </div>
            </a>

            <!-- SERVIZIO 3: DISCOVERY SERVER (WEB SERVER PROVIDER) -->
            <a href="/discovery-server/" class="service-card card-discovery">
                <div>
                    <div class="card-header">
                        <div class="card-icon icon-discovery" aria-hidden="true">🧭</div>
                        <span class="card-tag">
                            <?= $discoveryDirExists ? 'Servizio #3 · Attivo' : 'Servizio #3 · Web Provider' ?>
                        </span>
                    </div>

                    <div class="card-body">
                        <h3>Discovery Server</h3>
                        <p>
                            Web Server Provider locale che scansiona ed elenca automaticamente tutti i siti
                            e i progetti web caricati all'interno della propria cartella dedicata.
                        </p>

                        <ul class="feature-list">
                            <li>
                                <span class="bullet">🌐</span>
                                <span>Catalogo automatico di tutti i siti web presenti nella directory</span>
                            </li>
                            <li>
                                <span class="bullet">🚀</span>
                                <span>Accesso rapido e lancio immediato dei singoli progetti ospitati</span>
                            </li>
                            <li>
                                <span class="bullet">🗂️</span>
                                <span>Rilevamento entrypoint (`index.php` / `index.html`) e metadati sito</span>
                            </li>
                        </ul>
                    </div>
                </div>

                <div class="card-footer">
                    <code class="route-code">/discovery-server/</code>
                    <span class="btn-launch btn-purple">
                        Esplora Siti Web →
                    </span>
                </div>
            </a>

        </section>

        <!-- Quick Host Machine Snapshot -->
        <section class="telemetry-panel" aria-label="Riepilogo rapido macchina ospitante">
            <div class="telemetry-item">
                <span class="telemetry-label">Sistema Operativo Host</span>
                <span class="telemetry-value"><?= htmlspecialchars($osFamily . ' (' . $osVersion . ')') ?></span>
            </div>

            <div class="telemetry-item">
                <span class="telemetry-label">Web Server &amp; SAPI</span>
                <span class="telemetry-value"><?= htmlspecialchars($serverSoft . ' · ' . $phpSapi) ?></span>
            </div>

            <div class="telemetry-item">
                <span class="telemetry-label">Timestamp Server</span>
                <span class="telemetry-value"><?= htmlspecialchars($currentTime) ?></span>
            </div>
        </section>
    </main>

    <!-- Footer -->
    <footer class="footer">
        <div>
            <strong>UnaIdeaCrazy</strong> · OcchioDiFalco Web Server (`127.0.0.1`)
        </div>
        <div class="footer-links">
            <a href="/occhio-di-falco/">🩺 Health Checker</a>
            <span>·</span>
            <a href="/my-cloud/">☁️ My Cloud</a>
            <span>·</span>
            <a href="/discovery-server/">🧭 Discovery Server</a>
            <?php if ($pmaDirExists): ?>
                <span>·</span>
                <a href="/phpmyadmin/">🗄️ phpMyAdmin</a>
            <?php endif; ?>
        </div>
    </footer>

</body>
</html>
