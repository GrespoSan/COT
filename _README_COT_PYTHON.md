# COT Smart Money — versione Python V5

## File

- `app_cot_smart_money.py`: applicazione Streamlit completa.
- `PROMPT.TXT`: istruzioni operative preimpostate per l'interrogazione AI.
- `requirements.txt`: dipendenze per Streamlit Cloud.
- `requirements_cot.txt`: copia equivalente delle dipendenze.
- `term_structure.csv`: archivio manuale Contango / Backwardation per le commodity.
- `.streamlit/secrets.toml.example`: esempio delle chiavi necessarie per l'interrogazione AI.

## Installazione locale

```bash
pip install -r requirements.txt
streamlit run app_cot_smart_money.py
```

## Streamlit Cloud

1. Carica tutti i file nel repository GitHub, compreso `PROMPT.TXT`.
2. Imposta come Main file path `app_cot_smart_money.py`.
3. Apri **Settings → Secrets** e inserisci almeno una chiave AI.

Esempio:

```toml
GEMINI_API_KEY = "..."
GEMINI_MODEL = "gemini-3.5-flash"

GROQ_API_KEY = "..."
GROQ_MODEL = "openai/gpt-oss-120b"
```

Non caricare nel repository un file contenente chiavi reali.

## Motore Smart Money

Il responso principale usa automaticamente il report appropriato:

- commodity: Disaggregated, Managed Money contro Producer / Merchant;
- valute: Financial, Leveraged Funds contro Dealer / Intermediary;
- indici, tassi, volatilità e crypto CME: Financial, Leveraged Funds contro Asset Manager.

Il vecchio modulo Legacy è stato rimosso dall'interfaccia per evitare due letture diverse dello stesso mercato. Il risultato principale dell'app deriva quindi soltanto dal motore Smart Money specifico per famiglia di mercato.

## COT Alignment Map

L'app calcola anche i tre indici normalizzati richiesti dall'Alignment Map, usando lo stesso report CFTC e lo stesso lookback del motore principale:

- categoria speculativa: Managed Money oppure Leveraged Funds;
- controparte: Producer, Dealer oppure Asset Manager;
- Nonreportable / Small Traders.

Sono calcolati:

- valore 0–100 delle tre categorie;
- zona relativa: estremo alto, estremo basso, sopra o sotto la media;
- allineamento rialzista da 0/3 a 3/3;
- allineamento ribassista da 0/3 a 3/3;
- descrizione strutturale coerente con il Pine Script fornito.

L'Alignment Map non modifica il flusso settimanale del motore Smart Money: aggiunge il contesto strutturale necessario all'analisi finale e viene passato automaticamente all'AI.

## Term Structure

La CFTC non pubblica direttamente il confronto M1–M2. Il valore resta manuale:

- `NON APPLICABILE`: indici, valute, tassi, volatilità e crypto CME;
- `OPZIONALE`: commodity.

La Term Structure non modifica il responso Smart Money né l'Alignment Map. Puoi:

- modificare `term_structure.csv` nel repository;
- selezionare il valore dalla sidebar;
- caricare un CSV aggiornato dalla sidebar.

Valori ammessi: `Non disponibile`, `Contango`, `Backwardation`, `Curva piatta`.

## Interrogazione AI

La sezione AI riceve automaticamente:

- report e data delle posizioni;
- COT Index e posizionamento;
- flussi 1W, 3W e 6W;
- variazioni Long e Short;
- Open Interest;
- conferma prezzo Weekly ed EMA21;
- concentrazione Top 8;
- COT Alignment Map completo;
- stato e valore della Term Structure;
- responso deterministico Smart Money.

La modalità dell'interrogazione AI è automatica:

- campo **Domanda specifica** vuoto: viene applicato integralmente `PROMPT.TXT` e sono prodotti gli output completi previsti dal file;
- campo **Domanda specifica** compilato: `PROMPT.TXT` viene ignorato e l'AI risponde soltanto alla domanda inserita.

In questo modo una richiesta mirata, come “concentrati solo sulla qualità dei flussi dell'ultimo report”, non viene diluita dalla struttura del prompt generale.

Il prompt operativo viene caricato da `PROMPT.TXT`. Per modificarne stile, struttura o regole basta aggiornare quel file nel repository.

L'app non calcola ancora POC, supporti o resistenze. Quando il prompt li richiede, l'AI riceve il vincolo di dichiarare `dato non chiaramente leggibile` e di non inventare livelli.

Quando cambi strumento oppure arriva una nuova data COT, l'app cancella automaticamente la precedente risposta AI, la domanda personalizzata e il vecchio contesto.

## Logica inclusa

- report TFF Futures Only per finanziari e valute;
- report Disaggregated Futures Only per commodity;
- flussi 1W, 3W e 6W;
- COT Index 26/52/156/260 settimane;
- COT Alignment Map 0–100 con punteggi 0/3–3/3;
- Open Interest;
- concentrazione Top 8 e percentile storico;
- prezzo Weekly con EMA21, usando solo settimane completate;
- interrogazione AI con prompt esterno modificabile;
- export CSV del responso e dello storico.


## Modifica V5

- rimossa dalla schermata e dal contesto AI la dicitura di freschezza del tipo `FRESCO (4 giorni)`;
- domanda specifica prioritaria: quando il campo è compilato, il prompt generale viene ignorato;
- campo vuoto: resta disponibile l’analisi completa basata su `PROMPT.TXT`.
