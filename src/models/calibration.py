import numpy as np


def normalize_probabilities(probabilities):
    probabilities = np.asarray(
        probabilities,
        dtype=float,
    )

    probabilities = np.clip(
        probabilities,
        1e-8,
        None,
    )

    return probabilities / probabilities.sum(
        axis=-1,
        keepdims=True,
    )


def confidence_from_probability(
    probabilities,
):
    probabilities = normalize_probabilities(
        probabilities
    )

    max_probability = probabilities.max(
        axis=-1
    )

    entropy = -np.sum(
        probabilities *
        np.log(probabilities),
        axis=-1,
    )

    entropy /= np.log(
        probabilities.shape[-1]
    )

    certainty = 1 - entropy

    return (
        0.7 * max_probability
        + 0.3 * certainty
    )