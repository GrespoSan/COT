# COT Smart Money Python V6.21

Aggiornamento grafico e operativo della V6.20 dedicato al **COT Weekly Change Radar**.

## Novità V6.21

### 1. Colonna OGGI più leggibile
Nella tabella **Dove vale la pena concentrare il tempo** la colonna `Oggi` evidenzia ora:

- **LONG in verde**;
- **SHORT in rosso**;
- stati neutrali con il colore standard.

La stessa distinzione Long/Short viene mantenuta anche nel JPG del Radar e nel file Excel dedicato.

### 2. Filtri per macro-categoria
Il Weekly Change Radar dispone ora del filtro `Categoria mercati` con cinque gruppi operativi:

- **Indici**;
- **Valute**;
- **Metalli**;
- **Energetici**;
- **Resto**.

`Resto` raccoglie Tassi, Crypto CME, Agricoli, Soft e Bestiame. Il filtro è multiplo: è possibile visualizzare una o più categorie contemporaneamente.

I filtri di categoria si combinano con il filtro `Verdetto Radar` e con l'opzione per mostrare i mercati senza novità.

### 3. Export dedicati del Weekly Change Radar
La tabella operativa del Radar ha ora gli stessi export pratici della classifica principale:

- **Scarica Radar Excel**;
- **Scarica JPG Top 5**;
- **Scarica JPG Top 10**;
- **Scarica JPG Totale**.

Gli export rispettano **i filtri correnti**. In questo modo, ad esempio, selezionando `Valute + DA APPROFONDIRE` si ottiene un file che contiene soltanto quella vista operativa.

L'Excel dedicato contiene sia la sintesi del Radar sia i campi di confronto necessari: Stato, Score, flusso, prezzo Weekly e Regime 156W corrente e precedente.

### 4. Dettagli coerenti con i filtri
La tabella inferiore è stata rinominata **Dettagli del confronto filtrati** e segue gli stessi filtri applicati alla tabella operativa.

## Weekly Change Radar — logica invariata

Il Radar continua a confrontare automaticamente:

1. **snapshot corrente**: ultimo report COT + prezzo Weekly corrente disponibile;
2. **snapshot precedente**: storia COT troncata al report precedente + prezzo Weekly disponibile alla settimana di quel report.

Il prezzo precedente non usa dati futuri. Il Radar non crea un secondo punteggio: confronta lo **stesso Stato e lo stesso Score** su due snapshot consecutivi.

I quattro verdetti restano:

- **DA APPROFONDIRE**;
- **DA MONITORARE**;
- **PERDE INTERESSE**;
- **NESSUNA NOVITÀ — IGNORA**.

Le priorità e le soglie restano quelle introdotte nella V6.20:

- `🔥 NUOVA OPPORTUNITÀ CONFERMATA`;
- `⚡ SETUP CONFERMATO IN RAFFORZAMENTO`;
- `✅ SETUP CONFERMATO STABILE`;
- `⚠️ CONFERMATO MA NON INSEGUIRE`;
- `🟡 NUOVA OPPORTUNITÀ IN COSTRUZIONE`;
- `⚡ SETUP IN ACCELERAZIONE`;
- `⚠️ POSSIBILE CAMBIO DI REGIME`;
- `🔻 CONFERMATO MA IN DETERIORAMENTO`;
- `🔻 SETUP IN DETERIORAMENTO`;
- `🔻 SETUP PERSO / DETERIORAMENTO`;
- `⛔ NESSUNA NOVITÀ RILEVANTE`.

Un semplice Alignment 2/3 resta un warning e non viene promosso a opportunità operativa.

## Cosa NON cambia

La V6.21 **non modifica**:

- Smart Money Engine;
- Stato dello Screener;
- formula dello Score;
- soglie dello Score;
- logica del Weekly Change Radar;
- Alignment 156W;
- Rapid Shift;
- OI 3–6W / OI Index 52W;
- conferma prezzo Weekly;
- Analisi singolo strumento;
- prompt e logica AI, salvo l'aggiornamento del numero di versione del prompt Screener.

Le modifiche sono esclusivamente di **visualizzazione, filtro ed esportazione** del Weekly Change Radar.
