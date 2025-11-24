# menu.py
import arcade

class GameMenu:

    def __init__(self):
        # 選項清單
        self.options = [
            "Classic Mode",
            "Endless Survival Mode",
            "Wave / Roguelike Mode"
        ]
        self.index = 0 # 目前選定的選項索引

        # 標題文字
        self.title = arcade.Text(
            "PAC-MAN ARCADE",
            240, 480, arcade.color.YELLOW,
            38, anchor_x="center"
        )

        # 提示文字
        self.help_text = arcade.Text(
            "↑ ↓ 選擇模式 | ENTER 開始",
            240, 420, arcade.color.LIGHT_GRAY,
            14, anchor_x="center"
        )

    def draw(self):
        """繪製選單畫面"""
        self.title.draw()
        self.help_text.draw()

        base_y = 320
        # 繪製選項
        for i, option in enumerate(self.options):
            selected = (i == self.index)
            color = arcade.color.YELLOW if selected else arcade.color.GRAY
            prefix = "▶ " if selected else "  " # 箭頭標記選定項

            arcade.draw_text(
                prefix + option,
                140, base_y - i * 40,
                color, 22
            )

    def handle_input(self, key):
        """處理鍵盤輸入，回傳選擇的模式名稱 (字串) 或 None"""
        if key == arcade.key.UP:
            # 向上移動
            self.index = (self.index - 1) % len(self.options)
        elif key == arcade.key.DOWN:
            # 向下移動
            self.index = (self.index + 1) % len(self.options)
        elif key == arcade.key.ENTER:
            # 確認選擇，回傳模式名稱字串
            selected_option = self.options[self.index]
            if "Classic" in selected_option:
                return "classic"
            elif "Endless" in selected_option:
                return "endless"
            elif "Wave" in selected_option or "Roguelike" in selected_option:
                return "wave"
        return None # 沒有切換模式時回傳 None