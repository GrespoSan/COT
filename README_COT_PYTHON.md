# COT Smart Money — versione Python

## File

- `app_cot_smart_money.py`: applicazione Streamlit completa.
- `requirements_cot.txt`: dipendenze per Streamlit Cloud.
- `term_structure.csv`: archivio manuale Contango / Backwardation per le commodity.

## Installazione locale

```bash
pip install -r requirements_cot.txt
streamlit run app_cot_smart_money.py
```

## Streamlit Cloud

1. Carica i tre file nel repository GitHub.
2. Rinomina `requirements_cot.txt` in `requirements.txt` oppure copia il suo contenuto nel requirements già presente.
3. Imposta come Main file path `app_cot_smart_money.py`.

## Term Structure

La CFTC non pubblica direttamente il confronto M1–M2. Il valore resta quindi manuale:

- modifica `term_structure.csv` nel repository per salvare un valore predefinito;
- oppure seleziona il valore dalla sidebar;
- oppure carica un CSV aggiornato dalla sidebar.

Valori ammessi: `Non disponibile`, `Contango`, `Backwardation`, `Curva piatta`.

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
- export CSV del responso e dello storico.

## Nota

Il primo avvio può richiedere qualche secondo perché l'app risolve il nome esatto del mercato nei dataset CFTC. Le richieste vengono poi memorizzate nella cache Streamlit.
