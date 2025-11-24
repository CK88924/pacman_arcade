from __future__ import annotations

import random
from typing import List, Dict, Any

from .base_mode import BaseMode
from item import Pellet, PowerPellet
from constants import TILE_SIZE
from ghost_ai import Ghost


class EndlessMode(BaseMode):
    """
    無限模式：
    - 豆子 / Power Pellet 會在一段時間後 respawn
    - 鬼被吃掉「會重生」
    - 沒有勝利條件，玩家死掉才結束
    """

    PELLET_RESPAWN_FRAMES = 15 * 60   # 15 秒
    POWER_RESPAWN_FRAMES = 60 * 60   # 60 秒
    GHOST_RESPAWN_FRAMES = 2 * 60    # 2 秒

    def __init__(self) -> None:
        # 豆子 / 鬼 respawn 佇列
        self._respawn_queue: List[Dict[str, Any]] = []
        self._ghost_respawn_queue: List[Dict[str, Any]] = []
        super().__init__()

    # ---------- respawn 管理 ----------

    def _queue_pellet_respawn(self, sprite, kind: str) -> None:
        x = sprite.center_x - TILE_SIZE / 2
        y = sprite.center_y - TILE_SIZE / 2
        if kind == "pellet":
            timer = self.PELLET_RESPAWN_FRAMES
        else:
            timer = self.POWER_RESPAWN_FRAMES
        self._respawn_queue.append({"x": x, "y": y, "kind": kind, "timer": timer})

    def _update_pellet_respawn(self) -> None:
        """處理豆子 / Power pellet 重生"""
        for entry in list(self._respawn_queue):
            entry["timer"] -= 1
            if entry["timer"] <= 0:
                if entry["kind"] == "pellet":
                    self.pellets.append(Pellet(entry["x"], entry["y"]))  # type: ignore[arg-type]
                else:
                    self.power_pellets.append(PowerPellet(entry["x"], entry["y"]))  # type: ignore[arg-type]
                self._respawn_queue.remove(entry)

    def _queue_ghost_respawn(self, ghost: Ghost) -> None:
        """排程鬼魂重生"""
        color = getattr(ghost, "ghost_color", "red")
        self._ghost_respawn_queue.append(
            {"timer": self.GHOST_RESPAWN_FRAMES, "color": color}
        )

    def _update_ghost_respawn(self) -> None:
        """根據排程在地圖上重新生成鬼魂"""
        for entry in list(self._ghost_respawn_queue):
            entry["timer"] -= 1
            if entry["timer"] <= 0:
                # 選一個出生點；若沒有記錄就隨機從玩家附近
                if self.ghost_spawn_points:
                    x, y = random.choice(self.ghost_spawn_points)
                else:
                    # fallback：玩家附近
                    x = self.player.center_x - TILE_SIZE  # type: ignore[union-attr]
                    y = self.player.center_y             # type: ignore[union-attr]
                ghost = Ghost(x, y, entry["color"])
                ghost.validate_and_set_direction(self.walls)  # type: ignore[arg-type]
                self.ghosts.append(ghost)  # type: ignore[arg-type]
                self._ghost_respawn_queue.remove(entry)

    # ---------- 覆寫掛鉤 ----------

    def update(self, delta_time: float) -> None:
        # 先處理 respawn 計時
        self._update_pellet_respawn()
        self._update_ghost_respawn()
        # 再跑基礎 update
        super().update(delta_time)

    def handle_pellet_eaten(self, pellet: Pellet) -> None:
        # 照常加分
        super().handle_pellet_eaten(pellet)
        # 並排入 respawn 排程
        self._queue_pellet_respawn(pellet, "pellet")

    def handle_power_pellet_eaten(self, power: PowerPellet) -> None:
        super().handle_power_pellet_eaten(power)
        self._queue_pellet_respawn(power, "power")

    def handle_ghost_eaten(self, ghost: Ghost) -> None:
        """
        Endless 模式：吃掉鬼 → 消失一段時間再 respawn
        """
        self.score += 200
        # 先移出地圖
        ghost.remove_from_sprite_lists()
        # 安排重生
        self._queue_ghost_respawn(ghost)

    def check_post_update(self) -> None:
        # Endless 模式沒有勝利條件
        return
