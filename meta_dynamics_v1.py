"""meta_dynamics_v1.py -- META-DYNAMICS (Λ/τ/ρ) na siatce regionow ruchu.

Przeniesienie formalizmu Lambda-tau-rho z ekosystemu TIMDR
(bearing_meta_adapter.py w TIMDR-Industrial-Predict, TIMDR-META-DYNAMICS)
na pole ruchu wideo -- pelna specyfikacja, wzory i uzasadnienie wyborow
sa zamrozone w PREREG_META_DYNAMICS_v0.1.md, PRZED jakimkolwiek uzyciem
na realnych danych UCSD Ped2. Ten plik implementuje DOKLADNIE ten
dokument -- zmiana wzorow bez nowej wersji PREREG jest bledem.

Wykorzystuje ISTNIEJACA infrastrukture repo (Frame.M z split_layers()) --
nie duplikuje wczytywania/roznicy klatek. J (operator skretu) jest
SWIADOMIE POMINIETY (patrz PREREG sekcja 3) -- repo ma juz wlasny
TwistDetector o innej definicji.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple

import numpy as np

MAD_TO_STD = 1.4826  # ta sama stala co w calym ekosystemie TIMDR
ROBUST_K = 3.5        # jw. -- NIE dostrajane pod to zadanie, patrz PREREG #3

DEFAULT_GRID = (4, 4)
DEFAULT_TAU_WINDOW = 4  # +/- w klatek (9-klatkowe okno regresji)


@dataclass
class VideoMetaState:
    frame_id: int
    Lambda: float
    tau: float
    rho: int          # 0/1, binarne (patrz PREREG #3)
    E: float           # calkowita energia ruchu klatki (pomocnicze, do progow)


def region_energy_series(frames, grid: Tuple[int, int] = DEFAULT_GRID) -> np.ndarray:
    """Macierz [n_frames, n_regions] -- e_i(t) = mean(M[region_i]) per
    klatka. Wymaga `split_layers(frames)` wywolanego wczesniej (Frame.M
    musi byc juz policzone)."""
    rows, cols = grid
    n = len(frames)
    n_regions = rows * cols
    energies = np.zeros((n, n_regions), dtype=np.float64)

    for t, f in enumerate(frames):
        if f.M is None:
            raise ValueError(
                f"Frame {f.id}: f.M jest None -- wywolaj split_layers(frames) przed region_energy_series()."
            )
        M = f.M
        h, w = M.shape
        row_edges = np.linspace(0, h, rows + 1).astype(int)
        col_edges = np.linspace(0, w, cols + 1).astype(int)
        idx = 0
        for r in range(rows):
            for c in range(cols):
                region = M[row_edges[r]:row_edges[r + 1], col_edges[c]:col_edges[c + 1]]
                energies[t, idx] = float(np.mean(region)) if region.size else 0.0
                idx += 1

    return energies


def spatial_concentration(energies: np.ndarray) -> np.ndarray:
    """Lambda(t) -- koncentracja entropijna energii miedzy regionami
    (wzor zamrozony w PREREG #3). `energies`: [n_frames, n_regions]."""
    n_frames, n_regions = energies.shape
    h_max = np.log(n_regions)
    lam = np.zeros(n_frames, dtype=np.float64)

    for t in range(n_frames):
        e = energies[t]
        total = e.sum()
        if total <= 1e-12:
            p = np.full(n_regions, 1.0 / n_regions)
        else:
            p = e / total
        nz = p > 0
        H = -np.sum(p[nz] * np.log(p[nz]))
        lam[t] = np.clip(1.0 - H / h_max, 0.0, 1.0)

    return lam


def _local_slope(values: np.ndarray, t: int, w: int) -> float:
    """OLS nachylenie `values` wzgledem indeksu w oknie [t-w, t+w],
    przyciete na brzegach -- patrz PREREG #3 (klatki rownoodlegle w
    indeksie, brak potrzeby _nearest_k_bounds czasowego)."""
    n = len(values)
    lo = max(0, t - w)
    hi = min(n, t + w + 1)
    if hi - lo < 2:
        return 0.0
    idx = np.arange(lo, hi, dtype=np.float64)
    seg = values[lo:hi]
    A = np.column_stack([idx, np.ones_like(idx)])
    try:
        slope, _ = np.linalg.lstsq(A, seg, rcond=None)[0]
    except Exception:
        slope = 0.0
    return float(slope)


def energy_trend(E: np.ndarray, w: int = DEFAULT_TAU_WINDOW) -> np.ndarray:
    """tau(t) dla calej serii E(t) -- patrz _local_slope."""
    return np.array([_local_slope(E, t, w) for t in range(len(E))], dtype=np.float64)


def _mad_threshold(values: np.ndarray, k: float = ROBUST_K) -> float:
    finite = values[np.isfinite(values)]
    if finite.size == 0:
        return 0.0
    med = float(np.median(finite))
    mad = float(np.median(np.abs(finite - med))) * MAD_TO_STD
    return med + k * mad


@dataclass
class ReferenceThresholds:
    lambda_threshold: float
    energy_threshold: float


def compute_reference_thresholds(
    frames_ref, grid: Tuple[int, int] = DEFAULT_GRID, k: float = ROBUST_K
) -> ReferenceThresholds:
    """Progi MAD-owe policzone WYLACZNIE z klatek referencyjnych
    (zdrowych, np. klipy treningowe Ped2) -- patrz PREREG #3/#5. Wymaga
    split_layers(frames_ref) wywolanego wczesniej. `k` domyslnie ROBUST_K
    (stala calego ekosystemu TIMDR) -- parametryzowalne dla kalibracji,
    patrz PREREG_META_DYNAMICS_RHO_CALIBRATION_v0.1.md."""
    energies = region_energy_series(frames_ref, grid=grid)
    lam = spatial_concentration(energies)
    E = energies.sum(axis=1)
    return ReferenceThresholds(
        lambda_threshold=_mad_threshold(lam, k=k),
        energy_threshold=_mad_threshold(E, k=k),
    )


def compute_video_meta_states(
    frames_test,
    thresholds: ReferenceThresholds,
    grid: Tuple[int, int] = DEFAULT_GRID,
    tau_window: int = DEFAULT_TAU_WINDOW,
) -> List[VideoMetaState]:
    """Lista VideoMetaState per klatka testowa, wzgledem progow z
    compute_reference_thresholds(). Wymaga split_layers(frames_test)
    wywolanego wczesniej."""
    energies = region_energy_series(frames_test, grid=grid)
    lam = spatial_concentration(energies)
    E = energies.sum(axis=1)
    tau = energy_trend(E, w=tau_window)

    states = []
    for t, f in enumerate(frames_test):
        rho = int(lam[t] > thresholds.lambda_threshold or E[t] > thresholds.energy_threshold)
        states.append(VideoMetaState(frame_id=f.id, Lambda=float(lam[t]), tau=float(tau[t]), rho=rho, E=float(E[t])))

    return states


# ---------------------------------------------------------------------------
# v0.3: rho per region (PREREG_META_DYNAMICS_v0.3.md)
#
# Diagnoza v0.1/v0.2: rho liczone z GLOBALNYCH Lambda i E nie zadzialalo,
# bo klipy testowe sa ogolnie "ruchliwsze" niz referencja, a prog globalny
# nie odroznia "wiecej pieszych" od "cos nietypowego w jednym miejscu".
# Kamera w Ped2 jest stala, wiec kazdy region siatki ma wlasny, typowy
# poziom ruchu. v0.3: rho(t) = 1, gdy energia ruchu W KTORYMKOLWIEK regionie
# przekracza WLASNY prog tego regionu: mediana_i + k * 1.4826 * MAD_i z
# referencji zdrowej. Stare rho (v0.1/v0.2) zostaje bez zmian obok.
# ---------------------------------------------------------------------------

RHO_V3_K = 5.0      # z kalibracji na zbiorze deweloperskim (PREREG v0.3, sekcja 3)
MAD_FLOOR = 1e-6    # region bez zmiennosci w referencji -> minimalny rozrzut, nie dzielenie przez 0


@dataclass
class RegionReference:
    median: np.ndarray   # [n_regions]
    mad: np.ndarray      # [n_regions], juz przeskalowane * MAD_TO_STD
    k: float
    grid: Tuple[int, int]

    @property
    def thresholds(self) -> np.ndarray:
        return self.median + self.k * self.mad


def compute_region_reference(clips, grid: Tuple[int, int] = DEFAULT_GRID, k: float = RHO_V3_K) -> RegionReference:
    """Referencja per region z jednego klipu (lista Frame) albo z listy klipow.
    Energia liczona osobno w kazdym klipie (roznice klatek nie przechodza
    przez granice klipow), potem laczona."""
    if len(clips) and hasattr(clips[0], "M"):
        clips = [clips]
    return region_reference_from_energies([region_energy_series(c, grid) for c in clips], grid=grid, k=k)


def region_reference_from_energies(energies, grid: Tuple[int, int] = DEFAULT_GRID, k: float = RHO_V3_K) -> RegionReference:
    """Jak compute_region_reference, ale z gotowych macierzy energii [n_frames, n_regions] per klip - pozwala liczyc
    dlugie zbiory klip po klipie bez trzymania wszystkich klatek w pamieci."""
    E = np.concatenate([np.asarray(e, dtype=np.float64) for e in energies], axis=0)
    med = np.median(E, axis=0)
    mad = np.maximum(MAD_TO_STD * np.median(np.abs(E - med), axis=0), MAD_FLOOR)
    return RegionReference(median=med, mad=mad, k=float(k), grid=grid)


def rho_from_energies(E: np.ndarray, ref: RegionReference) -> Tuple[np.ndarray, np.ndarray]:
    exceed = np.asarray(E) > ref.thresholds
    return exceed.any(axis=1).astype(int), exceed


def region_rho_series(frames, ref: RegionReference) -> Tuple[np.ndarray, np.ndarray]:
    """(rho [n_frames] 0/1, exceed [n_frames, n_regions] bool) - ktore regiony
    przekroczyly wlasny prog w danej klatce."""
    return rho_from_energies(region_energy_series(frames, ref.grid), ref)


__all__ = [
    "VideoMetaState",
    "ReferenceThresholds",
    "DEFAULT_GRID",
    "DEFAULT_TAU_WINDOW",
    "region_energy_series",
    "spatial_concentration",
    "energy_trend",
    "compute_reference_thresholds",
    "compute_video_meta_states",
    "RHO_V3_K",
    "RegionReference",
    "compute_region_reference",
    "region_rho_series",
    "region_reference_from_energies",
    "rho_from_energies",
]
