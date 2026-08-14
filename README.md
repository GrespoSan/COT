# COT Smart Money Python V6.29

Versione Python allineata a **G. COT Smart Money Engine V1.5.48** e basata sulla V6.28.

La V6.29 **non modifica il motore COT, lo Stato dello Screener, lo Score, l'analisi singola o il Weekly Change Radar**. Corregge esclusivamente la gerarchia usata per ordinare i candidati del **Focus Operativo Settimanale**.

## Correzione: Origine Flow 1W prima dello Score

Nel primo Focus reale della V6.28 era emerso un caso utile:

- **CC — Cocoa**: Score 83, miglioramento derivante soprattutto dall'**aumento dei Long**;
- **SB — Sugar**: Score 93, miglioramento derivante soprattutto dalla **chiusura degli Short**, pur con Long in aumento.

La V6.28 lasciava prevalere il segnale sintetico `NUOVI LONG` e poi lo Score, quindi SB poteva essere ordinato davanti a CC. Questo non era coerente con la lettura più precisa dell'`Origine Flow 1W`.

La V6.29 corregge il problema senza creare un nuovo Score.

### Nuova gerarchia del Focus

Per ordinare candidati già validi, la qualità dell'origine del movimento viene classificata così:

1. **nuova partecipazione reale** nella direzione del Focus;
2. **movimento misto / bilanciato**;
3. **Short covering / Long liquidation dominante**;
4. origine non classificabile.

Solo dopo vengono considerati:

- nuova conferma / continuazione;
- Score numerico;
- Δ Score;
- ordinamento alfabetico come ultimo spareggio.

La priorità settoriale resta invariata: prima viene mostrato il migliore di ogni settore (`PRINCIPALE`), poi le altre opportunità valide dello stesso comparto (`ALTERNATIVA SETTORE`).

## Segnale flusso motore: ora solo fallback

Il campo `Segnale flusso motore` resta invariato e continua a essere usato dal motore. Nel solo ordinamento Focus, però, non può più sovrascrivere una `Origine Flow 1W` esplicita.

Esempio: se il motore sintetico indica `NUOVI LONG`, ma l'Origine Flow dice che il miglioramento deriva **soprattutto dalla chiusura degli Short**, il candidato viene classificato come **covering dominante**, non come nuova partecipazione Long di massima qualità.

La logica è simmetrica sul lato Short: una **riduzione dei Long dominante** non viene promossa a nuova partecipazione Short soltanto perché il segnale motore è `NUOVI SHORT`.

## Comportamento atteso sul caso reale

Con i dati del Focus del 14/08/2026, l'ordine atteso diventa:

1. CT — Cotton — PRINCIPALE Soft;
2. 6A — Australian Dollar — PRINCIPALE Valute;
3. CC — Cocoa — ALTERNATIVA Soft;
4. SB — Sugar — ALTERNATIVA Soft.

CC precede SB perché la nuova partecipazione Long è più genuina, anche se SB ha Score numerico superiore.

## Cosa non cambia

Restano identici alla V6.28:

- requisiti per entrare in `FOCUS`;
- `LONG/SHORT CONFERMATO` e `NON INSEGUIRE`;
- soglia Score >= 65;
- conferma prezzo Weekly;
- struttura 3W/6W;
- logica `MONITORARE`;
- Focus principale per settore e alternative;
- verifica causale della settimana precedente;
- MFE, MAE e rendimento direzionale;
- Weekly Change Radar;
- export Excel e JPG.

## Verifiche effettuate

- compilazione Python (`py_compile`);
- test simmetrici Long/Short della nuova gerarchia Origine Flow: nuova partecipazione = 0, misto = 1, covering/liquidation dominante = 2;
- test sintetico del caso reale CT / 6A / CC / SB con ordine finale 1 / 2 / 3 / 4;
- confronto AST delle funzioni core per verificare che motore COT, Stato, Score e Weekly Change Radar non siano stati modificati;
- integrità del pacchetto ZIP.

## Nota sui dati

COT: CFTC. Prezzi e verifica settimanale: Yahoo Finance. Feed e calendari possono non coincidere perfettamente con TradingView; la procedura continua a escludere le barre giornaliere non ancora completate.
