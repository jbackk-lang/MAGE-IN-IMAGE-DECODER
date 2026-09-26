# Aneks 1 do CLAIM_AUDIT_PREREG.md (zapisany PRZED drugim uruchomieniem audytu)

Pierwszy przebieg: commit e4cd777, raport `CLAIM_AUDIT_v1.md` z analizą post hoc. Po nim:

1. README poprawione: „k = 3,5 zbyt luźna” → „zbyt wysoka” (z wyjaśnieniem); ujawnione wspólne commity pre-rejestracji
   i wyników META/CONTOUR; CDnet — 10 masek (3 bazowe + 7 wariantów); „fuzja nie poprawiła wyniku w praktycznym sensie”
   z różnicami F1; stosunki czasu z powtórki audytu i uwaga, że czasy zależą od maszyny; F1 wszystkich raportów odtwarza
   się co do 4 miejsc; testy — 45 (22 + 23).
2. `RESULT_META_DYNAMICS_v0.1.md`: dopisane erratum na końcu (słowo „luźna” → „wysoka”), bez zmiany liczb i werdyktu.
3. Karty v1.1 (`claims_mage.py`, lista w nagłówku), zmienione PO zobaczeniu wyników przebiegu 1 — drugi przebieg sprawdza
   zgodność poprawionego README z plikami, nie jest niezależnym testem. `RECOMPUTE_MAGE.json` bez zmian.
