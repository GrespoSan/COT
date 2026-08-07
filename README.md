# COT Smart Money — Python V6.12

Questa versione aggiorna l'app Python sulla base di **G. COT Smart Money Engine V1.5.36** mantenendo separate:

1. **Analisi singolo strumento** — report didattico completo, grafici e AI facoltativa.
2. **COT Screener** — scansione deterministica dei mercati, classifica, filtri, Excel, JPG Top 5 / Top 10 / totale e AI facoltativa.

## Novità V6.12

### Alignment contrarian fisso 156W

La logica è ora unificata per tutte le famiglie di mercato:

- **Commodity:** Managed Money / Producer-Merchant / Small Traders.
- **FX:** Leveraged Funds / Dealer / Small Traders.
- **Altri Financial:** Leveraged Funds / Asset Manager / Small Traders.

Setup rialzista contrarian:

- categoria trend <= 20;
- controparte >= 80;
- Small Traders <= 20.

Setup ribassista contrarian:

- categoria trend >= 80;
- controparte <= 20;
- Small Traders >= 80.

Il calcolo è sempre riferito al range **156W** e non dipende dal lookback scelto per il COT Index principale del motore.

### Gerarchia del possibile cambio di regime

L'app distingue:

- segnali parziali **2/3**;
- setup contrarian **3/3 in costruzione**;
- **Long/Short contrarian in sviluppo** quando arrivano nuovi Long/Short coerenti con la variazione della Net Position;
- **cambio di regime rialzista/ribassista confermato** solo quando si aggiungono prezzo Weekly e struttura macro 3–6W coerenti.

Sono distinti esplicitamente i casi in cui:

- i Long aumentano ma la Net Position peggiora;
- gli Short aumentano ma la Net Position migliora;
- il miglioramento deriva soltanto da short covering;
- il peggioramento deriva soltanto da long liquidation.

### Report singolo

La prima sezione include ora anche:

**Si sta preparando un possibile cambio di regime?**

La Lettura semplice incorpora il nuovo contesto 156W e la sezione **Cosa fare** segue la stessa gerarchia della V1.5.36.

Quando un Long/Short è ancora parziale ma il prezzo ha già confermato, l'indicazione specifica quale componente manca in base alla famiglia di mercato: Leveraged Funds, Dealer/Intermediary, Asset Manager oppure struttura COT 3–6W.

La formulazione storica usa **ultime 156W** invece di riferimenti generici ai “tre anni”.

### Screener V6.12

Lo screener è stato rivisto per non trattare l'Alignment come un semplice filtro direzionale:

- **2/3:** informazione parziale, da sola non crea una direzione operativa;
- **3/3:** setup contrarian, non ancora conferma;
- **in sviluppo:** peso maggiore nello Score;
- **regime confermato:** peso massimo della componente regime.

Sono stati aggiunti:

- colonna **Regime 156W**;
- dettaglio del regime nei dati completi e nel prompt AI;
- filtro **Cambio di regime 156W**;
- fogli Excel **Regime confermato**, **Contrarian sviluppo**, **Contrarian 3-3**;
- componente **Score Regime 156W**;
- Regime 156W nei JPG dello screener.

Le sette classificazioni pubbliche restano semplici:

- LONG IN COSTRUZIONE
- LONG CONFERMATO
- LONG CONFERMATO — NON INSEGUIRE
- NEUTRALE / POCO CHIARO
- SHORT IN COSTRUZIONE
- SHORT CONFERMATO
- SHORT CONFERMATO — NON INSEGUIRE

La concentrazione Top 8 resta un indicatore di fragilità e non cambia da sola la classificazione.

### Prompt AI

Sono aggiornati entrambi:

- `PROMPT.TXT` — analisi singola;
- `PROMPT_SCREENER.TXT` — screener.

I prompt distinguono esplicitamente:

- posizione attuale vs variazione dell'ultimo report;
- COT Index vs esposizione Long/Short;
- 2/3 vs 3/3 vs regime in sviluppo vs confermato;
- nuovi Long/Short vs short covering/long liquidation;
- Top 8 come fragilità e non come segnale direzionale;
- OI Index 52W come livello di partecipazione e non come direzione.

## Funzioni mantenute

- report CFTC specifico per famiglia di mercato;
- COT Index 26W, 156W e lookback motore;
- Open Interest e OI Index 52W;
- prezzo Weekly + EMA21;
- concentrazione Top 8;
- Rapid Shift informativo;
- Term Structure manuale soltanto per commodity e fuori dallo Score;
- Excel screener;
- JPG Top 5 / Top 10 / totale;
- AI facoltativa sul singolo strumento e sullo screener;
- nessun CSV narrativo AI.

## File del pacchetto

- `app_cot_smart_money.py`
- `PROMPT.TXT`
- `PROMPT_SCREENER.TXT`
- `requirements.txt`
- `term_structure.csv`
- `.streamlit/secrets.toml.example`
- `README.md`

## Installazione

```bash
pip install -r requirements.txt
streamlit run app_cot_smart_money.py
```

## Verifiche svolte

- compilazione Python;
- test sintetici Long e Short su Financial, FX e Commodity;
- verifica che un 2/3 da solo resti neutrale nello screener;
- verifica dei testi principali V1.5.36;
- test export Excel e JPG;
- verifica dei placeholder dei prompt;
- controllo integrità ZIP.

Non è stata eseguita, durante la costruzione del pacchetto, una scansione live completa di tutti i mercati CFTC/Yahoo.
