from __future__ import annotations

from .base_mode import BaseMode
from constants import GHOST_SPEED
from ghost_ai import Ghost


class WaveMode(BaseMode):
    """
    Wave / Roguelike 模式：
    - 吃光所有豆子 → 直接重生新地圖進入下一層 Wave
    - 每一層 Wave 提高鬼速度、縮短 frightened 時間
    - 當層被吃掉的鬼不 respawn，但進入下一層時會重新生成
    """

    def __init__(self) -> None:
        self.wave: int = 1
        super().__init__()
        self._apply_wave_buff()

    def _apply_wave_buff(self) -> None:
        """根據 Wave 強化鬼的能力"""
        if not self.ghosts:
            return

        speed_factor = 1.0 + 0.15 * (self.wave - 1)
        for ghost in self.ghosts:
            ghost: Ghost
            ghost.speed = GHOST_SPEED * speed_factor
            # 縮短 frightened 時間（如果有這個屬性）
            if hasattr(ghost, "frightened_duration"):
                ghost.frightened_duration = max(
                    180, int(ghost.frightened_duration - 60 * (self.wave - 1))
                )

    def next_wave(self) -> None:
        """進入下一層 Wave：重生地圖與鬼、保留分數"""
        self.wave += 1
        # 重建世界（會重設鬼／豆子／牆），但不重置分數
        self.setup_world()
        self._apply_wave_buff()

    def handle_ghost_eaten(self, ghost: Ghost) -> None:
        """
        Wave 模式：當層內吃掉鬼後不 respawn，
        要到進入下一層 Wave 時才重新生出新鬼。
        """
        ghost.remove_from_sprite_lists()
        self.score += 200

    def check_post_update(self) -> None:
        # 沒有剩餘豆子 → 進入下一層 Wave 並給 bonus
        if len(self.pellets or []) == 0 and len(self.power_pellets or []) == 0:
            # 小小過關獎勵
            self.score += 500 * self.wave
            self.next_wave()
