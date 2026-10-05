"""Kildene. Hver kilde har en funksjon fetch(config) som returnerer en liste
med stillinger i dette felles formatet:

{
    "id": str,               # unik innen kilden, f.eks. "nav:<uuid>"
    "title": str,
    "company": str,
    "location": str,         # by/kommune, kan være tom
    "description": str,      # ren tekst (ikke HTML), kan være tom
    "apply_url": str,        # lenken der man leser/søker
    "published": str,        # ISO-dato "2026-10-05", kan være tom
    "deadline": str | None,  # søknadsfrist slik kilden skriver den
    "extent": str | None,    # "Heltid", "Deltid" eller None hvis ukjent
    "source": str,           # visningsnavn, f.eks. "NAV"
}
"""
