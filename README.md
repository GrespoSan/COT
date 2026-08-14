# COT Smart Money Python V6.27

Versione Python allineata a **G. COT Smart Money Engine V1.5.48** e basata sulla V6.26.

La V6.27 non modifica il motore COT, lo Stato dello Screener, lo Score o il Weekly Change Radar. Aggiunge un livello successivo di selezione operativa e una verifica causale della shortlist della settimana precedente.

## Novità: Focus Operativo Settimanale

Nella pagina Screener sono presenti quattro schede:

1. `Classifica attuale`
2. `Cambiamenti settimanali`
3. `Focus operativo`
4. `Verifica Focus precedente`

### Candidati FOCUS

Un mercato entra nella shortlist FOCUS soltanto se:

- è `LONG CONFERMATO` o `SHORT CONFERMATO`;
- non è `CONFERMATO — NON INSEGUIRE`;
- Score >= 65;
- il prezzo Weekly conferma la stessa direzione;
- Flow 3W e 6W sono entrambi coerenti con la direzione;
- il Flow 1W non è contrario alla direzione.

Non viene forzato un numero minimo di mercati. Il massimo è 8.

La tipologia distingue:

- `PUNTO DI SVOLTA — NUOVA CONFERMA`: la direzione è appena passata a confermata rispetto al report precedente;
- `CONTINUAZIONE FORTE`: il setup era già confermato e continua a rispettare i criteri;
- `SETUP CONFERMATO`: usato quando non è disponibile un confronto ancora precedente.

### Da monitorare

Restano separati dai candidati operativi:

- `PUNTO DI SVOLTA — PREZZO ANTICIPA COT`;
- `PUNTO DI SVOLTA — REGIME IN SVILUPPO`;
- `SETUP IN MATURAZIONE`.

Questi casi possono essere interessanti, ma non vengono presentati come FOCUS finché manca la conferma completa.

## Verifica Focus precedente

La V6.27 ricostruisce il Focus che sarebbe stato selezionato sullo snapshot COT precedente e misura il movimento successivo senza hindsight.

Regola fissa:

- data di selezione: venerdì associato al report COT precedente;
- prezzo di riferimento iniziale: apertura della prima seduta successiva;
- prezzo finale: chiusura dell'ultima seduta giornaliera completamente conclusa prima del nuovo ciclo;
- il giorno corrente viene escluso quando può essere ancora aperto.

Metriche:

- `Rendimento direzionale %`: positivo se il mercato si è mosso nella direzione del Focus;
- `MFE %`: massimo movimento favorevole durante la settimana;
- `MAE %`: massimo movimento contrario;
- `Esito`: FAVOREVOLE / SFAVOREVOLE / NEUTRO.

Queste misure verificano la qualità della shortlist. Non rappresentano un backtest di entry, stop loss o target.

## Export

L'Excel completo dello Screener aggiunge:

- `Focus settimana`;
- `Focus monitorare`.

La scheda Focus dispone inoltre di un export dedicato `cot_focus_operativo_YYYY-MM-DD.xlsx` con:

- `Focus settimana`;
- `Da monitorare`;
- `Verifica precedente`.

## Invariato rispetto alla V6.26

Sono rimasti identici:

- `screener_status()`;
- `calculate_screener_score()`;
- `build_weekly_change_radar()`;
- `analyze_alignment_map()`.

Rimangono inoltre tutte le regole V1.5.48: Origine Flow 1W separata dall'OI, prezzo che anticipa il COT su Alignment 3/3, correzione Long liquidation/Short covering, OI Index 52W informativo e distinzione fra 2/3, 3/3, prezzo anticipa COT, in sviluppo e confermato.

## Nota sui dati prezzo

Il COT proviene dalla CFTC; il controllo prezzo e la verifica settimanale usano Yahoo Finance. Differenze di calendario, ticker o feed possono produrre valori non perfettamente identici a TradingView. La logica evita deliberatamente di usare barre giornaliere ancora aperte.
