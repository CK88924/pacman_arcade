from __future__ import annotations

from .base_mode import BaseMode


class ClassicMode(BaseMode):
    """
    經典模式：
    - 豆子與 Power Pellet 不會 respawn
    - 鬼被吃掉後也不會 respawn（吃光豆子＋鬼）
    - 吃光所有豆子＋Power Pellet → 勝利
    """

    def __init__(self) -> None:
        super().__init__()

    def check_post_update(self) -> None:
        # 沒有剩餘豆子 → 勝利
        if len(self.pellets or []) == 0 and len(self.power_pellets or []) == 0:
            self.finished = True
            self.result = "VICTORY"
