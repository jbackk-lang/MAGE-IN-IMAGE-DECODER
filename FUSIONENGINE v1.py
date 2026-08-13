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
    """

    fusion_map = []

    # Grupowanie po klatkach
    det_by_frame = {}
    for d in detections:
        det_by_frame.setdefault(d.frame_id, []).append(d)

    for f in frames:
        frame_dets = det_by_frame.get(f.id, [])
        if not frame_dets:
            continue

        # Mapa bloków: (x,y) -> lista detekcji
        block_map = {}

        for d in frame_dets:
            key = (d.x // block_size, d.y // block_size)
            block_map.setdefault(key, []).append(d)

        # Analiza bloków
        for (bx, by), det_list in block_map.items():

            # Siła fuzji = suma sił wszystkich detekcji w bloku
            fusion_strength = sum(d.strength for d in det_list)

            # Warstwy obecne w bloku
            layers = list(set(d.layer for d in det_list))

            # Typy sygnałów
            types = list(set(d.dtype for d in det_list))

            # Opis fuzji
            desc = f"Fuzja sygnałów: {', '.join(types)} | warstwy: {', '.join(layers)}"

            fusion_map.append(
                Detection(
                    f.id,
                    f.time,
                    bx * block_size,
                    by * block_size,
                    "fusion",
                    fusion_strength,
                    ",".join(layers),
                    desc
                )
            )

    return fusion_map
