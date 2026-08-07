# COT Smart Money Python V6.19

Micro-aggiornamento testuale della V6.18.

## Modifica V6.19

Nessuna modifica a:

- motore Smart Money;
- Stato dello screener;
- Score;
- Alignment 156W;
- logica dei flussi;
- classificazione della graduatoria.

Sono stati eliminati dalle indicazioni operative i riferimenti a livelli tecnici che la dashboard Python non calcola.

In particolare:

- `SHORT CONFERMATO — NON INSEGUIRE`: ora invita ad attendere **un rimbalzo e una nuova conferma ribassista**, senza indicare livelli non calcolati;
- `LONG CONFERMATO — NON INSEGUIRE`: ora invita ad attendere **un pullback e una nuova conferma rialzista**, senza indicare livelli non calcolati;
- il possibile minimo Commodity non usa più la formula “conferme Long sui supporti”, ma la più neutra **“cerca conferme Long”**;
- `PROMPT.TXT` e `PROMPT_SCREENER.TXT` vietano all'AI di attribuire livelli tecnici non presenti nei dati e le chiedono di usare soltanto formulazioni generiche come pullback, rimbalzo e nuova conferma.

La modifica è esclusivamente testuale: Stato e Score devono restare identici alla V6.18 a parità di dati.
