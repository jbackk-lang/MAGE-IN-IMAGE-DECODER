"""
Kompatybilność wsteczna — kanoniczna wersja: colorpsychmap_v1.py.

Ten plik istnieje, bo nazwa ze spacją nie da się zaimportować
standardowym `import`. W nowym kodzie importuj bezpośrednio z
colorpsychmap_v1, żeby nie utrzymywać dwóch niezależnych kopii tej
samej logiki (patrz README, sekcja "Nienaprawione, warte uwagi" —
poprawione tym plikiem).
"""
from colorpsychmap_v1 import detect_color
