# COT Smart Money — versione Python V6.1

La V6.1 mantiene separate le due funzioni principali dell'app:

1. **Analisi singolo strumento**: approfondimento completo di un future, con AI facoltativa e risposta soltanto a video.
2. **COT Screener**: analisi su richiesta di tutti i mercati selezionati, classifica deterministica, esportazione Excel e spiegazione AI facoltativa dei primi 5 o 10 risultati.

## File principali

- `app_cot_smart_money.py`: applicazione Streamlit completa.
- `PROMPT.TXT`: prompt modificabile dell'analisi AI sul singolo strumento.
- `PROMPT_SCREENER.TXT`: prompt modificabile della spiegazione AI finale dello screener.
- `term_structure.csv`: archivio manuale Contango / Backwardation per le commodity.
- `requirements.txt`: dipendenze per Streamlit Cloud.
- `.streamlit/secrets.toml.example`: esempio delle chiavi AI.

## Installazione locale

```bash
pip install -r requirements.txt
streamlit run app_cot_smart_money.py
```

## Streamlit Cloud

1. Carica tutti i file nel repository GitHub.
2. Imposta `app_cot_smart_money.py` come **Main file path**.
3. Inserisci nei Secrets almeno una chiave AI.

```toml
GEMINI_API_KEY = "..."
GEMINI_MODEL = "gemini-3.5-flash"

GROQ_API_KEY = "..."
GROQ_MODEL = "openai/gpt-oss-120b"
```

Non pubblicare mai chiavi reali nel repository.

---

# 1. Analisi singolo strumento

La prima sezione conserva il funzionamento della V5:

- scelta del future;
- report CFTC specifico per famiglia di mercato;
- Smart Money Engine;
- flussi 1W, 3W e 6W;
- COT Index;
- COT Alignment Map;
- Open Interest;
- concentrazione Top 8;
- prezzo Weekly ed EMA21;
- grafici;
- domanda AI facoltativa.

## Report utilizzati

- commodity: report **Disaggregated**, Managed Money contro Producer / Merchant;
- valute: report **Financial**, Leveraged Funds contro Dealer / Intermediary;
- indici, tassi, volatilità e crypto CME: report **Financial**, Leveraged Funds contro Asset Manager.

Il vecchio modulo Legacy non viene utilizzato.

## AI sul singolo strumento

- campo domanda vuoto: usa integralmente `PROMPT.TXT`;
- campo domanda compilato: ignora `PROMPT.TXT` e risponde soltanto alla domanda specifica;
- quando cambia mercato o data COT, domanda e risposta precedenti vengono eliminate;
- la risposta AI resta soltanto a video;
- non viene più creato un CSV del responso;
- rimane disponibile soltanto il download facoltativo dello storico numerico COT.

La dicitura visibile del tipo `Freschezza: FRESCO (4 giorni)` non viene mostrata.

## Term Structure

La Term Structure resta manuale e compare soltanto nella pagina singola:

- `NON APPLICABILE`: indici, valute, tassi, volatilità e crypto CME;
- `OPZIONALE`: commodity.

Non modifica il responso Smart Money né l'Alignment Map.

---

# 2. COT Screener

Lo screener non parte automaticamente. Premi:

> **Avvia analisi di tutti i mercati selezionati**

Puoi selezionare tutte le famiglie oppure limitare l'analisi ad alcuni gruppi o strumenti.

Per ogni mercato vengono calcolati con la stessa logica della pagina singola:

- Smart Money Engine;
- qualità del flusso;
- struttura 3W e 6W;
- COT Index;
- COT Alignment Map;
- Open Interest;
- prezzo Weekly ed EMA21;
- concentrazione Top 8;
- stato finale e Score.

La prima scansione completa può richiedere alcuni minuti. Le richieste CFTC e Yahoo vengono poi memorizzate nella cache di Streamlit.

## Stati sintetici

Lo screener assegna una sola classificazione. Il filtro mostra sempre tutti gli stati possibili, anche quando uno di essi non compare nella scansione corrente:

- `LONG CONFERMATO`;
- `SHORT CONFERMATO`;
- `LONG IN COSTRUZIONE`;
- `SHORT IN COSTRUZIONE`;
- `LONG CONFERMATO MA AFFOLLATO (NON INSEGUIRE)`;
- `SHORT CONFERMATO MA AFFOLLATO (NON INSEGUIRE)`;
- `NEUTRALE / POCO CHIARO`.

## Qualità del flusso

Viene distinta automaticamente tra:

- nuovi Long;
- nuovi Short;
- short covering;
- liquidazione Long;
- miglioramento misto;
- peggioramento misto;
- flusso neutrale.

## Score 0–100

Lo Score ordina la qualità complessiva, ma non è un segnale automatico di ingresso.

Componenti visibili nella sezione `Come viene costruito lo Score`:

- motore Smart Money;
- qualità del flusso;
- struttura 3–6W;
- Alignment Map;
- prezzo Weekly;
- Open Interest;
- penalizzazioni per affollamento, concentrazione elevata o report non recenti.

La classifica è deterministica: l'AI non interviene nel calcolo e non modifica la posizione degli strumenti.

## Filtri

Sono disponibili filtri per:

- direzione Long, Short o Neutrale;
- Score minimo;
- Alignment minimo da 0/3 a 3/3;
- prezzo Weekly già confermato;
- stato finale;
- esclusione di short covering, liquidazione Long e flussi neutrali.

## Esportazione Excel

Il pulsante `Scarica Screener Excel` genera un unico file `.xlsx` con i fogli:

- `Classifica generale`;
- `Long interessanti`;
- `Short interessanti`;
- `Alignment 2-3`;
- `Mercati affollati`;
- `Dati completi`;
- `Errori`.

## AI finale dello screener

Dopo la classifica puoi chiedere una sola spiegazione AI dei:

- primi 5 risultati;
- primi 10 risultati.

L'AI riceve i risultati deterministici già ordinati e:

- spiega perché sono in cima;
- separa Long e Short;
- segnala situazioni affollate;
- distingue nuovi flussi da ricoperture o liquidazioni;
- non modifica Score e graduatoria;
- non inventa POC o livelli tecnici.

Le istruzioni sono contenute in `PROMPT_SCREENER.TXT` e possono essere cambiate senza modificare il codice Python.

---

## Avvertenza

Il COT è un dato settimanale ritardato. Lo screener serve a individuare i mercati che meritano un approfondimento; prima di operare apri sempre il singolo strumento e verifica il prezzo sul grafico.
