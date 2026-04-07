"""Anxiety risk tracker: feature extraction, training, and inference (standalone)."""

__all__ = ["RiskPredictor", "predict_from_dict"]


def __getattr__(name: str):
    if name in __all__:
        from tracker.predict import RiskPredictor, predict_from_dict

        return {"RiskPredictor": RiskPredictor, "predict_from_dict": predict_from_dict}[name]
    raise AttributeError(name)
