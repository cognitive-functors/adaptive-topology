"""
Distance Oracle — coordinate-first distance computation for Ultra-Scale TSP.

Вместо полной D[N,N] матрицы (80GB для N=100K), используем:
- coords[N,2]: координаты городов (1.6 MB для N=100K)
- k-NN graph via KDTree: индексы + расстояния (24 MB для N=100K, k=20)
- Sparse Laplacian из k-NN графа для спектрального анализа

Память: ~230 MB для N=100K vs 80 GB с полной матрицей.
"""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray
from typing import Optional
from scipy.spatial import cKDTree
from scipy.sparse import csr_matrix, diags
from scipy.sparse.csgraph import laplacian
from scipy.spatial.distance import cdist


class DistanceOracle:
    """
    Coordinate-based distance oracle.
    
    Предоставляет:
    - k-NN graph (indices + distances)
    - Sparse Laplacian для спектрального анализа
    - On-demand sub-distance matrices для segment solver
    - 1-NN distance per city (для SOC stress)
    """
    
    def __init__(self, coords: NDArray[np.float64], knn_k: int = 20):
        self.coords = np.ascontiguousarray(coords, dtype=np.float64)
        self.n = coords.shape[0]
        self.knn_k = min(knn_k, self.n - 1)
        
        self.knn_indices: Optional[NDArray[np.int32]] = None
        self.knn_dists: Optional[NDArray[np.float64]] = None
        self.nn_dists: Optional[NDArray[np.float64]] = None  # 1-NN dist
        self._tree: Optional[cKDTree] = None
        
    def build_knn(self):
        """Build k-NN graph using KDTree. O(N log N) build + O(Nk log N) query."""
        self._tree = cKDTree(self.coords)
        dists, indices = self._tree.query(self.coords, k=self.knn_k + 1)
        # Первый столбец = self (dist=0), пропускаем
        self.knn_indices = indices[:, 1:].astype(np.int32)
        self.knn_dists = dists[:, 1:].astype(np.float64)
        self.nn_dists = self.knn_dists[:, 0].copy()
        
    def dist(self, i: int, j: int) -> float:
        """Distance between two cities. O(1)."""
        dx = self.coords[i, 0] - self.coords[j, 0]
        dy = self.coords[i, 1] - self.coords[j, 1]
        return float(np.sqrt(dx * dx + dy * dy))
    
    def tour_length(self, tour) -> float:
        """Tour length from coordinates. Vectorized O(N)."""
        t = np.asarray(tour)
        c = self.coords[t]
        c_next = self.coords[np.roll(t, -1)]
        return float(np.sqrt(((c - c_next) ** 2).sum(axis=1)).sum())
    
    def sub_matrix(self, cities) -> NDArray[np.float64]:
        """
        Compute dense sub-distance matrix for a subset of cities.
        For segment solver: leaf_size=1000 → sub_D = 8MB.
        """
        idx = np.asarray(cities)
        local_coords = self.coords[idx]
        return cdist(local_coords, local_coords).astype(np.float64)
    
    def sparse_laplacian(self, sigma: Optional[float] = None) -> csr_matrix:
        """
        Build sparse Laplacian from k-NN graph.
        
        Uses Gaussian kernel: w_ij = exp(-d_ij² / (2*sigma²))
        Default sigma = 2 * median(1-NN distances).
        
        Memory: O(N*k) — sparse matrix with ~2*N*k non-zeros.
        """
        if self.knn_indices is None:
            self.build_knn()
            
        n = self.n
        k = self.knn_k
        
        if sigma is None:
            sigma = 2.0 * float(np.median(self.nn_dists))
        sigma_sq_2 = 2.0 * sigma * sigma
        
        # Строим sparse symmetric weight matrix
        rows = []
        cols = []
        vals = []
        
        for i in range(n):
            for ki in range(k):
                j = int(self.knn_indices[i, ki])
                d = self.knn_dists[i, ki]
                w = np.exp(-d * d / sigma_sq_2)
                rows.append(i)
                cols.append(j)
                vals.append(w)
        
        W = csr_matrix((vals, (rows, cols)), shape=(n, n))
        # Symmetrize
        W = (W + W.T) / 2.0
        W.setdiag(0)
        
        # Laplacian: L = D - W
        L = laplacian(W, normed=False)
        return L
    
    def spectral(self, n_vectors: int = 6):
        """
        Compute smallest eigenvectors of sparse Laplacian.
        Uses LOBPCG (preferred) with ARPACK fallback.
        
        Returns:
            (eigenvalues, eigenvectors) sorted ascending.
        """
        L = self.sparse_laplacian()
        n_eig = min(n_vectors, self.n - 2)
        
        try:
            from scipy.sparse.linalg import lobpcg
            # Initial guess
            X0 = np.random.RandomState(42).randn(self.n, n_eig)
            X0[:, 0] = 1.0 / np.sqrt(self.n)
            
            # Jacobi preconditioner
            diag_L = np.array(L.diagonal()).flatten()
            diag_L[diag_L < 1e-10] = 1.0
            M_inv = diags(1.0 / diag_L)
            
            eigenvalues, eigenvectors = lobpcg(
                L, X0, M=M_inv, largest=False, maxiter=300, tol=1e-6,
            )
            idx = np.argsort(eigenvalues)
            return eigenvalues[idx], eigenvectors[:, idx]
            
        except Exception:
            # Fallback to ARPACK
            from scipy.sparse.linalg import eigsh
            eigenvalues, eigenvectors = eigsh(L, k=n_eig, which='SM', maxiter=500)
            idx = np.argsort(eigenvalues)
            return eigenvalues[idx], eigenvectors[:, idx]
    
    def build_alpha_candidates(self, n_iters: int = 50) -> None:
        """
        Alpha-nearness reranking: 1-tree subgradient → alpha values → rerank k-NN.

        Заменяет distance-based k-NN на alpha-nearness k-NN.
        Города с alpha=0 (в MST) идут первыми в candidate list.

        Helsgaun (2000): alpha-nearness captures 95-99% optimal tour edges
        vs 85-90% для distance-based k-NN.
        """
        if self.knn_indices is None:
            self.build_knn()

        from src.core.numba_sparse import subgradient_alpha_jit, rerank_by_alpha_jit

        alpha, pi = subgradient_alpha_jit(
            self.n, self.knn_indices, self.knn_dists, self.coords, n_iters,
        )

        # Сохраняем alpha и pi для диагностики
        self.alpha_values = alpha
        self.pi_values = pi

        # Пересортировка k-NN по alpha (in-place)
        rerank_by_alpha_jit(self.knn_indices, self.knn_dists, alpha)

    def build_alpha_augmented(self, n_iters: int = 50, max_extra: int = 5) -> None:
        """
        Alpha-nearness augment: расширяет k-NN MST-рёбрами (НЕ заменяет порядок).

        Сохраняет distance-based порядок первых k соседей,
        добавляет до max_extra MST-рёбер (alpha≈0) в конец.
        """
        if self.knn_indices is None:
            self.build_knn()

        from src.core.numba_sparse import subgradient_alpha_jit, augment_knn_by_alpha_jit

        alpha, pi = subgradient_alpha_jit(
            self.n, self.knn_indices, self.knn_dists, self.coords, n_iters,
        )
        self.alpha_values = alpha
        self.pi_values = pi

        # Извлекаем MST parent из субградиентной оптимизации
        from src.core.numba_sparse import sparse_kruskal_mst_jit
        n = self.n
        k = self.knn_k

        # Строим edge list из k-NN + pi-weights для MST (vectorized)
        row_idx = np.repeat(np.arange(n, dtype=np.int32), k)
        col_idx = self.knn_indices.ravel().astype(np.int32)
        valid = col_idx >= 0
        edges_from = row_idx[valid]
        edges_to = col_idx[valid]
        edges_weight = (
            self.knn_dists.ravel()[valid] + pi[edges_from] + pi[edges_to]
        )

        mst_parent, _, _, _ = sparse_kruskal_mst_jit(
            n, edges_from, edges_to, edges_weight,
        )

        # Расширяем k-NN
        new_indices, new_dists, new_k = augment_knn_by_alpha_jit(
            self.knn_indices, self.knn_dists, alpha, self.coords,
            mst_parent, max_extra,
        )

        self.knn_indices = new_indices
        self.knn_dists = new_dists
        self.knn_k = new_k

    def query_radius(self, i: int, radius: float) -> NDArray[np.int64]:
        """All cities within radius of city i. Uses KDTree."""
        if self._tree is None:
            self._tree = cKDTree(self.coords)
        return np.array(self._tree.query_ball_point(self.coords[i], radius), dtype=np.int64)
