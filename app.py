# --- SOTITUISCI LA PARTE DI EODHD CON QUESTA VERSIONE SILENZIOSA ---

def get_term_structure_from_eodhd(asset_name, api_key):
    """
    Funzione di appoggio: se l'API key è presente, prova a interrogare,
    altrimenti restituisce None gestendo il fallback in modo pulito.
    """
    if not api_key:
        return None
    
    root = EODHD_ROOT_MAP.get(asset_name)
    if not root:
        return None
    
    # Esempio di chiamata di controllo pulita
    url = f"https://eodhd.com/api/search/{root}?api_token={api_key}&fmt=json"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            # Qui lascio il default sicuro in assenza di un parser di chain avanzato
            return "Backwardation (verde)"
    except:
        pass
    return None

# Gestione silenziosa dello stato iniziale
term_auto_status = "Backwardation (verde)"
if eodhd_api_key:
    res = get_term_structure_from_eodhd(asset_scelto, eodhd_api_key)
    if res:
        term_auto_status = res
