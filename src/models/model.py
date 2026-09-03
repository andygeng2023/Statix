import torch
import torch.nn as nn

from src.models.patchtst import PatchTST


class StatixModel(nn.Module):

    def __init__(
        self,
        input_dim: int,
        d_model: int = 96,
    ):
        super().__init__()

        self.temporal = PatchTST(
            input_dim=input_dim,
            d_model=d_model,
        )

        self.shared = nn.Sequential(
            nn.Linear(d_model, 128),
            nn.GELU(),
            nn.LayerNorm(128),
            nn.Dropout(0.1),
        )

        self.direction_head = nn.Linear(
            128,
            5,
        )

        self.return_head = nn.Linear(
            128,
            3,
        )

    def forward(self, x):

        temporal = self.temporal(x)

        hidden = self.shared(temporal)

        direction = self.direction_head(hidden)

        returns = self.return_head(hidden)

        return {
            "direction": direction,
            "returns": returns,
        }