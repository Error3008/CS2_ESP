import tkinter as tk
from cheat import Cheat
import ctypes
import math
import sys

def w2s(mtx, posx, posy, posz, width, height):
    screenW = mtx[12]*posx + mtx[13]*posy + mtx[14]*posz + mtx[15]
    if screenW > 0.001:
        screenX = mtx[0]*posx + mtx[1]*posy + mtx[2]*posz + mtx[3]
        screenY = mtx[4]*posx + mtx[5]*posy + mtx[6]*posz + mtx[7]
        camX = width / 2
        camY = height / 2
        x = camX + (camX * screenX / screenW) // 1
        y = camY - (camY * screenY / screenW) // 1
        return [x, y]
    return [-999, -999]

class Overlay(tk.Tk):
    def __init__(self, enemy_color, friend_color, box_width, only_enemy_visible_state, health_bar_state):
        super().__init__()
        self.enemy_color = enemy_color
        self.only_enemy_state = int(only_enemy_visible_state)
        self.friend_color = friend_color
        self.box_width = int(box_width)
        self.health_bar_state = int(health_bar_state)
        self.transparent_color = "white"
        self.screen_width = self.winfo_screenwidth()
        self.screen_height = self.winfo_screenheight()
        self.all_boxes = {}
        self.health = {}
        self.health_color_high = "#16DF47"
        self.health_color_medium = "#F3B20E"
        self.health_color_low = "#FA1313"
        self.cheat = Cheat()

        self.attributes('-fullscreen', True)
        self.attributes('-topmost', True)
        self.overrideredirect(True) 
        self.config(cursor="none")
        self.wm_attributes('-transparentcolor', self.transparent_color)

        self.canvas = tk.Canvas(self, width=self.screen_width, height=self.screen_height, bg=self.transparent_color, highlightthickness=0)
        self.canvas.pack()

        self.update_idletasks()
        hwnd = ctypes.windll.user32.FindWindowW(None, self.title())
        self.make_window_clickthrough(hwnd)

    def make_window_clickthrough(self, hwnd):
        ctypes.windll.user32.ShowCursor(False)
        extended_style = ctypes.windll.user32.GetWindowLongW(hwnd, -20)
        ctypes.windll.user32.SetWindowLongW(hwnd, -20, extended_style | 0x80000 | 0x20)

    def run(self):
        self.esp()
        self.mainloop()

    def get_health_color(self, h):
        return self.health_color_high if h >= 75 else self.health_color_medium if h > 25 else self.health_color_low

    def esp(self):
        self.cheat.get_info()
        existing_ids = set(self.all_boxes.keys())
        updated_ids = set()
        for pawn in self.cheat.info:
            try:
                if pawn["Id"] == self.cheat.LocalId or pawn["LifeState"] != 0 or pawn["Health"] <= 0:
                    continue

                if self.only_enemy_state and pawn["TeamNum"] == self.cheat.info[self.cheat.LocalPosInArr]["TeamNum"]:
                    continue

                updated_ids.add(pawn["Id"])

                color = self.friend_color if pawn["TeamNum"] == self.cheat.info[self.cheat.LocalPosInArr]["TeamNum"] else self.enemy_color

                local_pos = self.cheat.info[self.cheat.LocalPosInArr]["Pos"]
                pawn_pos = pawn["Pos"]
                distance = math.sqrt((local_pos[0] - pawn_pos[0]) ** 2 + (local_pos[1] - pawn_pos[1]) ** 2 + (local_pos[2] - pawn_pos[2]) ** 2)
                if distance == 0:
                    continue
                box_width = (80 * 100) / distance

                # print(pawn["Id"], pawn)
                head_pos = w2s(self.cheat.get_ViewMatrix(), pawn["HeadPos"][0], pawn["HeadPos"][1], pawn["HeadPos"][2], self.screen_width, self.screen_height)
                leg_pos = w2s(self.cheat.get_ViewMatrix(), pawn["HeadPos"][0], pawn["HeadPos"][1], pawn["LegZ"], self.screen_width, self.screen_height)
                box_height = leg_pos[1] - head_pos[1]
                center_x = (head_pos[0] + leg_pos[0]) / 2

                if pawn["Id"] not in self.all_boxes:
                    box = self.canvas.create_rectangle(
                        center_x - box_width, head_pos[1],  center_x + box_width,  leg_pos[1],
                        fill=self.transparent_color, 
                        outline=color, 
                        width=self.box_width
                    )
                    self.all_boxes[pawn["Id"]] = box
                    if self.health_bar_state:
                        health_line = self.canvas.create_line(
                            0, 0, 0, 0,
                            fill=self.health_color_high,
                            width=3
                        )
                        self.health[pawn["Id"]] = health_line
                else:
                    self.canvas.coords(
                        self.all_boxes[pawn["Id"]], 
                        center_x - box_width, 
                        head_pos[1], 
                        center_x + box_width, 
                        leg_pos[1]
                    )
                    if self.health_bar_state:
                        health_line_height = (box_height * pawn["Health"]) / 100
                        health_line_color = self.get_health_color(pawn["Health"])
                        self.canvas.coords(
                            self.health[pawn["Id"]],
                            center_x - box_width - 5,
                            leg_pos[1] - health_line_height,
                            center_x - box_width - 5,
                            leg_pos[1]
                        )
                        self.canvas.itemconfig(
                            self.health[pawn["Id"]],
                            fill=health_line_color
                        )
            except Exception:
                updated_ids.remove(pawn["Id"])
                continue
        for old_id in existing_ids - updated_ids:
            self.canvas.delete(self.all_boxes[old_id])
            del self.all_boxes[old_id]
            if self.health_bar_state:
                self.canvas.delete(self.health[old_id])
                del self.health[old_id]
        self.after(10, self.esp)

if __name__ == "__main__":
    # app = Overlay("#ff0000", "#ff0000", "1", "0", "0")
    app = Overlay(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5])
    app.run()