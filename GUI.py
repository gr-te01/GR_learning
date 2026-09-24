import engine
import explorer
import download
import tkinter as tk
import scrapling
engine = engine.FetcherEngine(adaptive=True)
explorer = explorer.ResourceSniffer
download = download


root = tk.Tk()