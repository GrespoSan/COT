# COT Smart Money Python V6.39

Base: V6.38. Questa versione rende misurabili i segnali anticipatori nel Replay storico e più visibili nella watchlist, senza modificare Stato, Score o criteri del Focus.

## Novità V6.39

### Replay storico: EARLY WARNING vs REVERSAL WATCH
Il Replay ora distingue tre livelli:

- `WARNING BASE`: semplice `2/3 + Daily21`. Rimane visibile ma non viene contato come primo segnale anticipatore forte.
- `EARLY WARNING`: `3/3 + Daily21`, `Prezzo Weekly anticipa COT`, oppure `2/3 PRE-PREZZO` con cambio COT significativo e causale.
- `REVERSAL WATCH`: memoria di un `3/3` recente con estremo 156W ancora presente e Daily21 coerente dopo la scomparsa del 3/3 corrente.

La tabella aggiunge:

- `Fase anticipatrice`
- `Early Warning`
- `Tipo Early Warning`
- `Prima comparsa Early Warning`
- la già esistente `Prima comparsa Reversal Watch`

Sotto la tabella vengono mostrate separatamente la prima data di EARLY WARNING forte e la prima data di REVERSAL WATCH.

### Perché il semplice 2/3 + Daily21 non conta come EARLY WARNING forte
Le ricostruzioni storiche mostrano che il 2/3 + Daily21 può ripetersi per più report senza evolvere in reversal. Per evitare rumore e hindsight rimane un `WARNING BASE`. I segnali più strutturati vengono invece marcati come `EARLY WARNING`.

### Watchlist più leggibile
Nel Focus Operativo, `Da monitorare` mostra ora la colonna `Fase osservazione`:

- `REVERSAL WATCH`
- `EARLY WARNING`
- `WARNING BASE`
- `CONFERMATO SOTTO SOGLIA`
- `REGIME IN SVILUPPO`
- `MATURAZIONE`

I mercati in `EARLY WARNING` o `REVERSAL WATCH` vengono anche richiamati sopra la tabella come segnali anticipatori prioritari da aprire sul grafico. Restano watchlist, non ingressi automatici.

La priorità del `2/3 PRE-PREZZO` significativo viene posta davanti al semplice `2/3 + Daily21`, perché il primo contiene anche un cambiamento causale del precedente setup e dello Score.

## Logica invariata
Non vengono modificati:

- motore Smart Money
- Stato Screener
- Score Screener
- Alignment Map
- Weekly Change Radar
- criteri di ingresso nel Focus
- Verifica Focus precedente
- Price Action Timing

La V6.39 modifica la classificazione/visibilità della watchlist e il Replay diagnostico, non il motore direzionale.
