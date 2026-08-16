# COT Smart Money Python V6.34

## Novità V6.34 — Price Action Timing sperimentale

La V6.34 aggiunge un **esperimento parallelo di timing Daily** alla verifica del Focus precedente. Il modulo non entra nel motore COT e non modifica **Focus, Stato, Score, Direzione, Alignment 156W o Weekly Change Radar**.

L'obiettivo è misurare in modo causale una domanda precisa: **dopo che il COT ha scelto mercato e direzione, attendere la fine di un pullback/rimbalzo migliora il timing rispetto all'ingresso passivo alla prima apertura della settimana?**

### Regola deterministica

Per un Focus **LONG**:

1. dopo il venerdì associato al report, il pullback si arma solo quando una seduta Daily completata chiude sotto la chiusura precedente **oppure** fa un minimo inferiore al minimo precedente;
2. da una seduta successiva, serve una chiusura **sopra il massimo della seduta precedente**;
3. il segnale nasce quindi solo a fine giornata;
4. l'ingresso teorico avviene all'**Open della seduta successiva**.

Per un Focus **SHORT** la logica è speculare: rimbalzo con Close > Close precedente oppure High > High precedente, poi una seduta successiva con Close < Low precedente e ingresso all'Open successivo.

La stessa candela non può creare il pullback e contemporaneamente autorizzare l'ingresso. Se il segnale arriva sull'ultima seduta disponibile e manca una successiva apertura completata, viene registrato **SEGNALE SENZA ENTRY**. Se non compare un pullback o non arriva la conferma, il modulo registra **NESSUN INGRESSO**: non viene scelto retroattivamente un punto migliore sul grafico.

### Confronto con il benchmark passivo

Il foglio/tab **Verifica precedente** resta invariato e continua a usare il benchmark neutrale:

- ingresso = Open della prima seduta disponibile dopo il venerdì associato al report Focus;
- uscita = Close dell'ultima seduta giornaliera completamente chiusa prima del nuovo ciclo;
- metriche = rendimento direzionale, MFE e MAE.

La nuova sezione **Timing Price Action — test** confronta, sugli stessi Focus precedenti:

- rendimento passivo vs rendimento PA;
- MFE passivo vs MFE PA;
- MAE passivo vs MAE PA;
- differenza di rendimento in punti percentuali;
- miglioramento/peggioramento del MAE;
- numero di sedute attese prima dell'ingresso;
- casi in cui il timing non avrebbe generato alcun trade.

Questo è intenzionale: un mercato che parte subito senza ritracciare deve risultare **NESSUN PULLBACK**, perché anche il mancato ingresso è parte del test.

## Report settimanale Excel unico

`cot_weekly_report_YYYY-MM-DD.xlsx` contiene ora 7 fogli, nell'ordine:

1. **Focus settimana**
2. **Focus principali**
3. **Alternative settore**
4. **Da monitorare**
5. **Verifica precedente**
6. **Timing Price Action**
7. **Radar completo**

Il foglio **Radar completo** continua a contenere l'intero universo analizzato e non dipende dai filtri della schermata Radar.

## Stato del modulo

Il Price Action Timing è volutamente marcato **esperimento**. Non simula stop loss o target e non è ancora una condizione operativa del Focus. Prima di promuoverlo a regola di entrata servono molte osservazioni fuori campione; il suo scopo attuale è accumulare dati senza hindsight.

## Cosa resta invariato dalla V6.33

- motore Smart Money allineato a TradingView G. COT Smart Money Engine V1.5.48;
- Stato e Direzione Screener;
- Score e Qualità;
- Alignment / Regime 156W e `Prezzo anticipa COT`;
- Weekly Change Radar;
- criteri e ordinamento Focus V6.29;
- priorità settoriale PRINCIPALE / ALTERNATIVA SETTORE;
- benchmark della Verifica Focus precedente;
- esclusione di HO — Heating Oil e ZO — Oats;
- aggiornamento forzato della cache CFTC a ogni nuova scansione.

## Dati

COT: CFTC. Prezzi Weekly e Daily: Yahoo Finance. Il giorno corrente viene escluso dalla verifica quando può essere ancora aperto. I ticker continui Yahoo possono avere differenze di roll rispetto a TradingView/broker; per questo il timing viene usato come ricerca comparativa, non come livello eseguibile.
