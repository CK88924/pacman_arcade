import arcade
from menu import GameMenu
from models.classic_mode import ClassicMode
from models.endless_mode import EndlessMode
from models.wave_mode import WaveMode


WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720
TITLE = "Pac-Man Arcade"


class GameWindow(arcade.Window):

    def __init__(self):
        super().__init__(WINDOW_WIDTH, WINDOW_HEIGHT, TITLE)

        self.state = "menu"  # menu / playing / paused / game_over
        self.menu = GameMenu()

        self.mode = None  # 遊戲模式實例
        self.score_text = arcade.Text("Score: 0", 10, 600, arcade.color.WHITE, 18)

    # --------------------------------------------------
    #  遊戲模式切換
    # --------------------------------------------------
    def start_mode(self, mode_name):
        if mode_name == "classic":
            self.mode = ClassicMode()
        elif mode_name == "endless":
            self.mode = EndlessMode()
        elif mode_name == "wave":
            self.mode = WaveMode()

        self.state = "playing"

    # --------------------------------------------------
    #  Keyboard Handling
    # --------------------------------------------------
    def on_key_press(self, key, modifiers):
        if self.state == "menu":
            result = self.menu.handle_input(key)
            if result:
                self.start_mode(result)
            return

        # 遊戲中
        if self.state == "playing":
            if key == arcade.key.ESCAPE:
                self.state = "paused"
                return
            if self.mode:
                self.mode.on_key_press(key, modifiers)

        elif self.state == "paused":
            if key == arcade.key.ESCAPE:
                self.state = "playing"

        elif self.state == "game_over":
            if key == arcade.key.R:
                self.state = "menu"

    # --------------------------------------------------
    #  Update Loop
    # --------------------------------------------------
    def on_update(self, delta_time):
        if self.state != "playing" or not self.mode:
            return

        self.mode.update(delta_time)

        # 更新分數
        self.score_text.value = f"Score: {self.mode.score}"

        # 遊戲結束/勝利
        if self.mode.finished:
            self.state = "game_over"

    # --------------------------------------------------
    #  Render
    # --------------------------------------------------
    def on_draw(self):
        self.clear()

        # ---------------- MENU ----------------
        if self.state == "menu":
            self.menu.draw()
            return

        # ---------------- GAME ----------------
        if self.mode:
            self.mode.draw()
            self.score_text.draw()

        # ---------------- PAUSED ----------------
        if self.state == "paused":
            arcade.draw_text(
                "PAUSED\nESC 回到遊戲",
                WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2,
                arcade.color.YELLOW, 26,
                anchor_x="center", anchor_y="center"
            )

        # ---------------- GAME OVER ----------------
        if self.state == "game_over":
            result = self.mode.result or "GAME OVER"
            arcade.draw_text(
                result,
                WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 40,
                arcade.color.YELLOW, 32,
                anchor_x="center"
            )
            arcade.draw_text(
                f"Score: {self.mode.score}",
                WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 10,
                arcade.color.WHITE, 22,
                anchor_x="center"
            )
            arcade.draw_text(
                "按 R 回主選單",
                WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 60,
                arcade.color.GRAY, 18,
                anchor_x="center"
            )


def main():
    window = GameWindow()
    arcade.run()


if __name__ == "__main__":
    main()
