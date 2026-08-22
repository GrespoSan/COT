# COT Smart Money Python V6.35

## Novità V6.35 — Daily21 anticipata + watchlist confermati sotto soglia

La V6.35 introduce due modifiche mirate allo Screener/Focus senza cambiare il motore Smart Money TradingView V1.5.48.

### 1. EMA21 Daily alla chiusura della settimana

La V6.35 separa il prezzo in due livelli:

- **Prezzo Weekly / EMA21 Weekly** = conferma strutturale;
- **Prezzo Daily21** = conferma anticipata, calcolata sull'ultima seduta disponibile della settimana del report COT.

Se il venerdì è festivo viene usata l'ultima seduta disponibile prima del cutoff. Il calcolo è causale anche per lo snapshot precedente.

Nuova colonna: **Daily21 + Alignment**.

Regole:

- **Alignment 2/3 + Daily21 coerente** → resta un warning. Non cambia Stato o Direzione, ma entra in **MONITORARE** come `COT 2/3 + DAILY21`;
- **Alignment 3/3 + Daily21 coerente** → può diventare `LONG/SHORT IN COSTRUZIONE` anticipato;
- **CONFERMATO** continua a richiedere le condizioni complete del motore; la Weekly21 resta la conferma strutturale;
- il contributo Daily21 allo Score prezzo è inferiore a quello della Weekly, così l'anticipazione non domina la classificazione.

La logica serve a evitare che una EMA21 Weekly troppo lenta faccia perdere completamente i turning point, senza trasformare ogni 2/3 in un segnale operativo.

### 2. Confermato sotto soglia Focus

Un mercato `LONG/SHORT CONFERMATO` con **Score 50–64** e non `NON INSEGUIRE` non viene più perso tra Focus e watchlist.

Ora compare in **Da monitorare** come:

`SETUP CONFERMATO SOTTO SOGLIA FOCUS`

La soglia vera del Focus resta **65**. Questa modifica risolve il caso tipo 6N: il setup è confermato ma non abbastanza forte per entrare tra i Focus principali.

### Ordine della watchlist

Nella sezione MONITORARE la maturità del motivo viene ora prima della qualità del Flow:

1. confermato sotto soglia Focus;
2. regime 156W in sviluppo;
3. prezzo Weekly che anticipa COT;
4. 3/3 + Daily21;
5. 2/3 + Daily21;
6. setup generico in maturazione.

In questo modo un warning importante non viene nascosto da setup meno maturi con un Flow 1W più pulito.

## Cosa resta invariato

- motore Smart Money allineato a TradingView G. COT Smart Money Engine V1.5.48;
- logica Flow Origin V1.5.48;
- soglia Focus 65 e massimo 8 candidati;
- priorità settoriale PRINCIPALE / ALTERNATIVA SETTORE;
- ordinamento del Focus V6.29 basato prima sulla qualità reale dell'Origine Flow;
- Weekly Change Radar come confronto causale tra report;
- benchmark Verifica Focus precedente;
- Price Action Timing V6.34 come esperimento parallelo;
- report Excel unico con Focus, verifica, Timing Price Action e Radar completo;
- esclusione di HO — Heating Oil e ZO — Oats;
- refresh cache CFTC a ogni nuova scansione.

## Report settimanale Excel

`cot_weekly_report_YYYY-MM-DD.xlsx` mantiene 7 fogli:

1. Focus settimana
2. Focus principali
3. Alternative settore
4. Da monitorare
5. Verifica precedente
6. Timing Price Action
7. Radar completo

Le tabelle Focus e Radar includono ora anche **Prezzo Daily21** e **Daily21 + Alignment**.

## Price Action Timing

Resta un test indipendente dal Focus. La nuova Daily21 non sostituisce il modulo di timing: Daily21 serve a classificare la maturazione del quadro settimanale, mentre Price Action Timing studia il momento di ingresso Daily dopo che un mercato è già entrato nel Focus.

## Dati

COT: CFTC. Prezzi Weekly e Daily: Yahoo Finance. I ticker continui Yahoo possono differire per roll rispetto a TradingView/broker; le letture prezzo sono quindi filtri di contesto e ricerca, non livelli eseguibili.
