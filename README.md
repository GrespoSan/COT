# COT Smart Money Python V6.36

## Novità V6.36 — Watchlist 2/3 pre-prezzo + tabelle verifica più leggibili

La V6.36 mantiene il motore Smart Money, lo Stato, lo Score, il Weekly Change Radar, il Focus e il Price Action Timing della V6.35, ma aggiunge una regola mirata alla watchlist e riordina le due tabelle di verifica.

### 1. Alignment 2/3 pre-prezzo

La Daily21 resta la conferma prezzo anticipata e la Weekly21 resta la conferma strutturale. Tuttavia un 2/3 può ora entrare in **MONITORARE anche prima della Daily21** quando il COT mostra un cambio significativo e causale rispetto alla settimana precedente.

La regola è volutamente stretta e simmetrica:

- esiste un Alignment 156W **2/3** nella nuova direzione;
- la settimana precedente esisteva un setup direzionale opposto **CONFERMATO o IN COSTRUZIONE**;
- quel setup ha perso la precedente direzione;
- lo Score è diminuito di almeno **20 punti**;
- il Flow 1W si muove nella direzione del nuovo 2/3.

Il risultato è soltanto **MONITORARE**:

- bearish: `COT IN DETERIORAMENTO — PREZZO NON CONFERMA`;
- bullish: `COT IN MIGLIORAMENTO — PREZZO NON CONFERMA`.

Non cambia Stato o Score. Se in seguito la Daily21 diventa coerente, il mercato sale di priorità nella watchlist come `COT 2/3 + DAILY21`. Questa regola copre il caso tipo Copper/HG senza trasformare un semplice 2/3 in un segnale Short/Long.

### 2. Confermato sotto soglia Focus

Resta la regola V6.35: un LONG/SHORT CONFERMATO, non `NON INSEGUIRE`, con Score **50–64** compare in `Da monitorare` come `CONFERMATO SOTTO SOGLIA FOCUS`. La soglia FOCUS resta 65.

## Tabelle Verifica Focus e Timing Price Action

La tabella **Verifica Focus precedente** è ora mostrata in questo ordine:

1. Strumento
2. Direzione
3. Tipo
4. Esito
5. Rendimento dir. %
6. Stato attuale
7. Score attuale
8. Report Focus
9. Data ingresso
10. Apertura riferimento
11. Data uscita
12. Chiusura riferimento
13. MFE %
14. MAE %

Sotto la tabella viene spiegato che:

- **MFE %** = Maximum Favorable Excursion, massimo movimento percentuale a favore della direzione dopo l’ingresso;
- **MAE %** = Maximum Adverse Excursion, massimo movimento percentuale contro la direzione dopo l’ingresso, mostrato negativo.

MFE e MAE non sono rendimento realizzato, target o stop loss.

La tabella **Timing Price Action — test** segue ora questo ordine:

1. Strumento
2. Direzione
3. Stato Timing PA
4. Esito PA
5. Data inizio pullback
6. Data segnale PA
7. Data ingresso PA
8. Ingresso PA
9. Sedute attesa
10. Rend. passivo %
11. Rend. PA %
12. Δ Rend. PA
13. MAE passivo %
14. MAE PA %
15. Δ MAE PA
16. MFE passivo %
17. MFE PA %

Sotto la tabella sono spiegati rendimento passivo/PA, differenza di rendimento, MAE passivo/PA, Δ MAE e MFE passivo/PA. Un **Δ MAE positivo** significa che il Timing PA ha ridotto l’escursione contraria; negativo significa peggioramento.

## Excel settimanale

`cot_weekly_report_YYYY-MM-DD.xlsx` mantiene 7 fogli:

1. Focus settimana
2. Focus principali
3. Alternative settore
4. Da monitorare
5. Verifica precedente
6. Timing Price Action
7. Radar completo

Nei fogli `Verifica precedente` e `Timing Price Action` le colonne sono nello stesso ordine delle tabelle Streamlit e, sotto i dati, è presente una legenda testuale delle metriche MFE/MAE e del confronto PA.

## Cosa resta invariato

- motore Smart Money allineato a TradingView G. COT Smart Money Engine V1.5.48;
- Stato e Score dello Screener, salvo la già esistente logica Daily21 V6.35;
- soglia Focus 65 e massimo 8 candidati;
- priorità settoriale PRINCIPALE / ALTERNATIVA SETTORE;
- ordinamento Focus basato sulla qualità reale dell’Origine Flow;
- Weekly Change Radar;
- benchmark Verifica Focus precedente;
- regola del Price Action Timing V6.34;
- esclusione HO — Heating Oil e ZO — Oats;
- refresh cache CFTC a ogni nuova scansione.

## Dati

COT: CFTC. Prezzi Weekly e Daily: Yahoo Finance. I ticker continui Yahoo possono differire per roll rispetto a TradingView/broker; le letture prezzo sono filtri di contesto e ricerca, non livelli eseguibili.
