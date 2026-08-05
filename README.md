# COT Smart Money — Python V6.9

Aggiornamento della dashboard Python allineato al **G. COT Smart Money Engine TradingView V1.5.22**.

## Novità principali

- Report principale con lo stesso ordine didattico di TradingView:
  1. posizione attuale Long/Short dei Fondi;
  2. cosa hanno fatto nell’ultimo report;
  3. andamento delle ultime 3 e 6 settimane;
  4. estremità del posizionamento;
  5. sostegno dell’Open Interest;
  6. concentrazione Top 8.
- COT Index informativi fissi a **26W** e **156W**.
- Segnalazione di nuovi massimi/minimi della Net Position a 26W e 156W.
- Esposizione direzionale Long/Short, escludendo le posizioni Spreading.
- Nuova sintesi semplice che descrive Fondi, controparte e conferma del prezzo.
- Modalità report **Compatto** predefinita e **Completo** opzionale.
- In modalità Completo:
  - confronto Leveraged Funds / Asset Manager sulle valute;
  - flussi facoltativi di tutte le categorie disponibili.
- Screener ed export Excel/JPG aggiornati con COT Index 26W e 156W.

## Logica invariata

Le nuove misure sono informative. Non modificano:

- motore Smart Money;
- COT Alignment Map;
- Score dello screener;
- classificazioni Long/Short;
- Term Structure manuale.

## Avvio locale

```bash
pip install -r requirements.txt
streamlit run app_cot_smart_money.py
```

## Streamlit Cloud

Usa `app_cot_smart_money.py` come file principale. Per l’AI, copia le chiavi necessarie nei Secrets della piattaforma seguendo `.streamlit/secrets.toml.example`.
