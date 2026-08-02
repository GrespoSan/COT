# COT Smart Money Python V6.4

## Novità

- Tre esportazioni JPG separate nella pagina `COT Screener`:
  - `Scarica JPG Top 5`
  - `Scarica JPG Top 10`
  - `Scarica JPG Totale`
- Tutte le immagini rispettano i filtri applicati alla tabella.
- Top 5 e Top 10 esportano le prime righe della classifica attualmente visibile.
- Il titolo dell'immagine indica chiaramente il tipo di esportazione.
- L'esportazione Excel continua a contenere lo screener completo.
- Restano attive le classificazioni AI esclusive introdotte nella V6.3.

## File principali

- `app_cot_smart_money.py`: applicazione Streamlit.
- `PROMPT.TXT`: prompt dell'analisi del singolo strumento.
- `PROMPT_SCREENER.TXT`: prompt dello screener con sezioni operative mutuamente esclusive.
- `requirements.txt`: dipendenze, inclusa Pillow per creare i JPG.
- `term_structure.csv`: archivio manuale della Term Structure.

## Avvio locale

```bash
pip install -r requirements.txt
streamlit run app_cot_smart_money.py
```

## Regola delle esportazioni JPG

Le immagini vengono costruite sulla tabella visibile dopo i filtri:

- `Top 5`: prime 5 righe visibili;
- `Top 10`: prime 10 righe visibili;
- `Totale`: tutte le righe visibili.

Se i risultati filtrati sono meno di 5 o 10, il file contiene tutte le righe disponibili.
