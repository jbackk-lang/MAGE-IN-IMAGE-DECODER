"""
fusionengine_v1.py — FusionEngine v1
Łączenie wyników modułów I²D.

Użycie:
    from fusionengine_v1 import fusion_engine
    fusion = fusion_engine(frames, detections)
"""

try:
    from i2d_core import Detection
except ImportError:
    from i2d_core_defectscanner_v2 import Detection


def fusion_engine(frames, detections, block_size=16):
    """
    FusionEngine v1 – łączenie wyników modułów I²D

    - scala detekcje z różnych warstw (L, C, M, F)
    - wykrywa miejsca, gdzie wiele modułów wskazuje na ten sam obszar
    - tworzy mapę fuzji (fusion map)

    Parametry:
        frames      : lista obiektów Frame (z i2d_core)
        detections  : lista obiektów Detection ze wszystkich modułów
        block_size  : rozmiar bloku grupowania (px), domyślnie 16

    Zwraca:
        lista Detection z dtype="fusion" i skumulowaną siłą
    """
    fusion_map = []

    # Grupowanie detekcji po klatkach
    det_by_frame = {}
    for d in detections:
        det_by_frame.setdefault(d.frame_id, []).append(d)

    for f in frames:
        frame_dets = det_by_frame.get(f.id, [])
        if not frame_dets:
            continue

        # Mapa bloków: (bx, by) -> lista detekcji w tym bloku
        block_map = {}
        for d in frame_dets:
            key = (d.x // block_size, d.y // block_size)
            block_map.setdefault(key, []).append(d)

        for (bx, by), det_list in block_map.items():
            # Siła fuzji = suma sił wszystkich detekcji w bloku
            fusion_strength = sum(d.strength for d in det_list)

            # Warstwy obecne w bloku
            layers = list(set(d.layer for d in det_list))

            # Typy sygnałów
            types = list(set(d.dtype for d in det_list))

            desc = f"Fuzja sygnałów: {', '.join(types)} | warstwy: {', '.join(layers)}"

            fusion_map.append(
                Detection(
                    frame_id=f.id,
                    time=f.time,
                    x=bx * block_size,
                    y=by * block_size,
                    dtype="fusion",
                    strength=fusion_strength,
                    layer=",".join(layers),
                    desc=desc,
                )
            )

    return fusion_map
