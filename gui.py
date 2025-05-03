import customtkinter as ctk
from CTkColorPicker import *
import requests
import subprocess
from bs4 import BeautifulSoup
import json

class GUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Cheat")
        self.iconbitmap('resources\\main_icon.ico')
        self.resizable(width=False, height=False)
        self.geometry(f'{400}x{400}')

        self.protocol("WM_DELETE_WINDOW", self.on_close)
        ctk.set_appearance_mode("dark")

        self.overlay = None

        self.enemy_color = "#ff0000"
        self.friend_color = "#ff0000"
        self.box_width = 1

        self.esp_state = ctk.BooleanVar(value=False)
        self.only_enemy_state = ctk.BooleanVar(value=False)
        self.health_bar_state = ctk.BooleanVar(value=False)

        self.toplevel_error_window = None

        espSwitch = ctk.CTkSwitch(master=self, text="ESP", command=self.switch_esp,
            variable=self.esp_state, onvalue=True, offvalue=False)
        espSwitch.pack(anchor="nw", padx=10, pady=10)

        onlyEnemy = ctk.CTkSwitch(master=self, text="Only enemy", command=self.restart_esp,
            variable=self.only_enemy_state, onvalue=True, offvalue=False)
        onlyEnemy.pack(anchor="nw", padx=30)

        healthBar = ctk.CTkSwitch(master=self, text="Health bar", command=self.restart_esp,
            variable=self.health_bar_state, onvalue=True, offvalue=False)
        healthBar.pack(anchor="nw", padx=30)

        self.enemyColorLable = ctk.CTkLabel(master=self, text=f"Enemy box color = {self.enemy_color}")
        self.enemyColorLable.pack(anchor="nw", padx=30)
        self.cpb = ctk.CTkButton(self, text="Change enemy color", command=self.change_enemy_color)
        self.cpb.pack(anchor="nw", padx=30)

        self.friendColorLable = ctk.CTkLabel(master=self, text=f"Friend box color = {self.friend_color}")
        self.friendColorLable.pack(anchor="nw", padx=30)
        self.cpb2 = ctk.CTkButton(self, text="Change friend color", command=self.change_friend_color)
        self.cpb2.pack(anchor="nw", padx=30)

        self.BoxWidthLable = ctk.CTkLabel(master=self, text=f"Box width = {self.box_width}")
        self.BoxWidthLable.pack(anchor="nw", padx=30)
        self.ib = ctk.CTkButton(self, text="Change box width", command=self.change_box_width)
        self.ib.pack(anchor="nw", padx=30)
        
        self.update_offsets(url="https://github.com/a2x/cs2-dumper/blob/main/output/client_dll.json", filename="data\\client_dll.json")
        self.update_offsets(url="https://github.com/a2x/cs2-dumper/blob/main/output/offsets.json", filename="data\\offsets.json")

    def switch_esp(self):
        if self.esp_state.get():
            self.start_esp()
        else:
            self.stop_esp()

    def start_esp(self):
        if self.overlay == None:
            self.overlay = subprocess.Popen([
                "python", 
                "overlay.py", 
                self.enemy_color, 
                self.friend_color, 
                str(self.box_width),
                str(int(self.only_enemy_state.get())),
                str(int(self.health_bar_state.get()))
            ])

    def stop_esp(self):
        if self.overlay:
            self.overlay.terminate()
            self.overlay = None

    def restart_esp(self):
        if not self.esp_state.get():
            return
        self.stop_esp()
        self.start_esp()

    def on_close(self):
        self.stop_esp()
        self.destroy()

    def change_enemy_color(self):
        color = AskColor().get()
        if color == None:
            return
        self.enemyColorLable.configure(text=f"Enemy box color = {color}")
        self.enemy_color = color
        self.restart_esp()

    def change_friend_color(self):
        color = AskColor().get()
        if color == None:
            return
        self.friendColorLable.configure(text=f"Friend box color = {color}")
        self.friend_color = color
        self.restart_esp()

    def change_box_width(self):
        dialog = ctk.CTkInputDialog(text="Type in a number in px:", title="Box width")
        number = dialog.get_input()
        if not number.isdigit():
            self.toplevel_error_window = ErrorWindow("Use only numbers!")
        else:
            self.box_width = number
            self.BoxWidthLable.configure(text=f"Box width = {self.box_width}")
            self.restart_esp()

    def update_offsets(self, url, filename):
        try:
            response = requests.get(url)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")

            script_tag = soup.find("script", {
                "type": "application/json",
                "data-target": "react-app.embeddedData"
            })

            json_data = json.loads(script_tag.string)
            raw_lines = json_data["payload"]["blob"]["rawLines"]
            json_string = "\n".join(raw_lines)
            parsed_json = json.loads(json_string)
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(parsed_json, f, ensure_ascii=False, indent=2)
        except requests.exceptions.ConnectionError:
            if self.toplevel_error_window == None or not self.toplevel_error_window.winfo_exists():
                self.toplevel_error_window = ErrorWindow(f"Bad internet connection")
        except requests.exceptions.RequestException as e:
            if self.toplevel_error_window == None or not self.toplevel_error_window.winfo_exists():
                self.toplevel_error_window = ErrorWindow(f"Error when downloading an update : {response.status_code}", width=250)


class ErrorWindow(ctk.CTkToplevel):
    def __init__(self, error_msg, width=200, height=100):
        super().__init__()
        self.geometry(f"{width}x{height}")
        self.title("Error")
        self.attributes('-topmost', True)
        self.iconbitmap('resources\\error_icon.ico')

        self.label = ctk.CTkLabel(self, text=error_msg)
        self.label.pack(pady=20)
        self.button = ctk.CTkButton(self, text="Ok", width=50, command=self.on_close)
        self.button.pack(anchor="e", padx=10)

    def on_close(self):
        self.destroy()


if __name__ == "__main__":
    app = GUI()
    app.mainloop()