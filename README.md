# COT Smart Money Python V6.38

Base: V6.37. Questa versione aggiunge un replay storico causale per verificare quando un segnale REVERSAL WATCH sarebbe apparso realmente e rende più leggibili le spiegazioni delle metriche nella sezione Timing Price Action.

## Novità V6.38

### Replay storico — nessun hindsight
Nuova scheda `Replay storico` nello Screener.

- Selezione del mercato (default: `6N — New Zealand Dollar`).
- Numero di report ricostruiti configurabile da 4 a 30 (default 12).
- Ogni riga viene calcolata come uno snapshot point-in-time indipendente.
- Lo storico COT viene troncato al report analizzato.
- Il prezzo Weekly e il prezzo Daily/EMA21 vengono troncati al venerdì associato a quel report.
- Anche lo snapshot precedente usato dalle regole di cambiamento viene ricostruito senza dati futuri.
- Il `3/3 recente` guarda solo report precedenti allo snapshot corrente.
- La tabella mostra Stato, Score, Alignment, Daily21, Reversal Watch, Decisione/Priorità di watchlist e Origine Flow.
- La prima comparsa di `REVERSAL WATCH` nel periodo ricostruito viene evidenziata.

Questo permette di rispondere in modo oggettivo alla domanda: “al 28/07, 04/08, 11/08, usando solo ciò che era disponibile allora, 6N sarebbe già entrato in REVERSAL WATCH?”.

### Timing Price Action — spiegazioni su righe separate
Le spiegazioni a video sono ora separate in caption distinte:

- `Rend. passivo %`
- `Rend. PA %`
- `Δ Rend. PA`
- `MAE passivo % / MAE PA %`
- `Δ MAE PA`
- `MFE passivo % / MFE PA %`
- nota finale MFE/MAE

Le spiegazioni MFE/MAE della `Verifica Focus precedente` restano anch'esse su tre righe separate.

## Logica invariata
Non sono state modificate le funzioni validate di:

- Stato Screener
- Score Screener
- Alignment Map
- Weekly Change Radar
- Focus Operativo
- Verifica Focus precedente
- Price Action Timing

Il Replay storico è un modulo diagnostico separato e non cambia Focus, Stato o Score.
