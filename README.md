# COT Smart Money — Python V6.11

Versione allineata alle frasi e alla lettura didattica di TradingView **G. COT Smart Money Engine V1.5.25**.

## Aggiornamenti principali

- COT Index 26W e 156W descritti come collocazione della Net Position nel range storico.
- Eliminata l'equivalenza impropria tra COT Index alto/basso e posizione necessariamente Net Long/Net Short.
- Lettura OI 3–6W resa direzionale: rialzista, ribassista oppure quadro senza direzione uniforme.
- Nuove frasi: movimento sostenuto, perdita di partecipazione, partecipazione stabile e movimento non ancora confermato.
- Sintesi semplice basata su esposizione Long/Short effettiva, ultimo report, controparte, range storico e prezzo Weekly.
- Sezione “Cosa fare” preceduta dalla view rialzista/ribassista o possibile view.
- Stati pubblici semplificati: `LONG/SHORT CONFERMATO — NON INSEGUIRE`; nessuna etichetta “affollato”.
- Screener ed export aggiornati con la colonna `Partecipazione OI 3-6W`.
- `PROMPT.TXT` e `PROMPT_SCREENER.TXT` allineati alla V1.5.25.

## File principali

- `app_cot_smart_money.py`
- `PROMPT.TXT`
- `PROMPT_SCREENER.TXT`
- `requirements.txt`
- `term_structure.csv`
- `.streamlit/secrets.toml.example`

## Avvio locale

```bash
pip install -r requirements.txt
streamlit run app_cot_smart_money.py
```

## Nota

Il COT Index indica dove si trova la Net Position rispetto al proprio intervallo storico. La direzione attuale Long/Short deriva invece dalle percentuali delle posizioni direzionali, con le posizioni Spreading escluse.
