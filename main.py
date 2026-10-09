"""Entry point for Signal Lab."""

import tkinter as tk
from gui import SignalApp


def main():
    root = tk.Tk()
    SignalApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
