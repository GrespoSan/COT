# COT Smart Money Python V6.3

## Novità

- Esportazione della tabella visibile dello screener in formato JPG.
- Il JPG rispetta i filtri applicati e include le stesse colonne mostrate a video.
- Nuova classificazione AI deterministica ed esclusiva.
- `LONG IN COSTRUZIONE` viene inserito soltanto tra i mercati da monitorare.
- `LONG CONFERMATO` viene inserito soltanto tra le opportunità Long confermate.
- Gli stati affollati vengono inseriti soltanto tra i mercati da non inseguire.
- Uno strumento non può comparire in più sezioni operative della risposta AI.

## File principali

- `app_cot_smart_money.py`: applicazione Streamlit.
- `PROMPT.TXT`: prompt dell'analisi del singolo strumento.
- `PROMPT_SCREENER.TXT`: prompt dello screener.
- `requirements.txt`: dipendenze, inclusa Pillow per creare il JPG.
- `term_structure.csv`: archivio manuale della Term Structure.

## Avvio locale

```bash
pip install -r requirements.txt
streamlit run app_cot_smart_money.py
```

## Esportazione JPG

Nella pagina `COT Screener`, dopo la tabella, sono disponibili due pulsanti:

- `Scarica Screener Excel`
- `Scarica tabella JPG`

Il file JPG contiene i risultati attualmente visibili dopo l'applicazione dei filtri.
