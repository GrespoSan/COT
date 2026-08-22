# COT Smart Money Python V6.37

## Novità V6.37 — Reversal Watch con memoria 3/3 + spiegazioni metriche più leggibili

La V6.37 mantiene invariati motore Smart Money, Stato, Score, Weekly Change Radar, Focus confermato, Verifica Focus e algoritmo del Price Action Timing della V6.36. Aggiunge soltanto una nuova regola di **MONITORARE** e migliora la leggibilità delle spiegazioni MFE/MAE a video e nell’Excel.

### 1. REVERSAL WATCH — memoria del 3/3 recente

Per evitare di perdere casi come 6N, il sistema conserva una memoria causale dei **6 report precedenti**. Un mercato entra in `MONITORARE` come:

`⚠️ PREZZO ANTICIPA COT — REVERSAL WATCH`

soltanto quando sono vere insieme queste condizioni:

- almeno uno dei 6 report precedenti aveva un Alignment contrarian **3/3** nella direzione del reversal;
- la categoria seguita (Managed Money / Leveraged Funds) è **ancora all’estremo 156W opposto**;
- la chiusura del venerdì è già coerente con il reversal rispetto alla **EMA21 Daily**;
- il regime contrarian non è già completamente confermato.

Il 3/3 **non deve essere ancora presente nel report corrente**. È proprio questo il punto: il prezzo può iniziare a girare mentre il COT resta ancora estremo e l’Alignment 3/3 si è già dissolto.

Questa regola:

- non cambia `Stato`;
- non cambia `Score`;
- non crea un `FOCUS`;
- non è un ingresso automatico;
- serve soltanto a far comparire prima il mercato nella watchlist.

La regola 2/3 pre-prezzo della V6.36 resta attiva e separata.

### 2. Confermato sotto soglia Focus

Resta invariata la regola introdotta per il caso tipo 6N: un LONG/SHORT CONFERMATO, non `NON INSEGUIRE`, con Score **50–64** compare in `Da monitorare` come `CONFERMATO SOTTO SOGLIA FOCUS`. La soglia FOCUS resta 65.

## Verifica Focus — spiegazione MFE/MAE

Sotto la tabella la spiegazione è ora spezzata su tre righe:

**MFE % (Maximum Favorable Excursion)** = massimo movimento percentuale raggiunto A FAVORE della direzione Focus dopo l’ingresso.

**MAE % (Maximum Adverse Excursion)** = massimo movimento percentuale raggiunto CONTRO la direzione Focus dopo l’ingresso; viene mostrato negativo.

**MFE e MAE** descrivono il percorso del prezzo durante la settimana: non sono rendimento realizzato, target o stop loss.

## Timing Price Action — spiegazione più leggibile

Anche la legenda sotto la tabella Timing Price Action è ora su righe separate:

- rendimento passivo / rendimento PA / differenza di rendimento;
- MAE passivo / MAE PA / differenza MAE;
- MFE passivo / MFE PA;
- nota finale: MFE e MAE descrivono il percorso del prezzo e non sono rendimento realizzato, target o stop loss.

## Excel settimanale

`cot_weekly_report_YYYY-MM-DD.xlsx` mantiene 7 fogli:

1. Focus settimana
2. Focus principali
3. Alternative settore
4. Da monitorare
5. Verifica precedente
6. Timing Price Action
7. Radar completo

Nei fogli `Verifica precedente` e `Timing Price Action` la legenda in fondo è aggiornata con la stessa formulazione più chiara utilizzata a video.

## Cosa resta invariato

- motore Smart Money allineato a TradingView G. COT Smart Money Engine V1.5.48;
- Stato e Score dello Screener;
- soglia Focus 65 e massimo 8 candidati;
- priorità settoriale PRINCIPALE / ALTERNATIVA SETTORE;
- ordinamento Focus basato sulla qualità reale dell’Origine Flow;
- Weekly Change Radar;
- benchmark Verifica Focus precedente;
- algoritmo del Price Action Timing V6.34;
- Daily21 anticipatoria e Weekly21 strutturale;
- warning 2/3 pre-prezzo V6.36;
- esclusione HO — Heating Oil e ZO — Oats;
- refresh cache CFTC a ogni nuova scansione.

## Dati

COT: CFTC. Prezzi Weekly e Daily: Yahoo Finance. I ticker continui Yahoo possono differire per roll rispetto a TradingView/broker; le letture prezzo sono filtri di contesto e ricerca, non livelli eseguibili.
