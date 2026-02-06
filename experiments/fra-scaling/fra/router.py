"""
FRA Router - learns to select best strategy based on instance fingerprint.
"""

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import json


@dataclass
class RouterConfig:
    """Router configuration."""
    input_dim: int  # Fingerprint dimension
    n_strategies: int  # Number of strategies to choose from
    hidden_layers: List[int] = None
    dropout: float = 0.2
    learning_rate: float = 0.001
    epochs: int = 50
    batch_size: int = 32
    early_stopping_patience: int = 10

    def __post_init__(self):
        if self.hidden_layers is None:
            self.hidden_layers = [128, 64]


class MLPRouter(nn.Module):
    """MLP-based strategy router."""

    def __init__(self, config: RouterConfig):
        super().__init__()
        self.config = config

        layers = []
        prev_dim = config.input_dim

        for hidden_dim in config.hidden_layers:
            layers.extend([
                nn.Linear(prev_dim, hidden_dim),
                nn.ReLU(),
                nn.Dropout(config.dropout)
            ])
            prev_dim = hidden_dim

        layers.append(nn.Linear(prev_dim, config.n_strategies))

        self.network = nn.Sequential(*layers)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.network(x)

    def predict(self, fingerprints: np.ndarray) -> np.ndarray:
        """Predict best strategy indices."""
        self.eval()
        with torch.no_grad():
            x = torch.FloatTensor(fingerprints)
            logits = self.forward(x)
            return torch.argmax(logits, dim=1).numpy()

    def predict_proba(self, fingerprints: np.ndarray) -> np.ndarray:
        """Predict strategy probabilities."""
        self.eval()
        with torch.no_grad():
            x = torch.FloatTensor(fingerprints)
            logits = self.forward(x)
            return torch.softmax(logits, dim=1).numpy()


class FRARouter:
    """
    Fingerprint-Route-Adapt Router.

    Given instance fingerprints and strategy performance data,
    learns to route instances to the best strategy.
    """

    def __init__(self, config: RouterConfig):
        self.config = config
        self.model = MLPRouter(config)
        self.strategy_names: List[str] = []
        self.feature_mean: Optional[np.ndarray] = None
        self.feature_std: Optional[np.ndarray] = None

    def fit(
        self,
        fingerprints: np.ndarray,
        strategy_performance: Dict[str, np.ndarray],
        val_split: float = 0.2
    ) -> Dict:
        """
        Train the router.

        Args:
            fingerprints: (N, d) array of instance fingerprints
            strategy_performance: {strategy_name: (N,) array of performance values}
                                  Lower is better (gaps/times)
            val_split: Validation split ratio

        Returns:
            Training history
        """
        # Normalize fingerprints
        self.feature_mean = fingerprints.mean(axis=0)
        self.feature_std = fingerprints.std(axis=0) + 1e-8
        X = (fingerprints - self.feature_mean) / self.feature_std

        # Find best strategy per instance
        self.strategy_names = list(strategy_performance.keys())
        perf_matrix = np.stack([strategy_performance[s] for s in self.strategy_names], axis=1)

        # Handle NaN/inf
        perf_matrix = np.nan_to_num(perf_matrix, nan=1e6, posinf=1e6, neginf=-1e6)

        # Best = lowest value (gap or time)
        y = np.argmin(perf_matrix, axis=1)

        # Train/val split
        n = len(X)
        indices = np.random.permutation(n)
        val_size = int(n * val_split)
        train_idx, val_idx = indices[val_size:], indices[:val_size]

        X_train, y_train = X[train_idx], y[train_idx]
        X_val, y_val = X[val_idx], y[val_idx]

        # Create dataloaders
        train_ds = TensorDataset(torch.FloatTensor(X_train), torch.LongTensor(y_train))
        val_ds = TensorDataset(torch.FloatTensor(X_val), torch.LongTensor(y_val))

        train_loader = DataLoader(train_ds, batch_size=self.config.batch_size, shuffle=True)
        val_loader = DataLoader(val_ds, batch_size=self.config.batch_size)

        # Training
        optimizer = torch.optim.Adam(self.model.parameters(), lr=self.config.learning_rate)
        criterion = nn.CrossEntropyLoss()

        history = {"train_loss": [], "val_loss": [], "val_acc": []}
        best_val_loss = float('inf')
        patience_counter = 0

        for epoch in range(self.config.epochs):
            # Train
            self.model.train()
            train_loss = 0
            for batch_x, batch_y in train_loader:
                optimizer.zero_grad()
                logits = self.model(batch_x)
                loss = criterion(logits, batch_y)
                loss.backward()
                optimizer.step()
                train_loss += loss.item()

            train_loss /= len(train_loader)

            # Validate
            self.model.eval()
            val_loss = 0
            correct = 0
            total = 0
            with torch.no_grad():
                for batch_x, batch_y in val_loader:
                    logits = self.model(batch_x)
                    loss = criterion(logits, batch_y)
                    val_loss += loss.item()
                    preds = torch.argmax(logits, dim=1)
                    correct += (preds == batch_y).sum().item()
                    total += len(batch_y)

            val_loss /= len(val_loader)
            val_acc = correct / total

            history["train_loss"].append(train_loss)
            history["val_loss"].append(val_loss)
            history["val_acc"].append(val_acc)

            # Early stopping
            if val_loss < best_val_loss:
                best_val_loss = val_loss
                patience_counter = 0
                best_state = {k: v.cpu().clone() for k, v in self.model.state_dict().items()}
            else:
                patience_counter += 1
                if patience_counter >= self.config.early_stopping_patience:
                    self.model.load_state_dict(best_state)
                    break

        return history

    def route(self, fingerprints: np.ndarray) -> List[str]:
        """Route instances to strategies."""
        # Normalize
        X = (fingerprints - self.feature_mean) / self.feature_std
        indices = self.model.predict(X)
        return [self.strategy_names[i] for i in indices]

    def evaluate(
        self,
        fingerprints: np.ndarray,
        strategy_performance: Dict[str, np.ndarray]
    ) -> Dict:
        """
        Evaluate router performance.

        Returns:
            - fra_gap: Average gap achieved by FRA
            - best_single_gap: Average gap of best single strategy
            - oracle_gap: Average gap of perfect routing (oracle)
            - routing_accuracy: How often FRA picks the best strategy
        """
        # Normalize
        X = (fingerprints - self.feature_mean) / self.feature_std

        # Get FRA predictions
        pred_indices = self.model.predict(X)

        # Build performance matrix
        perf_matrix = np.stack([strategy_performance[s] for s in self.strategy_names], axis=1)
        perf_matrix = np.nan_to_num(perf_matrix, nan=1e6, posinf=1e6, neginf=-1e6)

        n = len(fingerprints)

        # FRA performance
        fra_perf = np.array([perf_matrix[i, pred_indices[i]] for i in range(n)])
        fra_gap = np.mean(fra_perf)

        # Best single strategy (virtual best solver)
        strategy_means = perf_matrix.mean(axis=0)
        best_single_idx = np.argmin(strategy_means)
        best_single_gap = strategy_means[best_single_idx]
        best_single_name = self.strategy_names[best_single_idx]

        # Oracle (always picks best for each instance)
        oracle_perf = perf_matrix.min(axis=1)
        oracle_gap = np.mean(oracle_perf)

        # Routing accuracy
        best_indices = np.argmin(perf_matrix, axis=1)
        routing_accuracy = (pred_indices == best_indices).mean()

        return {
            "fra_gap": fra_gap,
            "best_single_gap": best_single_gap,
            "best_single_name": best_single_name,
            "oracle_gap": oracle_gap,
            "routing_accuracy": routing_accuracy,
            "improvement_over_single": (best_single_gap - fra_gap) / best_single_gap * 100 if best_single_gap > 0 else 0,
            "gap_to_oracle": (fra_gap - oracle_gap) / oracle_gap * 100 if oracle_gap > 0 else 0
        }

    def save(self, path: str):
        """Save router to file."""
        torch.save({
            "model_state": self.model.state_dict(),
            "config": self.config,
            "strategy_names": self.strategy_names,
            "feature_mean": self.feature_mean,
            "feature_std": self.feature_std
        }, path)

    @classmethod
    def load(cls, path: str) -> "FRARouter":
        """Load router from file."""
        data = torch.load(path)
        router = cls(data["config"])
        router.model.load_state_dict(data["model_state"])
        router.strategy_names = data["strategy_names"]
        router.feature_mean = data["feature_mean"]
        router.feature_std = data["feature_std"]
        return router
