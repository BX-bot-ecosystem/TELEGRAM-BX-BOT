from . import base

class OnlyGains(base.Committee):
    def __init__(self):
        super().__init__(
            "OnlyGains"
        )