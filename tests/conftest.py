import os
import sys

# Repo nie jest zainstalowanym pakietem (luźne pliki .py w katalogu
# głównym) — dorzuć katalog główny do sys.path, żeby `import i2d_core`
# itd. działało niezależnie od tego, skąd odpalane jest pytest.
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)
