# COT Smart Money Python V6.31

## Novità V6.31 — rimosso Heating Oil (HO)

Su richiesta, **HO — Heating Oil** è stato rimosso dall’universo dei mercati selezionabili e dallo screener. È stato eliminato anche dal file `term_structure.csv`, quindi non compare più tra le commodity energetiche gestite dall’app.

La V6.31 **non modifica** motore COT, Stato Screener, Score, Alignment 156W, Weekly Change Radar, Focus Operativo o Verifica Focus precedente. Tutta la logica V6.30 resta invariata.


## Novità V6.30 — aggiornamento CFTC realmente forzato a ogni nuova scansione

La V6.30 nasce da un controllo su un export effettuato subito dopo l'uscita di un nuovo COT: il file conteneva correttamente il foglio **Verifica precedente**, ma lo Screener stava ancora usando la **Data COT 04/08/2026**. Di conseguenza anche Focus e verifica appartenevano ancora al ciclo precedente.

La causa possibile era la cache oraria dei dati CFTC: una scansione eseguita poco prima della nuova pubblicazione poteva mantenere temporaneamente il report precedente anche premendo di nuovo il pulsante di analisi.

La V6.30 corregge questo comportamento senza cambiare il motore quantitativo:

- ogni pressione di **Avvia analisi di tutti i mercati selezionati** svuota esclusivamente le cache dei dati CFTC che possono rendere vecchio il report;
- la nuova scansione interroga quindi nuovamente il dataset CFTC;
- dopo lo Screener viene mostrata chiaramente la **Data COT effettivamente usata**;
- se i mercati hanno date COT diverse viene mostrato un avviso;
- se la data più recente ha 10 o più giorni viene mostrato un avviso specifico: dopo una nuova uscita del venerdì non bisogna considerare Focus/Radar come nuovo ciclo finché la Data COT non cambia;
- il foglio **Verifica precedente** continua a ricostruire il Focus del report immediatamente precedente. Quindi, quando il report corrente passa da 04/08 a 11/08, la verifica passa automaticamente dal Focus 28/07 al Focus 04/08.

La V6.30 **non modifica** analisi singola, Stato Screener, Score, Alignment, Weekly Change Radar, logica Focus V6.29 o regole dei prompt. I prompt vengono solo riallineati al numero di versione.


1. **nuova partecipazione reale** nella direzione del Focus;
2. **movimento misto / bilanciato**;
3. **Short covering / Long liquidation dominante**;
4. origine non classificabile.

Solo dopo vengono considerati:

- nuova conferma / continuazione;
- Score numerico;
- Δ Score;
- ordinamento alfabetico come ultimo spareggio.

La priorità settoriale resta invariata: prima viene mostrato il migliore di ogni settore (`PRINCIPALE`), poi le altre opportunità valide dello stesso comparto (`ALTERNATIVA SETTORE`).

## Segnale flusso motore: ora solo fallback

Il campo `Segnale flusso motore` resta invariato e continua a essere usato dal motore. Nel solo ordinamento Focus, però, non può più sovrascrivere una `Origine Flow 1W` esplicita.

Esempio: se il motore sintetico indica `NUOVI LONG`, ma l'Origine Flow dice che il miglioramento deriva **soprattutto dalla chiusura degli Short**, il candidato viene classificato come **covering dominante**, non come nuova partecipazione Long di massima qualità.

La logica è simmetrica sul lato Short: una **riduzione dei Long dominante** non viene promossa a nuova partecipazione Short soltanto perché il segnale motore è `NUOVI SHORT`.

## Comportamento atteso sul caso reale

Con i dati del Focus del 14/08/2026, l'ordine atteso diventa:

1. CT — Cotton — PRINCIPALE Soft;
2. 6A — Australian Dollar — PRINCIPALE Valute;
3. CC — Cocoa — ALTERNATIVA Soft;
4. SB — Sugar — ALTERNATIVA Soft.

CC precede SB perché la nuova partecipazione Long è più genuina, anche se SB ha Score numerico superiore.

## Cosa non cambia

Restano identici alla V6.28:

- requisiti per entrare in `FOCUS`;
- `LONG/SHORT CONFERMATO` e `NON INSEGUIRE`;
- soglia Score >= 65;
- conferma prezzo Weekly;
- struttura 3W/6W;
- logica `MONITORARE`;
- Focus principale per settore e alternative;
- verifica causale della settimana precedente;
- MFE, MAE e rendimento direzionale;
- Weekly Change Radar;
- export Excel e JPG.

## Verifiche effettuate

- compilazione Python (`py_compile`);
- test simmetrici Long/Short della nuova gerarchia Origine Flow: nuova partecipazione = 0, misto = 1, covering/liquidation dominante = 2;
- test sintetico del caso reale CT / 6A / CC / SB con ordine finale 1 / 2 / 3 / 4;
- confronto AST delle funzioni core per verificare che motore COT, Stato, Score e Weekly Change Radar non siano stati modificati;
- integrità del pacchetto ZIP.

## Nota sui dati

COT: CFTC. Prezzi e verifica settimanale: Yahoo Finance. Feed e calendari possono non coincidere perfettamente con TradingView; la procedura continua a escludere le barre giornaliere non ancora completate.
