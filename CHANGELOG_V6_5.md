# Changelog V6.5

## Calcoli

```python
counter_rapid_shift_6w = counter_index - counter_index.shift(6)
```

```python
oi_index_52w = 100 * (oi - rolling_min_52) / (rolling_max_52 - rolling_min_52)
```

Se massimo e minimo dell'Open Interest coincidono, l'indice assume valore 50.

## Soglie Rapid Shift

- `>= +40`: RAPIDO RIALZISTA
- `+20 / +39,9`: IN ACCELERAZIONE
- `-19,9 / +19,9`: NORMALE
- `-39,9 / -20`: IN PEGGIORAMENTO
- `<= -40`: RAPIDO RIBASSISTA

## Soglie OI Index 52W

- `80–100`: PARTECIPAZIONE MOLTO ALTA
- `60–79,9`: PARTECIPAZIONE ALTA
- `40–60`: PARTECIPAZIONE NELLA MEDIA
- `20,1–40`: PARTECIPAZIONE BASSA
- `0–20`: PARTECIPAZIONE MOLTO BASSA
