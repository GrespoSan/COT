# COT Smart Money — versione Python

## File

- `app_cot_smart_money.py`: applicazione Streamlit completa.
- `PROMPT.TXT`: istruzioni operative preimpostate per l'interrogazione AI.
- `requirements_cot.txt`: dipendenze per Streamlit Cloud.
- `term_structure.csv`: archivio manuale Contango / Backwardation per le commodity.
- `.streamlit/secrets.toml.example`: esempio delle chiavi necessarie per l'interrogazione AI.

## Installazione locale

```bash
pip install -r requirements_cot.txt
streamlit run app_cot_smart_money.py
```

## Streamlit Cloud

1. Carica tutti i file nel repository GitHub, compreso `PROMPT.TXT`.
2. Rinomina `requirements_cot.txt` in `requirements.txt` oppure copia il suo contenuto nel requirements già presente.
3. Imposta come Main file path `app_cot_smart_money.py`.
4. Apri **Settings → Secrets** e inserisci almeno una chiave AI.

Esempio:

```toml
GEMINI_API_KEY = "..."
GEMINI_MODEL = "gemini-3.5-flash"

GROQ_API_KEY = "..."
GROQ_MODEL = "openai/gpt-oss-120b"
```

Non caricare nel repository un file contenente chiavi reali.

## Term Structure

La CFTC non pubblica direttamente il confronto M1–M2. Il valore resta manuale, ma l'app chiarisce automaticamente quando serve:

- `NON APPLICABILE`: indici, valute, tassi, volatilità e crypto CME;
- `OPZIONALE`: commodity con il solo motore Smart Money;
- `RICHIESTA SOLO PER SQUEEZE LEGACY`: commodity con modulo Legacy attivo.

La Term Structure non modifica il responso principale Smart Money. Nel modulo Legacy è necessaria soltanto per confermare lo scenario `SHORT COVERING SQUEEZE` in presenza di Backwardation.

Puoi:

- modificare `term_structure.csv` nel repository per salvare un valore predefinito;
- selezionare il valore dalla sidebar;
- caricare un CSV aggiornato dalla sidebar.

Valori ammessi: `Non disponibile`, `Contango`, `Backwardation`, `Curva piatta`.

## Interrogazione AI

La sezione AI riceve l'intero quadro deterministico:

- report e data delle posizioni;
- COT Index e posizionamento;
- flussi 1W, 3W e 6W;
- Open Interest;
- conferma prezzo Weekly ed EMA21;
- concentrazione Top 8;
- stato e valore della Term Structure;
- responso Smart Money e, quando attivo, modulo Legacy.

Il prompt operativo viene caricato automaticamente da `PROMPT.TXT`. Per modificarne stile, struttura o regole basta aggiornare quel file nel repository: non serve intervenire nel codice Python.

L'app non allega automaticamente uno screenshot all'AI e non calcola ancora Alignment Map, POC, supporti o resistenze. Quando il prompt li richiede, l'AI riceve il vincolo di dichiarare `dato non chiaramente leggibile` e di non inventare livelli.

Quando cambi strumento oppure arriva una nuova data COT, l'app cancella automaticamente:

- la precedente risposta AI;
- la domanda personalizzata precedente;
- il vecchio contesto AI.

È possibile scegliere Google Gemini oppure Groq e aggiungere una domanda personalizzata. L'AI può spiegare e contestualizzare il risultato, ma non deve sostituire il responso deterministico calcolato dall'app.

## Logica inclusa

- report TFF Futures Only per indici, valute, tassi, volatilità e crypto CME;
- report Disaggregated Futures Only per commodity;
- Managed Money / Producer per commodity;
- Leveraged Funds / Dealer per valute;
- Leveraged Funds / Asset Manager per altri finanziari;
- flussi 1W, 3W e 6W;
- COT Index 26/52/156/260 settimane;
- Open Interest;
- concentrazione Top 8 e percentile storico;
- prezzo Weekly con EMA21, usando solo settimane completate;
- modulo Legacy separato ultimo report vs penultimo;
- interrogazione AI con prompt esterno modificabile;
- export CSV del responso e dello storico.
