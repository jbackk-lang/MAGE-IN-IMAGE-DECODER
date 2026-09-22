"""
fusionengine_v1.py — FusionEngine v1
Łączenie wyników modułów I²D.

Użycie:
    from fusionengine_v1 import fusion_engine
    fusion = fusion_engine(frames, detections)
"""

from i2d_core import Detection


def _detector_family(dtype):
    """Warianty jednego detektora nie są niezależnymi potwierdzeniami."""
    for prefix in ("spectral", "rhythm", "color"):
        if dtype.startswith(prefix):
            return prefix
    return dtype


def fusion_engine(frames, detections, block_size=16):
    """
    FusionEngine v1 – łączenie wyników modułów I²D

    - scala detekcje z różnych warstw (L, C, M, F)
    - wykrywa miejsca, gdzie wiele modułów wskazuje na ten sam obszar
    - tworzy mapę fuzji tylko przy zgodności co najmniej dwóch rodzin

    Parametry:
        frames      : lista obiektów Frame (z i2d_core)
        detections  : lista obiektów Detection ze wszystkich modułów
        block_size  : rozmiar bloku grupowania (px), domyślnie 16

    Zwraca:
        lista Detection z dtype="fusion"; strength to liczba rodzin,
        a NIE prawdopodobieństwo ani suma nieporównywalnych amplitud
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
            families = {_detector_family(d.dtype) for d in det_list}
            if len(families) < 2:
                continue
            fusion_strength = float(len(families))

            # Warstwy obecne w bloku
            layers = sorted({d.layer for d in det_list})

            # Typy sygnałów
            types = sorted({d.dtype for d in det_list})

            desc = (f"Fuzja {len(families)} rodzin: {', '.join(sorted(families))} "
                    f"| typy: {', '.join(types)} | warstwy: {', '.join(layers)}")

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
