# COT Smart Money Python V6.18

Aggiornamento testuale della V6.17 dopo verifica con il COT del 04/08/2026.

## Modifica V6.18

Nessuna modifica a motore Smart Money, Stato, Score o logica dello screener.

È stata corretta la lettura dei casi in cui il quadro complessivo è già confermato ma l’ultimo report deriva dalla chiusura di posizioni:

- **LONG CONFERMATO + SHORT COVERING**: il Long resta confermato; si precisa che l’ultimo impulso è meno robusto perché deriva soprattutto dalla chiusura degli Short e non da nuovi Long. Non viene più chiesta una conferma prezzo già presente.
- **SHORT CONFERMATO + LIQUIDAZIONE LONG**: lo Short resta confermato; si precisa che l’ultimo impulso è meno robusto perché deriva soprattutto dalla chiusura dei Long e non da nuovi Short. Non viene più chiesta una conferma prezzo già presente.

Se short covering o liquidazione Long compaiono senza un quadro già confermato, resta la lettura prudente precedente.

Aggiornati anche `PROMPT.TXT` e `PROMPT_SCREENER.TXT` per impedire all’AI di confondere chiusura di posizioni con nuova accumulazione e per evitare la frase contraddittoria “attendi conferma del prezzo” quando lo Stato è già confermato.
