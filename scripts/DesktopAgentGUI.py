#!/usr/bin/env python3
"""Desktop Agent control panel with clickable action buttons."""

from __future__ import annotations

import argparse
import queue
import subprocess
import threading
from pathlib import Path
import tkinter as tk
from tkinter import messagebox, simpledialog, ttk


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
TOOLS_SCRIPT = SCRIPT_DIR / "DesktopAgentTools.ps1"
TODO_PATH = REPO_ROOT / "todo.md"
MEMORY_ROOT = Path(r"D:\scanner\velocity_memory")


def build_tool_command(
    action: str,
    text: str | None = None,
    task_id: int | None = None,
    full_backup: bool = False,
) -> list[str]:
    cmd = [
        "powershell",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(TOOLS_SCRIPT),
        "-Action",
        action,
        "-TodoPath",
        str(TODO_PATH),
        "-MemoryRoot",
        str(MEMORY_ROOT),
    ]
    if text:
        cmd.extend(["-Text", text])
    if task_id is not None:
        cmd.extend(["-Id", str(task_id)])
    if full_backup:
        cmd.append("-FullBackup")
    return cmd


class DesktopAgentGUI:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Desktop Agent Control Panel")
        self.root.geometry("980x700")
        self.root.minsize(840, 560)

        self._queue: queue.Queue[tuple[str, str | int]] = queue.Queue()
        self._worker: threading.Thread | None = None
        self._is_busy = False
        self._buttons: list[ttk.Button] = []

        self.status_var = tk.StringVar(value="Ready.")
        self._build_ui()
        self.root.after(120, self._poll_queue)

    def _build_ui(self) -> None:
        outer = ttk.Frame(self.root, padding=10)
        outer.pack(fill="both", expand=True)

        title = ttk.Label(outer, text="Desktop Agent Actions", font=("Segoe UI", 14, "bold"))
        title.pack(anchor="w", pady=(0, 8))

        btn_frame = ttk.Frame(outer)
        btn_frame.pack(fill="x", pady=(0, 8))

        self._add_button(btn_frame, "Daily Brief", self._run_brief, 0, 0)
        self._add_button(btn_frame, "Morning News Digest", self._run_morning_news, 0, 1)
        self._add_button(btn_frame, "Open Finviz News", self._open_finviz_news, 1, 0)
        self._add_button(btn_frame, "Todo List", self._run_todo_list, 1, 1)
        self._add_button(btn_frame, "Add Todo", self._add_todo, 2, 0)
        self._add_button(btn_frame, "Mark Todo Done", self._mark_todo_done, 2, 1)
        self._add_button(btn_frame, "Remove Todo", self._remove_todo, 3, 0)
        self._add_button(btn_frame, "Latest Report Path", self._latest_report, 3, 1)
        self._add_button(btn_frame, "Daily Wrap + Backup", self._daily_wrap, 4, 0)
        self._add_button(btn_frame, "Full Backup Wrap", self._full_backup_wrap, 4, 1)
        self._add_button(btn_frame, "Open Workspace Pack", self._open_workspace, 5, 0)
        self._add_button(btn_frame, "Clear Output", self._clear_output, 5, 1)

        for col in (0, 1):
            btn_frame.grid_columnconfigure(col, weight=1)

        status = ttk.Label(outer, textvariable=self.status_var, font=("Segoe UI", 9))
        status.pack(anchor="w", pady=(4, 6))

        out_frame = ttk.Frame(outer)
        out_frame.pack(fill="both", expand=True)

        self.output = tk.Text(
            out_frame,
            wrap="word",
            height=20,
            font=("Consolas", 10),
            state="normal",
            padx=8,
            pady=8,
        )
        self.output.pack(side="left", fill="both", expand=True)

        scroll = ttk.Scrollbar(out_frame, orient="vertical", command=self.output.yview)
        scroll.pack(side="right", fill="y")
        self.output.configure(yscrollcommand=scroll.set)

        self._append_output("Desktop Agent GUI ready.")
        self._append_output("Tip: use buttons one at a time; output appears here.")

    def _add_button(self, parent: ttk.Frame, text: str, callback, row: int, col: int) -> None:
        btn = ttk.Button(parent, text=text, command=callback)
        btn.grid(row=row, column=col, padx=4, pady=4, sticky="ew")
        self._buttons.append(btn)

    def _set_busy(self, busy: bool, message: str | None = None) -> None:
        self._is_busy = busy
        for b in self._buttons:
            b.configure(state="disabled" if busy else "normal")
        if message:
            self.status_var.set(message)
        else:
            self.status_var.set("Working..." if busy else "Ready.")

    def _append_output(self, line: str) -> None:
        self.output.insert("end", f"{line}\n")
        self.output.see("end")

    def _clear_output(self) -> None:
        self.output.delete("1.0", "end")
        self._append_output("Output cleared.")

    def _run_tool_action(
        self,
        action: str,
        text: str | None = None,
        task_id: int | None = None,
        full_backup: bool = False,
    ) -> None:
        if self._is_busy:
            messagebox.showinfo("Busy", "A command is already running. Please wait.")
            return

        if not TOOLS_SCRIPT.exists():
            messagebox.showerror("Missing Script", f"Could not find: {TOOLS_SCRIPT}")
            return

        cmd = build_tool_command(
            action=action,
            text=text,
            task_id=task_id,
            full_backup=full_backup,
        )
        self._append_output("")
        self._append_output(f"$ {' '.join(cmd)}")
        self._set_busy(True, f"Running action: {action}")

        def worker() -> None:
            try:
                proc = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                )
                assert proc.stdout is not None
                for line in proc.stdout:
                    self._queue.put(("line", line.rstrip("\n")))
                ret = proc.wait()
                self._queue.put(("done", ret))
            except Exception as exc:  # pragma: no cover - runtime safety
                self._queue.put(("line", f"[ERROR] {exc}"))
                self._queue.put(("done", 1))

        self._worker = threading.Thread(target=worker, daemon=True)
        self._worker.start()

    def _poll_queue(self) -> None:
        try:
            while True:
                kind, payload = self._queue.get_nowait()
                if kind == "line":
                    self._append_output(str(payload))
                elif kind == "done":
                    code = int(payload)
                    if code == 0:
                        self._append_output("[OK] Command completed.")
                        self._set_busy(False, "Ready.")
                    else:
                        self._append_output(f"[FAIL] Exit code: {code}")
                        self._set_busy(False, "Command failed. Ready.")
        except queue.Empty:
            pass
        finally:
            self.root.after(120, self._poll_queue)

    def _run_brief(self) -> None:
        self._run_tool_action("brief")

    def _run_morning_news(self) -> None:
        self._run_tool_action("morning-news")

    def _open_finviz_news(self) -> None:
        self._run_tool_action("open-finviz-news")

    def _run_todo_list(self) -> None:
        self._run_tool_action("todo-list")

    def _latest_report(self) -> None:
        self._run_tool_action("latest-report")

    def _open_workspace(self) -> None:
        self._run_tool_action("open-workspace")

    def _add_todo(self) -> None:
        item = simpledialog.askstring("Add Todo", "Enter todo item:", parent=self.root)
        if item is None:
            return
        item = item.strip()
        if not item:
            messagebox.showinfo("Add Todo", "Todo item was empty.")
            return
        self._run_tool_action("todo-add", text=item)

    def _mark_todo_done(self) -> None:
        raw = simpledialog.askstring("Mark Todo Done", "Enter open task number:", parent=self.root)
        if raw is None:
            return
        raw = raw.strip()
        if not raw.isdigit():
            messagebox.showinfo("Mark Todo Done", "Please enter a valid number.")
            return
        self._run_tool_action("todo-done", task_id=int(raw))

    def _remove_todo(self) -> None:
        raw = simpledialog.askstring("Remove Todo", "Enter open task number to remove:", parent=self.root)
        if raw is None:
            return
        raw = raw.strip()
        if not raw.isdigit():
            messagebox.showinfo("Remove Todo", "Please enter a valid number.")
            return
        self._run_tool_action("todo-remove", task_id=int(raw))

    def _daily_wrap(self) -> None:
        note = simpledialog.askstring("Daily Wrap", "Optional wrap note (blank = default):", parent=self.root)
        if note is None:
            return
        note = note.strip()
        self._run_tool_action("daily-wrap", text=note if note else None)

    def _full_backup_wrap(self) -> None:
        note = simpledialog.askstring("Full Backup Wrap", "Optional wrap note (blank = default):", parent=self.root)
        if note is None:
            return
        note = note.strip()
        self._run_tool_action("daily-wrap", text=note if note else None, full_backup=True)


def run_check() -> int:
    missing: list[str] = []
    if not TOOLS_SCRIPT.exists():
        missing.append(str(TOOLS_SCRIPT))
    if missing:
        print("Missing required files:")
        for m in missing:
            print(f"- {m}")
        return 1
    print("DesktopAgentGUI check: OK")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Desktop Agent GUI launcher.")
    parser.add_argument("--check", action="store_true", help="Validate required files and exit.")
    args = parser.parse_args()

    if args.check:
        return run_check()

    root = tk.Tk()
    DesktopAgentGUI(root)
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
