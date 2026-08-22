# COT Smart Money Python V6.42

Base: V6.40. Modifica esclusivamente testuale nella colonna pubblica **Tipo opportunità** del Focus Operativo.

## Novità V6.42

La dicitura:

`NUOVA DIREZIONE APPENA CONFERMATA`

è stata sostituita con:

`NUOVA DIREZIONE APPENA CONFERMATA - PUNTO DI SVOLTA`

Lo scopo è rendere immediatamente evidente anche a un neofita che non si tratta soltanto di una direzione confermata, ma di un possibile **punto di svolta appena confermato**.

## Logica invariata

Nessuna modifica a motore Smart Money, Stato, Score, Alignment, Radar, Focus, Replay storico, Verifica Focus precedente o Price Action Timing.


## Correzione V6.42 — Groq 413 / limite 8K TPM

- Corretto l'errore Groq `413 Request too large` osservato con `openai/gpt-oss-120b` quando la richiesta superava il limite di 8.000 token/minuto.
- Per l'analisi singola con Groq l'app usa una versione compatta ma semanticamente equivalente delle istruzioni di `PROMPT.TXT`; Gemini continua a usare il prompt completo.
- La risposta Groq è limitata a 900 token tramite `max_completion_tokens`, così il budget totale resta prudente.
- Anche lo Screener AI usa un payload Groq compatto e lo stesso limite di completamento.
- Le domande specifiche restano invariate: quando compilate, `PROMPT.TXT` viene ignorato e viene inviata solo la domanda con i dati strutturati.
- Nessuna modifica a motore COT, Stato, Score, Focus, Radar, Replay, Verifica Focus o Price Action Timing.
