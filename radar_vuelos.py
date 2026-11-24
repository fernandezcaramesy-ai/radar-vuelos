import json
import os
from datetime import datetime, timezone
import requests

SERPAPI_KEY = os.getenv("SERPAPI_KEY")
AEROPUERTO_ORIGEN = "MAD"  # Madrid (puedes cambiarlo por BCN, AGP, VLC...)
PRESUPUESTO_MAX = 150      # Precio máximo de vuelo en EUR


def buscar_vuelos_google(origen):
    """Consulta Google Travel Explore a través de SerpApi."""
    url = "https://serpapi.com/search.json"
    params = {
        "engine": "google_travel_explore",
        "departure_id": origen,
        "currency": "EUR",
        "hl": "es",
        "gl": "es",
        "type": "1",             # 1 = Ida y vuelta
        "travel_duration": "1",  # 1 = Fin de semana, 2 = 1 semana
        "api_key": SERPAPI_KEY,
    }
    resp = requests.get(url, params=params, timeout=25)
    resp.raise_for_status()
    return resp.json().get("destinations", [])


def calcular_ranking(destinos, noches=3):
    ranking = []

    for d in destinos:
        precio_vuelo = d.get("flight_price")
        if not precio_vuelo or precio_vuelo > PRESUPUESTO_MAX:
            continue

        # Si Google devuelve precio de hotel lo usamos; si no, estimamos 75 €/noche
        hotel_noche = d.get("hotel_price", 75)
        coste_total = round(precio_vuelo + (hotel_noche * noches), 2)

        score_vuelo = max(0, 100 - (precio_vuelo / PRESUPUESTO_MAX) * 100)
        score_hotel = max(0, 100 - (hotel_noche / 150) * 100)
        puntuacion = round((score_vuelo * 0.65) + (score_hotel * 0.35), 1)

        ranking.append({
            "destino": d.get("name", "Desconocido"),
            "pais": d.get("country", ""),
            "origen": AEROPUERTO_ORIGEN,
            "precio_vuelo_eur": precio_vuelo,
            "coste_escapada_3n_eur": coste_total,
            "fecha_salida": d.get("start_date", ""),
            "fecha_regreso": d.get("end_date", ""),
            "foto": d.get("thumbnail", ""),
            "enlace": d.get("link", ""),
            "puntuacion_chollo": puntuacion,
        })

    ranking.sort(key=lambda x: x["puntuacion_chollo"], reverse=True)
    return ranking[:15]


def main():
    if not SERPAPI_KEY:
        raise ValueError("Falta la variable de entorno SERPAPI_KEY")

    destinos = buscar_vuelos_google(AEROPUERTO_ORIGEN)
    top_destinos = calcular_ranking(destinos)

    salida = {
        "actualizado_utc": datetime.now(timezone.utc).isoformat(),
        "origen": AEROPUERTO_ORIGEN,
        "destinos": top_destinos,
    }

    with open("destinos_hoy.json", "w", encoding="utf-8") as f:
        json.dump(salida, f, ensure_ascii=False, indent=2)

    print(f"Ranking actualizado con {len(top_destinos)} destinos.")


if __name__ == "__main__":
    main()
