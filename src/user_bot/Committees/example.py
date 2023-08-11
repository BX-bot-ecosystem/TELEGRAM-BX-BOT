from user_bot.Committees import base


class Example(base.Committee):
    def __init__(self):
        super().__init__(
            'example',
        )
    