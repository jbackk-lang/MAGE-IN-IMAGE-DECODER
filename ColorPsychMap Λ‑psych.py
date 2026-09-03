"""
Kompatybilność wsteczna — kanoniczna wersja: colorpsychmap_lambda_psych.py.

Ten plik istnieje, bo nazwa ze spacją i znakiem Λ nie da się
zaimportować standardowym `import`. W nowym kodzie importuj
bezpośrednio z colorpsychmap_lambda_psych.
"""
from colorpsychmap_lambda_psych import detect_color_emotion, hue_to_emotion
