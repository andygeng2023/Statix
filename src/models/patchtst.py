import torch
import torch.nn as nn


class PatchEmbedding(nn.Module):

    def __init__(
        self,
        input_dim: int,
        patch_len: int = 8,
        stride: int = 4,
        d_model: int = 96,
    ):
        super().__init__()

        self.patch_len = patch_len
        self.stride = stride

        self.projection = nn.Linear(
            input_dim * patch_len,
            d_model,
        )

    def forward(self, x):

        # x:
        # [batch, time, features]

        batch, time, features = x.shape

        patches = x.unfold(
            dimension=1,
            size=self.patch_len,
            step=self.stride,
        )

        # [batch, patches, features, patch_len]

        patches = patches.permute(
            0,
            1,
            3,
            2,
        )

        patches = patches.reshape(
            batch,
            patches.shape[1],
            -1,
        )

        return self.projection(patches)


class PatchTST(nn.Module):

    def __init__(
        self,
        input_dim: int,
        d_model: int = 96,
        n_heads: int = 4,
        layers: int = 3,
        patch_len: int = 8,
        stride: int = 4,
        dropout: float = 0.1,
    ):
        super().__init__()

        self.embedding = PatchEmbedding(
            input_dim=input_dim,
            patch_len=patch_len,
            stride=stride,
            d_model=d_model,
        )

        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model,
            nhead=n_heads,
            dim_feedforward=d_model * 4,
            dropout=dropout,
            activation="gelu",
            batch_first=True,
            norm_first=True,
        )

        self.encoder = nn.TransformerEncoder(
            encoder_layer,
            num_layers=layers,
        )

        self.norm = nn.LayerNorm(d_model)

    def forward(self, x):

        x = self.embedding(x)

        x = self.encoder(x)

        x = self.norm(x)

        # Global representation.
        return x.mean(dim=1)