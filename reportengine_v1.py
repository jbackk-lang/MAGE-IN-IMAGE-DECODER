"""
reportengine_v1.py — ReportEngine v1
Generowanie raportu tekstowego I²D.

Kanoniczna nazwa pliku (patrz "REPORTENGINE v1.py" — cienki re-eksport
zachowany dla wstecznej zgodności, bo nazwa ze spacją nie da się
zaimportować standardowym `import`).

Użycie:
    from reportengine_v1 import report_engine
"""


def report_engine(frames, detections, fusion, top_n=20):
    """
    ReportEngine v1 – generowanie raportu tekstowego I²D
    - podsumowanie detekcji
    - statystyki warstw
    - statystyki typów sygnałów
    - ranking najsilniejszych punktów
    - analiza fuzji
    """

    report = []
    report.append("=== RAPORT I²D ===\n")

    # ------------------------------------------------------------
    # 1. PODSUMOWANIE OGÓLNE
    # ------------------------------------------------------------
    report.append(f"Liczba klatek: {len(frames)}")
    report.append(f"Liczba detekcji: {len(detections)}")
    report.append(f"Liczba punktów fuzji: {len(fusion)}\n")

    # ------------------------------------------------------------
    # 2. STATYSTYKI WARSTW
    # ------------------------------------------------------------
    layer_stats = {}
    for d in detections:
        layer_stats[d.layer] = layer_stats.get(d.layer, 0) + 1

    report.append("=== Statystyki warstw ===")
    for layer, count in layer_stats.items():
        report.append(f"{layer}: {count}")
    report.append("")

    # ------------------------------------------------------------
    # 3. STATYSTYKI TYPÓW SYGNAŁÓW
    # ------------------------------------------------------------
    type_stats = {}
    for d in detections:
        type_stats[d.dtype] = type_stats.get(d.dtype, 0) + 1

    report.append("=== Typy sygnałów ===")
    for t, count in type_stats.items():
        report.append(f"{t}: {count}")
    report.append("")

    # ------------------------------------------------------------
    # 4. NAJSILNIEJSZE DETEKCJE
    # ------------------------------------------------------------
    strongest = sorted(detections, key=lambda d: d.strength, reverse=True)[:top_n]

    report.append(f"=== Top {top_n} najsilniejszych detekcji ===")
    for d in strongest:
        report.append(
            f"[Frame {d.frame_id} | t={d.time:.3f}s] "
            f"({d.x},{d.y}) | {d.dtype} | warstwa {d.layer} | siła {d.strength:.2f}"
        )
    report.append("")

    # ------------------------------------------------------------
    # 5. ANALIZA FUZJI
    # ------------------------------------------------------------
    report.append("=== Punkty fuzji (najbardziej podejrzane miejsca) ===")

    fusion_sorted = sorted(fusion, key=lambda d: d.strength, reverse=True)

    for d in fusion_sorted[:top_n]:
        report.append(
            f"[Frame {d.frame_id} | t={d.time:.3f}s] "
            f"({d.x},{d.y}) | siła fuzji {d.strength:.2f} | {d.desc}"
        )

    report.append("")

    # ------------------------------------------------------------
    # 6. ZWROT RAPORTU
    # ------------------------------------------------------------
    return "\n".join(report)
