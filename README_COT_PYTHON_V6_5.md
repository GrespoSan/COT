# COT Smart Money Python V6.5

Questa versione parte dal progetto **COT-main ULTIMO**, che include già le tre esportazioni JPG della V6.4 e la classificazione AI esclusiva della V6.3.

## Novità V6.5

- **Rapid Shift 6W** della controparte: differenza tra il COT Index corrente e quello di sei report fa.
- Classificazione Rapid Shift: Rapido rialzista, In accelerazione, Normale, In peggioramento, Rapido ribassista.
- **OI Index 52W**: Open Interest normalizzato nel range degli ultimi 52 report.
- Rapid Shift mostrato sotto le tre categorie della COT Alignment Map.
- OI Index 52W nelle metriche e nel quadro tecnico dell'analisi singola.
- Nuove colonne e filtri nello screener.
- Nuovi fogli Excel per Rapid Shift e OI Index estremi.
- Esportazioni JPG e prompt AI aggiornati.
- Lo storico CSV contiene automaticamente le nuove colonne.

## Regola importante

Rapid Shift 6W e OI Index 52W sono inizialmente **informativi**. Non modificano:

- Score dello screener;
- Stato deterministico;
- classificazione AI;
- responso Smart Money.

## File principali

- `app.py`: applicazione Streamlit.
- `PROMPT.TXT`: istruzioni AI per il singolo mercato.
- `PROMPT_SCREENER.TXT`: istruzioni AI dello screener.
- `requirements.txt`: dipendenze.
- `term_structure.csv`: archivio manuale della Term Structure.

## Avvio locale

```bash
pip install -r requirements.txt
streamlit run app.py
```
