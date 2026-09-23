"""Locating the model artifacts bundled inside the installed package."""
from importlib.resources import files


def default_model_dir():
    """Absolute path to the models shipped with this package.

    Used whenever a predictor is constructed without an explicit ``model_dir``,
    so that ``LGBMForecaster()`` works straight after ``pip install``.
    """
    return str(files(__package__) / 'models')
