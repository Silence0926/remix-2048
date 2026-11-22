"""Legacy compatibility launcher for 2048 Remix."""

import tkinter as tk

from game_main_controller import Game2048


def main():
    root = tk.Tk()
    Game2048(root, size=4)
    root.mainloop()


if __name__ == "__main__":
    main()
