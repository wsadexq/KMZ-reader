"""Open a DJI KMZ route in a local browser preview."""

from __future__ import annotations

import argparse
import sys
import time
import webbrowser

from kmz_parser import KmzParseError, parse_kmz_document
from local_server import start_server


def _select_file() -> str | None:
    try:
        import tkinter as tk
        from tkinter import filedialog

        root = tk.Tk()
        root.withdraw()
        selected = filedialog.askopenfilename(title="选择 KMZ 航线文件", filetypes=[("KMZ 航线", "*.kmz"), ("所有文件", "*.*")])
        root.destroy()
        return selected or None
    except Exception:
        return None


def _show_error(message: str) -> None:
    try:
        import tkinter as tk
        from tkinter import messagebox

        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("KMZ Preview", message)
        root.destroy()
    except Exception:
        print(message, file=sys.stderr)


def main() -> int:
    parser = argparse.ArgumentParser(description="在浏览器中预览 DJI KMZ 航线")
    parser.add_argument("path", nargs="?", help="KMZ 文件路径")
    args = parser.parse_args()
    path = args.path or _select_file()
    if not path:
        return 0
    try:
        document = parse_kmz_document(path)
        server, thread, url = start_server(document.route, document)
    except KmzParseError as exc:
        _show_error(str(exc))
        return 2
    except Exception as exc:  # keep the right-click experience understandable
        _show_error(f"启动预览失败: {exc}")
        return 3
    if not webbrowser.open(url):
        _show_error(f"浏览器启动失败，请手动打开：\n{url}")
    try:
        while thread.is_alive():
            time.sleep(0.5)
    except KeyboardInterrupt:
        server.shutdown()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
