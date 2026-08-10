# COT Smart Money Python V6.26

Versione Python allineata al nuovo indicatore di riferimento **G. COT Smart Money Engine V1.5.48**.

La V6.26 aggiorna insieme:

- Analisi singolo strumento;
- COT Screener;
- Weekly Change Radar;
- export Excel/JPG;
- `PROMPT.TXT`;
- `PROMPT_SCREENER.TXT`.

## Novità recepite dalla V1.5.48

### 1. Prezzo che anticipa il COT su Alignment contrarian 3/3

La V1.5.48 introduce due nuovi stati distinti:

- `DIVERGENZA RIALZISTA PREZZO/COT IN ATTO`;
- `DIVERGENZA RIBASSISTA PREZZO/COT IN ATTO`.

Caso rialzista:

- Alignment rialzista 156W = 3/3;
- prezzo Weekly già confermato rialzista;
- non sono ancora presenti nuovi Long della categoria trend insieme a un miglioramento della Net Position.

Caso ribassista speculare:

- Alignment ribassista 156W = 3/3;
- prezzo Weekly già confermato ribassista;
- non sono ancora presenti nuovi Short della categoria trend insieme a un peggioramento della Net Position.

La lettura è quindi: **il prezzo sta anticipando il COT**. È un segnale più avanzato di un semplice 3/3 grezzo, ma non è ancora un cambio di regime confermato.

La gerarchia usata nel Weekly Change Radar diventa:

`2/3 < 3/3 grezzo < PREZZO ANTICIPA COT < IN SVILUPPO < CONFERMATO`.

### 2. Correzione Long liquidation / Short covering nei setup 3/3

La V1.5.48 rende più rigorose due classificazioni speciali:

- `alignment_bull_long_liquidation_dominant` richiede ora **Long in calo + Short in calo + Net Position in peggioramento**;
- `alignment_bear_short_covering_dominant` richiede ora **Long in calo + Short in calo + Net Position in miglioramento**.

In questo modo non viene più usata la frase “domina la Long liquidation / domina lo Short covering” quando soltanto una delle due componenti sta realmente diminuendo.

## Funzioni V1.5.47 mantenute

### Origine Flow 1W separata dall'Open Interest

L'ultimo report mantiene la lettura pubblica **Origine Flow 1W**, calcolata da:

- variazione Long;
- variazione Short;
- variazione della Net Position.

L'Open Interest 1W resta mostrato separatamente come:

- `PARTECIPAZIONE CRESCENTE`;
- `PARTECIPAZIONE DECRESCENTE`;
- `PARTECIPAZIONE STABILE`.

Quando Long e Short si muovono in direzioni opposte, resta la soglia di dominanza **1,25**.

Le classificazioni `NUOVI LONG / NUOVI SHORT / SHORT COVERING / LIQUIDAZIONE LONG` restano disponibili come **segnale interno del motore**, perché sono ancora utilizzate dalla logica deterministica.

### Conferme mancanti

Per i quadri incompleti la dashboard continua a verificare:

1. prezzo Weekly;
2. struttura 3–6W della categoria principale;
3. Flow 1W della categoria principale;
4. controparte nell'ultimo report;
5. controparte nella struttura 3–6W.

Per le valute i **Dealer/Intermediary** devono svolgere il normale ruolo di controparte dei Leveraged Funds.

### Primo miglioramento / peggioramento

Restano:

- `PRIMO MIGLIORAMENTO COT, MA VIEW RIALZISTA NON ANCORA FORMATA`;
- `PRIMO PEGGIORAMENTO COT, MA VIEW RIBASSISTA NON ANCORA FORMATA`.

## Analisi singolo strumento V6.26

La sezione **“Si sta preparando un possibile cambio di regime?”** riconosce ora anche le due divergenze Prezzo/COT.

Quando il prezzo anticipa il COT, la dashboard spiega esplicitamente che:

- il prezzo Weekly è già coerente con il possibile cambio;
- l'Alignment è già 3/3;
- il COT non ha ancora confermato con nuovi Long/Short e variazione coerente della Net Position;
- il setup va monitorato ma non trattato come Long/Short confermato.

La diagnostica completa continua a mostrare Origine Flow 1W, Δ Long, Δ Short, Net Position 1W, OI 1W separato e struttura 3–6W.

## Screener V6.26

Lo Screener espone ora anche:

- colonna `Prezzo anticipa COT` = `RIALZISTA`, `RIBASSISTA` oppure `NO`;
- flag dedicati di divergenza rialzista/ribassista;
- filtro Regime 156W `PREZZO ANTICIPA COT`;
- foglio Excel `Prezzo anticipa COT`.

**La nuova divergenza non promuove automaticamente lo Stato principale dello Screener.** Rimane una informazione del Regime 156W finché il COT non compie il passo successivo previsto dalla V1.5.48.

Lo **Score Screener non è stato modificato** dalla nuova logica V1.5.48: la modifica Pine riguarda la classificazione del possibile cambio di regime, non la formula del ranking operativo Python.

Lo Score Screener resta inoltre distinto dall'output nascosto `Smart Money Score 0-100` del Pine, che misura un regime direzionale.

## Weekly Change Radar V6.26

Il Radar confronta ora anche:

- `Prezzo anticipa COT precedente`;
- `Prezzo anticipa COT` attuale.

Se compare per la prima volta una divergenza prezzo/COT mentre lo Stato principale non è ancora operativo, il Radar restituisce:

- priorità `⚠️ PREZZO ANTICIPA IL COT`;
- verdetto `DA MONITORARE`.

Non viene promosso automaticamente a `DA APPROFONDIRE`: servono ancora i nuovi Long/Short e la variazione coerente della Net Position richiesti dal riferimento V1.5.48.

Il Radar continua a confrontare anche:

- Origine Flow 1W precedente / corrente;
- Δ Long precedente / corrente;
- Δ Short precedente / corrente;
- contesto OI 1W precedente / corrente;
- Stato;
- Score;
- prezzo Weekly;
- Regime 156W.

Lo snapshot precedente continua a essere ricostruito senza utilizzare dati futuri del prezzo.

L'Excel dedicato resta **completo e indipendente dai filtri a video** e comprende il foglio generale e i nove fogli settoriali. I JPG continuano invece a rappresentare la vista filtrata.

## Prompt AI V6.26

Entrambi i prompt sono stati aggiornati alla V1.5.48. In particolare obbligano l'AI a:

- riconoscere `DIVERGENZA RIALZISTA/RIBASSISTA PREZZO/COT IN ATTO`;
- non trasformarla in Long/Short confermato;
- spiegare che il prezzo anticipa il COT e quale conferma manca;
- applicare la classificazione dominante Long liquidation / Short covering soltanto quando Long e Short stanno entrambi diminuendo;
- mantenere Origine Flow 1W e OI 1W separati;
- rispettare le conferme specifiche della controparte;
- non inventare supporti, resistenze, POC o altri livelli non calcolati dall'app Python.

## Salvaguardie Python mantenute

Restano intenzionalmente:

- un semplice Alignment 2/3 non crea una direzione;
- un 3/3 grezzo resta separato dalla view principale;
- anche `PREZZO ANTICIPA COT` resta separato dalla view principale finché il COT non conferma;
- dati COT troppo vecchi non producono una view operativa;
- Top 8 è fragilità, non direzione;
- OI Index 52W è partecipazione, non direzione;
- nessun riferimento operativo a supporti, resistenze o POC che Python non calcola.

## Verifiche eseguite

- diff completo Pine V1.5.47 → V1.5.48;
- compilazione Python con `py_compile`;
- test sintetici divergenza rialzista Prezzo/COT;
- test sintetici divergenza ribassista Prezzo/COT;
- test priorità della divergenza rispetto ai sottocasi 3/3 in costruzione;
- test correzione Long liquidation dominante;
- test correzione Short covering dominante;
- verifica che `screener_status()` e lo Score non vengano promossi automaticamente dalla sola divergenza;
- test maturità del regime nel Weekly Change Radar;
- test priorità `⚠️ PREZZO ANTICIPA IL COT`;
- verifica colonne/export e foglio Excel dedicato;
- controllo placeholder dei prompt;
- controllo integrità ZIP.

## Nota sulla parità con TradingView

La logica viene replicata il più fedelmente possibile. I valori live possono comunque differire in alcuni casi per differenze tra la sorgente CFTC usata da Python, la Library COT di TradingView, tempi di aggiornamento dei report e dati prezzo Yahoo/TradingView.
