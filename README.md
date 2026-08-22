# COT Smart Money Python V6.43

Base: V6.42.

## Novità V6.43

### Focus operativo — testo più chiaro
- Titolo sezione modificato da `Punti di svolta interessanti, ma non ancora maturi` a `Punti di svolta interessanti, da monitorare`.
- La riga `Segnali anticipatori prioritari da aprire sul grafico...` viene evidenziata in rosso per renderla immediatamente visibile.
- La riga resta una watchlist: non è un ingresso automatico.

### Groq — analisi completa resa di nuovo utile
La V6.42 evitava il 413 riducendo troppo la risposta. In V6.43 la strategia cambia:
- Gemini continua a ricevere il payload completo e `PROMPT.TXT` integrale.
- Groq riceve un pacchetto dati dedicato molto più piccolo, con i campi decisionali essenziali già calcolati dalla dashboard.
- Il budget massimo della risposta Groq per l'analisi singola sale da 900 a 1800 token.
- Lo Screener Groq usa un budget separato di 1200 token.
- La risposta completa Groq deve includere posizione Fondi, ultimo report, struttura 3–6W, estremi COT, OI, Top 8, Alignment/regime, Weekly/Daily21, elemento favorevole/contrario, conferma necessaria, invalidazione e cosa fare.
- Anche le domande specifiche Groq usano il pacchetto dati compatto, evitando di inviare l'intero payload Gemini.

Questa modifica riduce i token di input invece di sacrificare quasi tutta la risposta. Non garantisce che Groq produca una qualità identica a Gemini: i due modelli restano diversi. Per l'analisi completa Gemini rimane il riferimento; Groq è un'alternativa/fallback più utilizzabile.

## Logica quantitativa invariata
Nessuna modifica a motore Smart Money, Stato, Score, Alignment, Radar, Focus, Early Warning/Reversal Watch, Replay storico, Verifica Focus precedente o Price Action Timing.
