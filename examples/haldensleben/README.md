# Haldensleben Gleistopologie - Beispieldatei

## Übersicht

Die Datei `haldensleben.json` enthält eine reale Gleistopologie des Bahnhofs Haldensleben, extrahiert aus OpenStreetMap-Daten.

## Datenstruktur

### Nodes (Knoten)
- **270 Knoten** (von ursprünglich 605)
- Jeder Knoten repräsentiert einen Punkt im Gleisnetz
- Koordinaten in EPSG:3857 (Web Mercator)

**Knotentypen:**
- `railway=stop`: Haltepunkte (Gleis 1, Gleis 2)
- `railway=switch`: Weichen (mit Referenznummern)
- `railway=level_crossing`: Bahnübergänge
- `railway=buffer_stop`: Prellböcke
- `railway=signal`: Signale

**Beispiel-Knoten:**
```json
{
  "name": "N_447379843",
  "x": 1269736.1605721754,
  "y": 6851817.151734603,
  "osm_local_ref": "2",
  "osm_name": "Haldensleben",
  "osm_railway": "stop",
  "interior": true
}
```

### Tracks (Gleise)
- **278 Gleissegmente** (von ursprünglich 619)
- Verbinden jeweils zwei Knoten
- Enthalten OSM-Metadaten

**Gleistypen:**
- `usage=main`: Hauptgleise
- `service=siding`: Nebengleise
- `service=yard`: Rangiergleise

**Beispiel-Gleis:**
```json
{
  "name": "Track_319161053_seg8",
  "start_node": "N_7598337086",
  "end_node": "N_447379843",
  "osm_railway": "rail",
  "osm_gauge": "1435",
  "osm_maxspeed": "100",
  "osm_usage": "main",
  "crosses_boundary": false
}
```

### Polygon
Begrenzungspolygon des ausgeschnittenen Bereichs (7 Eckpunkte)

### Stats
```json
{
  "original_nodes": 605,
  "original_tracks": 619,
  "clipped_nodes": 270,
  "clipped_tracks": 278,
  "interior_nodes": 263,
  "boundary_crossing_tracks": 9
}
```

## Verwendung im MVP

### ❌ NICHT für MVP
Diese Datei ist **NICHT Teil des MVP**. Der MVP verwendet ein **vereinfachtes Track-Modell** ohne detaillierte Gleistopologie.

### ✅ Für Post-MVP / Vollversion
Diese Datei kann in der Vollversion verwendet werden für:
- **Realistische Gleislayouts**: Import echter Bahnhofsstrukturen
- **Visualisierung**: 2D-Darstellung der Gleistopologie
- **Kapazitätsplanung**: Analyse von Engpässen basierend auf realer Infrastruktur
- **Rangierlogik**: Detaillierte Simulation von Rangieroperationen

## Datenquelle

- **Quelle**: OpenStreetMap (OSM)
- **Bahnhof**: Haldensleben, Deutschland
- **Operator**: DB InfraGO AG
- **Spurweite**: 1435mm (Normalspur)
- **Elektrifizierung**: Nicht elektrifiziert (geplant: 15kV 16.7Hz)

## Konvertierung für MVP

Um diese Datei für den MVP zu nutzen, müsste sie vereinfacht werden:

```python
# Beispiel: Extraktion von Werkstattgleisen
def extract_workshop_tracks(topology_data):
    """Konvertiert OSM-Topologie zu MVP WorkshopTrackConfig"""
    tracks = []

    # Filtere Rangiergleise (service=yard)
    yard_tracks = [
        t for t in topology_data["tracks"]
        if t.get("osm_service") == "yard"
    ]

    # Gruppiere zu logischen Werkstattgleisen
    for i, track_group in enumerate(group_tracks(yard_tracks)):
        tracks.append({
            "id": f"TRACK{i+1:02d}",
            "capacity": estimate_capacity(track_group),
            "retrofit_time_min": 30  # Default
        })

    return tracks
```

## Weitere Informationen

- **OSM-Relation**: Bahnhof Haldensleben
- **Koordinatensystem**: EPSG:3857 (Web Mercator)
- **Dateiformat**: JSON
- **Dateigröße**: ~200KB

---

**Status**: Beispieldatei für zukünftige Entwicklung | **MVP**: Nicht verwendet | **Vollversion**: Geplant
