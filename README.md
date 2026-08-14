# COT Smart Money Python V6.28

Versione Python allineata a **G. COT Smart Money Engine V1.5.48** e basata sulla V6.27.

La V6.28 **non modifica il motore COT, lo Stato dello Screener, lo Score, l'analisi singola o il Weekly Change Radar**. Interviene soltanto sull'ordinamento del **Focus Operativo Settimanale** per evitare che più mercati dello stesso comparto occupino automaticamente tutte le prime posizioni.

## Novità: Focus finale per settore

I requisiti per entrare in `FOCUS` restano identici alla V6.27:

- `LONG CONFERMATO` o `SHORT CONFERMATO`;
- esclusi i casi `CONFERMATO — NON INSEGUIRE`;
- Score >= 65;
- prezzo Weekly confermato nella stessa direzione;
- Flow 3W e 6W coerenti;
- Flow 1W non contrario.

La V6.28 **non crea un nuovo mega-score**. I candidati già validi vengono ordinati in modo deterministico usando, nell'ordine:

1. nuova conferma / continuazione;
2. fascia qualitativa dello Score già esistente;
3. qualità dell'`Origine Flow 1W` rispetto alla direzione;
4. Score numerico;
5. Δ Score;
6. diversificazione del tempo di analisi per settore.

## PRINCIPALE e ALTERNATIVA SETTORE

Dopo l'ordinamento di base:

- il candidato migliore di ogni categoria diventa `PRINCIPALE`;
- gli altri candidati FOCUS dello stesso comparto diventano `ALTERNATIVA SETTORE`;
- tutte le prime scelte settoriali vengono mostrate prima delle alternative;
- le alternative **non vengono scartate** e conservano la loro piena validità COT.

La logica serve a decidere **quale grafico guardare per primo**, non a modificare la view di mercato.

Sono ora disponibili due campi distinti:

- `Ordine Focus`: graduatoria operativa vera 1, 2, 3... dopo la priorità settoriale;
- `Ordine settore`: posizione del mercato all'interno del proprio comparto.

Il massimo resta 8 candidati FOCUS complessivi e non viene mai forzato un numero minimo.

## Interfaccia Focus

La scheda `Focus operativo` è divisa in:

1. **Focus principali — prima scelta per settore**;
2. **Alternative valide dello stesso settore**;
3. **Punti di svolta interessanti, ma non ancora maturi**.

Questo rende esplicito che, per esempio, tre Soft commodity contemporaneamente valide non devono necessariamente essere i primi tre grafici da analizzare.

## Verifica della settimana precedente

La verifica causale resta identica nei prezzi e nelle metriche, ma ora conserva anche:

- `Ordine Focus`;
- `Ruolo settore`;
- `Categoria`.

In questo modo, dopo un numero sufficiente di settimane, sarà possibile confrontare separatamente la performance delle **prime scelte settoriali** e delle **alternative**, senza modificare retroattivamente la selezione.

Restano invariati:

- prezzo di riferimento = apertura della prima seduta successiva al report;
- uscita di verifica = ultima seduta giornaliera completata prima del ciclo successivo;
- `Rendimento direzionale %`;
- `MFE %`;
- `MAE %`;
- `Esito`.

Queste metriche non sono target o stop loss.

## Export Excel

L'Excel dedicato del Focus contiene ora:

- `Focus settimana` — tutti i candidati FOCUS;
- `Focus principali` — una prima scelta per settore;
- `Alternative settore` — gli altri setup validi dello stesso comparto;
- `Da monitorare`;
- `Verifica precedente`.

Anche l'Excel generale dello Screener aggiunge `Focus principali` e `Alternative settore`, mantenendo i fogli già esistenti.

## Funzioni del motore verificate come invariate

Rispetto alla V6.27 risultano identiche a livello AST:

- `analyze_smart_money()`;
- `screener_status()`;
- `calculate_screener_score()`;
- `build_weekly_change_radar()`;
- `analyze_alignment_map()`.

La V6.28 modifica esclusivamente il modulo Focus, i relativi export e la descrizione nei prompt.

## Nota sui dati

COT: CFTC. Prezzi e verifica settimanale: Yahoo Finance. Feed e calendari possono non coincidere perfettamente con TradingView; la procedura continua a escludere le barre giornaliere non ancora completate.
