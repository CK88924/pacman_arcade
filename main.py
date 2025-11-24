# main.py
import arcade

# 修正 import 路徑 - 從 models package 中匯入
from constants import SCREEN_WIDTH, SCREEN_HEIGHT, COLOR_BG, TILE_SIZE 
from models.classic_mode import ClassicMode
from models.endless_mode import EndlessMode
from models.wave_mode import WaveMode
from menu import GameMenu

class PacManGame(arcade.Window):
    """
    主遊戲 Window：
    - MENU 狀態：選擇 Classic / Endless / Wave
    - PLAYING 狀態：把鍵盤 & update 轉發給當前模式物件
    - END 狀態：顯示 GAME OVER / VICTORY，按 R 回主選單
    """

    def __init__(self):
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, "Arcade Pac-Man")
        arcade.set_background_color(COLOR_BG)

        # 狀態機
        self.state = "MENU"      # "MENU" / "PLAYING" / "END"
        self.end_reason = None   # "GAME_OVER" / "VICTORY" / None

        # 使用 GameMenu 物件
        self.menu = GameMenu()
        
        # 當前模式物件（ClassicMode / EndlessMode / WaveMode）
        self.mode = None

        # 鍵盤映射
        self.key_map = {
            arcade.key.UP: (0, 1),
            arcade.key.DOWN: (0, -1),
            arcade.key.LEFT: (-1, 0),
            arcade.key.RIGHT: (1, 0),
        }


    def on_draw(self):
        arcade.start_render()

        if self.state == "MENU":
            self.menu.draw()

        elif self.state == "PLAYING" and self.mode is not None:
            self.mode.draw()
            self._draw_score()

        elif self.state == "END":
            self._draw_end_screen()


    def update(self, delta_time):
        if self.state == "PLAYING" and self.mode is not None:
            self.mode.update(delta_time)
            
            # 檢查遊戲模式是否結束
            if self.mode.finished:
                self.end_reason = self.mode.result
                self.state = "END"


    def on_key_press(self, key, modifiers):
        
        if self.state == "MENU":
            mode_name = self.menu.handle_input(key)
            
            if mode_name:
                # 取得選定的模式類別
                if mode_name == "classic":
                    ModeClass = ClassicMode
                elif mode_name == "endless":
                    ModeClass = EndlessMode
                elif mode_name == "wave":
                    ModeClass = WaveMode
                else:
                    return

                # 實例化並啟動遊戲
                self.mode = ModeClass()
                self.state = "PLAYING"
                
        elif self.state == "PLAYING" and self.mode is not None:
            
            # 玩家移動控制
            if key in self.key_map:
                dx, dy = self.key_map[key]
                self.mode.player.next_change_x = dx
                self.mode.player.next_change_y = dy
                
        elif self.state == "END":
            if key == arcade.key.R:
                # 重設狀態回主選單
                self.state = "MENU"
                self.mode = None
                self.end_reason = None
                self.menu.index = 0


    def _draw_score(self):
        """繪製分數和 Wave 數"""
        if self.mode:
            arcade.draw_text(
                f"SCORE: {self.mode.score}",
                10, SCREEN_HEIGHT - 20,
                arcade.color.WHITE, 14
            )
            # 繪製 Wave 數 (WaveMode 專用)
            if hasattr(self.mode, 'wave'):
                arcade.draw_text(
                    f"WAVE: {self.mode.wave}",
                    SCREEN_WIDTH - 10, SCREEN_HEIGHT - 20,
                    arcade.color.WHITE, 14, anchor_x="right"
                )


    def _draw_end_screen(self):
        """繪製遊戲結束畫面"""
        if self.end_reason == "GAME_OVER":
            text = "GAME OVER"
            color = arcade.color.RED
        elif self.end_reason == "VICTORY":
            text = "VICTORY!"
            color = arcade.color.GREEN
        else:
            text = "GAME END"
            color = arcade.color.WHITE

        arcade.draw_text(
            text,
            SCREEN_WIDTH / 2,
            SCREEN_HEIGHT / 2 + 20,
            color,
            28,
            anchor_x="center",
        )
        arcade.draw_text(
            "Press R to return to Menu",
            SCREEN_WIDTH / 2,
            SCREEN_HEIGHT / 2 - 20,
            arcade.color.WHITE,
            16,
            anchor_x="center",
        )

        
# 執行遊戲
def main():
    window = PacManGame()
    arcade.run()

if __name__ == "__main__":
    main()