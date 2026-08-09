# COT Smart Money Python V6.25

Versione Python allineata al nuovo indicatore di riferimento **G. COT Smart Money Engine V1.5.47**.

La V6.25 aggiorna insieme:

- Analisi singolo strumento;
- COT Screener;
- Weekly Change Radar;
- export Excel/JPG;
- `PROMPT.TXT`;
- `PROMPT_SCREENER.TXT`.

## Novità recepite dalla V1.5.47

### 1. Origine Flow 1W separata dall'Open Interest

L'ultimo report non viene più ridotto pubblicamente alle sole etichette `NUOVI LONG`, `NUOVI SHORT`, `SHORT COVERING` o `LIQUIDAZIONE LONG`.

La dashboard espone ora **Origine Flow 1W**, calcolata da:

- variazione Long;
- variazione Short;
- variazione della Net Position.

L'Open Interest 1W è mostrato a parte come:

- `PARTECIPAZIONE CRESCENTE`;
- `PARTECIPAZIONE DECRESCENTE`;
- `PARTECIPAZIONE STABILE`.

Quando Long e Short si muovono in direzioni opposte, la V1.5.47 usa una soglia di dominanza pari a **1,25** per stabilire quale componente spiega soprattutto il cambiamento.

Le vecchie classificazioni `NUOVI LONG / NUOVI SHORT / SHORT COVERING / LIQUIDAZIONE LONG` restano disponibili esclusivamente come **segnale interno del motore**, perché sono ancora usate dalla logica originale TradingView e dal ranking deterministico dello Screener.

### 2. COT Index: dicitura 156W esplicita

Le zone pubbliche sono ora:

- `VICINO AL MASSIMO DEL RANGE STORICO 156W`;
- `FASCIA ALTA DEL RANGE STORICO 156W`;
- `FASCIA CENTRALE DEL RANGE STORICO 156W`;
- `FASCIA BASSA DEL RANGE STORICO 156W`;
- `VICINO AL MINIMO DEL RANGE STORICO 156W`.

### 3. Conferme mancanti spiegate in modo deterministico

Per i quadri incompleti la dashboard verifica, nello stesso ordine della V1.5.47:

1. prezzo Weekly;
2. struttura 3–6W della categoria principale;
3. Flow 1W della categoria principale;
4. controparte nell'ultimo report;
5. controparte nella struttura 3–6W.

Per le valute viene esplicitato che i **Dealer/Intermediary** devono confermare il normale ruolo di controparte dei Leveraged Funds.

### 4. Nuovi warning di prima variazione

Sono state aggiunte le formule:

- `PRIMO MIGLIORAMENTO COT, MA VIEW RIALZISTA NON ANCORA FORMATA`;
- `PRIMO PEGGIORAMENTO COT, MA VIEW RIBASSISTA NON ANCORA FORMATA`.

Servono a evitare che un solo cambiamento settimanale venga interpretato come struttura 3–6W già formata.

### 5. Divergenza COT/prezzo

Le frasi Long e Short sono state riallineate alla V1.5.47: quando il COT indica una direzione ma il prezzo Weekly non la conferma, la dashboard lo dichiara esplicitamente e invita a non anticipare l'operazione.

### 6. Diagnostica completa

Nei dettagli dell'analisi vengono ora mostrati anche:

- Origine Flow 1W;
- Δ Long 1W;
- Δ Short 1W;
- Net Position 1W;
- contesto OI 1W;
- Flow 3W e 6W.

## Screener V6.25

La classifica pubblica mostra **Origine Flow 1W**. Il segnale `NUOVI LONG / NUOVI SHORT / SHORT COVERING / LIQUIDAZIONE LONG` è conservato come **Segnale flusso motore** per la logica deterministica.

La formula e le soglie dello **Score Screener** non sono state cambiate dalla V6.24: il nuovo indicatore TradingView modifica soprattutto la spiegazione dell'origine del Flow, non la logica interna `smart_new_long`, `smart_new_short`, `smart_short_covering` e `smart_long_liquidation`.

Lo Score Screener resta un ranking operativo Python e non va confuso con l'output nascosto `Smart Money Score 0-100` dell'indicatore TradingView, che misura un regime direzionale da ribassista a rialzista.

## Weekly Change Radar V6.25

Il confronto tra report precedente e corrente ora considera esplicitamente:

- Origine Flow 1W precedente / corrente;
- Δ Long precedente / corrente;
- Δ Short precedente / corrente;
- contesto OI 1W precedente / corrente;
- Stato;
- Score;
- prezzo Weekly;
- Regime 156W.

Il Radar continua a ricostruire lo snapshot precedente senza utilizzare dati futuri del prezzo.

L'Excel dedicato continua a essere **completo e indipendente dai filtri a video** e comprende:

- `Weekly Change Radar`;
- `Radar Indici`;
- `Radar Valute`;
- `Radar Metalli`;
- `Radar Energetici`;
- `Radar Tassi`;
- `Radar Crypto`;
- `Radar Agricoli`;
- `Radar Soft`;
- `Radar Bestiame`.

I JPG continuano invece a rappresentare la vista filtrata.

## Prompt AI

Entrambi i prompt sono stati aggiornati alla V1.5.47. In particolare obbligano l'AI a:

- non usare l'OI per definire l'origine del Flow;
- distinguere aumento Long, aumento Short, chiusura Short e riduzione Long;
- rispettare la soglia di dominanza 1,25;
- spiegare quale conferma manca;
- trattare Dealer/Intermediary come normale controparte FX;
- riconoscere i warning di primo miglioramento/peggioramento;
- confrontare nel Weekly Change Radar l'Origine Flow dei due report;
- non inventare supporti, resistenze, POC o altri livelli non calcolati dall'app Python.

## Salvaguardie Python mantenute

Restano intenzionalmente le correzioni già introdotte nelle versioni precedenti:

- un semplice Alignment 2/3 non crea una direzione;
- un 3/3 grezzo resta separato dalla view principale finché non passa almeno a `IN SVILUPPO`;
- dati COT troppo vecchi non producono una view operativa;
- se un quadro è già Long confermato ma l'ultimo impulso è soprattutto Short Covering, la frase non finge che il prezzo debba ancora confermare;
- caso speculare per Short confermato + Liquidazione Long;
- nessun riferimento operativo a supporti, resistenze o POC che la dashboard Python non calcola.

## Verifiche eseguite

- compilazione Python con `py_compile`;
- test di tutte le combinazioni principali di Origine Flow 1W;
- test separazione Origine Flow / OI 1W;
- test conferma mancante FX Dealer/Intermediary;
- test warning di primo miglioramento;
- confronto casuale su 1.000 casi per verificare che Stato e Score Screener non siano stati alterati accidentalmente;
- test Weekly Change Radar sull'origine del Flow e sul contesto OI;
- verifica export Excel del Radar e dei nove fogli settoriali;
- controllo placeholder dei prompt;
- controllo integrità ZIP.

## Nota sulla parità con TradingView

La logica viene replicata il più fedelmente possibile. I valori live possono comunque differire in alcuni casi per differenze tra la sorgente CFTC usata da Python, la Library COT di TradingView, tempi di aggiornamento dei report e dati prezzo Yahoo/TradingView.
