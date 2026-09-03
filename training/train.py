from pathlib import Path

import numpy as np
import torch
import torch.nn.functional as F

from torch.utils.data import (
    DataLoader,
    TensorDataset,
)

from src.models.model import StatixModel
from src.models.features import FEATURE_COLUMNS


DATASET = Path("training_dataset.npz")
MODEL_PATH = Path("artifacts/statix_model.pt")

BATCH_SIZE = 256
EPOCHS = 20
LEARNING_RATE = 1e-3


def main():

    data = np.load(
        DATASET
    )

    X = torch.tensor(
        data["X"],
        dtype=torch.float32,
    )

    y_direction = torch.tensor(
        data["y_direction"],
        dtype=torch.long,
    )

    y_returns = torch.tensor(
        data["y_returns"],
        dtype=torch.float32,
    )

    # Chronological split.
    split = int(
        len(X) * 0.85
    )

    train_X = X[:split]
    train_y = y_direction[:split]
    train_r = y_returns[:split]

    valid_X = X[split:]
    valid_y = y_direction[split:]
    valid_r = y_returns[split:]

    train_ds = TensorDataset(
        train_X,
        train_y,
        train_r,
    )

    loader = DataLoader(
        train_ds,
        batch_size=BATCH_SIZE,
        shuffle=True,
        num_workers=0,
    )

    model = StatixModel(
        input_dim=len(
            FEATURE_COLUMNS
        ),
        d_model=96,
    )

    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=LEARNING_RATE,
        weight_decay=1e-4,
    )

    for epoch in range(EPOCHS):

        model.train()

        total_loss = 0.0

        for xb, yb, rb in loader:

            optimizer.zero_grad()

            output = model(xb)

            direction_loss = (
                F.cross_entropy(
                    output["direction"],
                    yb,
                )
            )

            return_loss = (
                F.smooth_l1_loss(
                    output["returns"],
                    rb,
                )
            )

            loss = (
                direction_loss
                + 0.5 * return_loss
            )

            loss.backward()

            torch.nn.utils.clip_grad_norm_(
                model.parameters(),
                1.0,
            )

            optimizer.step()

            total_loss += float(
                loss.detach()
            )

        model.eval()

        with torch.inference_mode():

            validation_output = model(
                valid_X
            )

            predicted = (
                validation_output[
                    "direction"
                ]
                .argmax(dim=1)
            )

            accuracy = (
                predicted == valid_y
            ).float().mean().item()

            return_error = (
                torch.mean(
                    torch.abs(
                        validation_output[
                            "returns"
                        ]
                        - valid_r
                    )
                )
                .item()
            )

        print(
            f"Epoch {epoch + 1}/{EPOCHS} "
            f"loss={total_loss / max(len(loader), 1):.4f} "
            f"val_acc={accuracy:.4f} "
            f"val_return_mae={return_error:.5f}"
        )

    MODEL_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    torch.save(
        {
            "model": model.state_dict(),
            "d_model": 96,
            "feature_columns": FEATURE_COLUMNS,
            "model_version": "statix-v11-patchtst-1",
        },
        MODEL_PATH,
    )

    print(
        "Saved model:",
        MODEL_PATH,
    )


if __name__ == "__main__":
    main()