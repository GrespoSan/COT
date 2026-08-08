# COT Smart Money Python V6.24

Aggiornamento della V6.23 dedicato esclusivamente all'**export Excel del COT Weekly Change Radar**.

## Novità V6.24

L'Excel scaricato dalla pagina **Weekly Change Radar** non è più influenzato dai filtri a video.

Il file Excel contiene sempre **tutti i mercati presenti nella scansione completata**, compresi:

- tutti i verdetti (`DA APPROFONDIRE`, `DA MONITORARE`, `PERDE INTERESSE`, `NESSUNA NOVITÀ — IGNORA`);
- tutte le categorie disponibili nella scansione;
- il foglio generale `Weekly Change Radar`;
- i nove fogli settoriali:
  - `Radar Indici`
  - `Radar Valute`
  - `Radar Metalli`
  - `Radar Energetici`
  - `Radar Tassi`
  - `Radar Crypto`
  - `Radar Agricoli`
  - `Radar Soft`
  - `Radar Bestiame`

I filtri **Verdetto Radar**, **Categoria mercati** e **Mostra anche i mercati senza novità** continuano a modificare soltanto ciò che viene mostrato a video.

Gli export **JPG Top 5 / Top 10 / Totale** continuano invece a rispettare la vista filtrata, perché rappresentano ciò che si sta guardando nella pagina.

Il pulsante Excel è ora denominato **Scarica Radar Excel completo** per rendere evidente questa differenza.

> Nota: l'Excel può includere soltanto i mercati effettivamente analizzati nella scansione. Se prima di avviare lo Screener vengono esclusi interi gruppi o mercati dalla sidebar, questi non possono comparire nell'export.

## Cosa NON cambia

La V6.24 **non modifica**:

- Smart Money Engine;
- Stato dello Screener;
- formula e soglie dello Score;
- logica e verdetti del Weekly Change Radar;
- Alignment 156W;
- Rapid Shift;
- OI 3–6W / OI Index 52W;
- conferma prezzo Weekly;
- Analisi singolo strumento;
- logica AI;
- filtri a video del Radar;
- comportamento degli export JPG.

La modifica riguarda esclusivamente **quale DataFrame viene passato all'export Excel dedicato del Radar**: ora viene usato il Radar completo anziché la vista filtrata.
