# COT Smart Money Python V6.20

Aggiornamento funzionale della V6.19: aggiunto il **COT Weekly Change Radar** nello Screener.

## Obiettivo

Lo Screener continua a rispondere a **“com'è il mercato adesso?”**.
Il nuovo Radar risponde invece a **“cosa è cambiato rispetto al report precedente e dove vale la pena concentrare il tempo?”**.

Non viene creato un secondo punteggio. Il Radar confronta lo **stesso Stato e lo stesso Score** su due snapshot consecutivi.

## Confronto automatico senza hindsight

Per ogni mercato la scansione costruisce automaticamente:

1. **snapshot corrente**: ultimo report COT + prezzo Weekly corrente disponibile;
2. **snapshot precedente**: storia COT troncata prima dell'ultimo report + prezzo Weekly disponibile alla settimana del report precedente.

Il prezzo precedente non usa il prezzo attuale. Anche EMA21 e conferma Weekly sono quindi valutate con le informazioni disponibili allora.

Per evitare che il vecchio report venga penalizzato come “datato”, il motore storico usa come data di analisi il venerdì normalmente associato al report COT del martedì.

## Nuova sottosezione Screener

Lo Screener ora presenta due tab:

- **Classifica attuale**
- **Cambiamenti settimanali**

La seconda contiene il **COT Weekly Change Radar**.

## Verdetti operativi del Radar

Ogni mercato riceve uno dei quattro verdetti:

- **DA APPROFONDIRE** — merita di aprire l'analisi singola e poi verificare il grafico;
- **DA MONITORARE** — cambiamento interessante ma non ancora sufficientemente maturo;
- **PERDE INTERESSE** — il setup si è deteriorato rispetto alla settimana precedente;
- **NESSUNA NOVITÀ — IGNORA** — nessun cambiamento sufficiente a giustificare altro tempo di analisi questa settimana.

## Priorità riconosciute

Il Radar distingue, tra gli altri:

- `🔥 NUOVA OPPORTUNITÀ CONFERMATA`
- `⚡ SETUP CONFERMATO IN RAFFORZAMENTO`
- `✅ SETUP CONFERMATO STABILE`
- `⚠️ CONFERMATO MA NON INSEGUIRE`
- `🟡 NUOVA OPPORTUNITÀ IN COSTRUZIONE`
- `⚡ SETUP IN ACCELERAZIONE`
- `⚠️ POSSIBILE CAMBIO DI REGIME`
- `🔻 CONFERMATO MA IN DETERIORAMENTO`
- `🔻 SETUP IN DETERIORAMENTO`
- `🔻 SETUP PERSO / DETERIORAMENTO`
- `⛔ NESSUNA NOVITÀ RILEVANTE`

Un semplice Alignment 2/3 resta un warning e **non** viene promosso a opportunità operativa.
Un `CONFERMATO — NON INSEGUIRE` resta in watchlist ma non viene classificato come opportunità da inseguire.

## Soglie del confronto

Il Radar usa il Δ Score solo come indicatore di cambiamento, non come nuovo Score:

- setup già confermato: **+10** = rafforzamento significativo;
- setup in costruzione: **+15** = accelerazione significativa;
- qualsiasi setup direzionale: **-15** = deterioramento significativo;
- Score corrente **≥ 50** è la soglia usata per distinguere un setup confermato da approfondire da uno da monitorare con maggiore prudenza.

Le transizioni di Stato, il nuovo flusso coerente, la nuova conferma prezzo e l'avanzamento del Regime 156W possono rendere significativo il cambiamento anche senza superare una soglia di Δ Score.

## Tabella Radar

La vista principale mostra:

- Priorità
- Strumento
- Settimana precedente
- Oggi
- Δ Score
- Cosa è cambiato
- Verdetto
- Lettura operativa

È disponibile anche una tabella dettagliata con Stato, flusso, prezzo Weekly e Regime 156W corrente e precedente.

Per impostazione predefinita vengono nascosti i mercati `NESSUNA NOVITÀ — IGNORA`, così il Radar funziona come filtro del tempo di analisi.

## Export Excel

Il file Excel dello Screener include ora anche il foglio:

- `Weekly Change Radar`

oltre ai fogli già presenti nella V6.19.

## Cosa NON cambia

La V6.20 non modifica la logica corrente di:

- Smart Money Engine;
- Stato dello Screener;
- Score;
- Alignment 156W;
- Rapid Shift;
- OI 3–6W / OI Index 52W;
- conferma prezzo Weekly;
- Analisi singolo strumento.

Il Radar è un livello comparativo aggiuntivo costruito sopra gli stessi risultati deterministici.
