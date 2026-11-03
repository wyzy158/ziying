#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TVBox 接口自动生成工具 - Windows GUI 版
双击运行，选择资源类型，一键生成可导入 TVBox 的 JSON 配置
"""

import json
import os
import sys
import time
import threading
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests

# Windows 下用 %APPDATA% 或程序目录，避免权限问题
if getattr(sys, "frozen", False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

OUTPUT_DIR = os.path.join(BASE_DIR, "tvbox_output")
LOG_DIR = os.path.join(BASE_DIR, "logs")
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

UPDATE_INTERVAL_SECONDS = 6 * 3600
MAX_WORKERS = 12
REQUEST_TIMEOUT = (6, 12)
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

# 预置源清单（示例骨架，生产请替换为自行验证的源）
KNOWN_SOURCES: dict[str, list[dict]] = {
    "movie": [
        {"name": "肥猫", "url": "http://肥猫.net/tv", "type": "mix"},
        {"name": "王二小", "url": "https://d.kstore.dev/download/9280/wex.json", "type": "mix"},
        {"name": "老刘备", "url": "https://raw.liucn.cc/box/m.json", "type": "mix"},
        {"name": "小马", "url": "https://szyyds.cn/tv/x.json", "type": "mix"},
        {"name": "4K小盒子", "url": "http://xhztv.top/4k.json", "type": "movie"},
    ],
    "tv": [
        {"name": "肥猫", "url": "http://肥猫.net/tv", "type": "mix"},
        {"name": "王二小", "url": "https://d.kstore.dev/download/9280/wex.json", "type": "mix"},
        {"name": "讴歌", "url": "http://ztha.top/TVBox/GYCK.json", "type": "mix"},
        {"name": "老刘备", "url": "https://raw.liucn.cc/box/m.json", "type": "mix"},
    ],
    "live": [
        {"name": "IPTV-API", "url": "https://raw.githubusercontent.com/Guovin/iptv-api/gd/output/result.m3u", "type": "live_m3u"},
        {"name": "TVBox直播聚合", "url": "https://agit.ai/Yoursmile7/TVBox/raw/branch/master/live.txt", "type": "live_txt"},
    ],
    "mix": [
        {"name": "肥猫", "url": "http://肥猫.net/tv", "type": "mix"},
        {"name": "王二小", "url": "https://d.kstore.dev/download/9280/wex.json", "type": "mix"},
        {"name": "老刘备", "url": "https://raw.liucn.cc/box/m.json", "type": "mix"},
        {"name": "小马", "url": "https://szyyds.cn/tv/x.json", "type": "mix"},
        {"name": "真心", "url": "https://tvbox.catvod.com/FongMi.json", "type": "mix"},
    ],
}


@dataclass
class HealthResult:
    url: str
    name: str
    category: str
    ok: bool = False
    status_code: Optional[int] = None
    latency_ms: float = 0.0
    error: str = ""
    sites_count: int = 0
    lives_count: int = 0
    payload: Optional[dict] = field(default=None, repr=False)


class TVBoxEngine:
    """核心引擎：健康检查 + 配置生成 + 定时调度"""

    def __init__(self, log_func=None):
        self.output_dir = OUTPUT_DIR
        self.checker = HealthChecker()
        self.generator = ConfigGenerator(self.output_dir)
        self._stop_event = threading.Event()
        self.log_func = log_func or (lambda msg: None)
        self._scheduler_thread = None
        self.logger = logging.getLogger("TVBoxEngine")
        self._setup_logging()

    def _setup_logging(self):
        if self.logger.handlers:
            return
        self.logger.setLevel(logging.INFO)
        fh = logging.FileHandler(
            os.path.join(LOG_DIR, "tvbox_gen.log"), encoding="utf-8"
        )
        fh.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
        self.logger.addHandler(fh)

    def generate(self, category: str) -> dict:
        category = category.lower().strip()
        if category not in KNOWN_SOURCES:
            raise ValueError(f"不支持的类型: {category}")

        entries = KNOWN_SOURCES[category]
        self._log(f"开始生成 [{category}]，候选源 {len(entries)} 个")

        results = self.checker.check_many(entries, log_func=self._log)
        ok_results = [r for r in results if r.ok]
        self._log(f"健康检查：{len(ok_results)}/{len(results)} 通过")

        single = self.generator.build_single(ok_results, category)
        multi = self.generator.build_multi({category: single})
        paths = self.generator.write(category, single, multi)
        self._write_health_report(category, results)
        self._write_meta(category, len(single["sites"]), len(single["lives"]))

        self._log(
            f"生成完成：sites={len(single['sites'])}, lives={len(single['lives'])}"
        )
        return {
            "paths": paths,
            "sites": len(single["sites"]),
            "lives": len(single["lives"]),
        }

    def generate_all(self, categories: Optional[list[str]] = None) -> dict:
        categories = categories or ["movie", "tv", "live", "mix"]
        all_singles = {}
        for cat in categories:
            try:
                r = self.generate(cat)
                with open(r["paths"]["single"], encoding="utf-8") as f:
                    all_singles[cat] = json.load(f)
            except Exception as e:
                self._log(f"生成 [{cat}] 失败: {e}")
        multi = self.generator.build_multi(all_singles)
        multi_path = os.path.join(self.output_dir, "multi.json")
        with open(multi_path, "w", encoding="utf-8") as f:
            json.dump(multi, f, ensure_ascii=False, indent=2)
        self._log("全类型多仓已更新")
        return all_singles

    def start_scheduler(self, interval: int = UPDATE_INTERVAL_SECONDS):
        if self._scheduler_thread and self._scheduler_thread.is_alive():
            return
        self._stop_event.clear()

        def loop():
            while not self._stop_event.is_set():
                try:
                    self.generate_all()
                except Exception as e:
                    self._log(f"定时更新异常: {e}")
                self._stop_event.wait(interval)

        self._scheduler_thread = threading.Thread(
            target=loop, daemon=True, name="tvbox-updater"
        )
        self._scheduler_thread.start()
        self._log(f"定时更新已启动，间隔 {interval} 秒")

    def stop_scheduler(self):
        self._stop_event.set()
        self._log("定时更新已停止")

    def _log(self, msg: str):
        self.logger.info(msg)
        self.log_func(msg)

    def _write_health_report(self, category: str, results: list[HealthResult]):
        report = []
        for r in results:
            d = asdict(r)
            d.pop("payload", None)
            d["timestamp"] = datetime.now(timezone.utc).isoformat()
            report.append(d)
        path = os.path.join(self.output_dir, f"health_{category}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

    def _write_meta(self, category: str, sites: int, lives: int):
        path = os.path.join(self.output_dir, "status.json")
        existing = {}
        if os.path.exists(path):
            try:
                with open(path, encoding="utf-8") as f:
                    existing = json.load(f)
            except Exception:
                pass
        existing[category] = {
            "category": category,
            "sites": sites,
            "lives": lives,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(existing, f, ensure_ascii=False, indent=2)


class HealthChecker:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT})

    def check(self, entry: dict, log_func=None) -> HealthResult:
        result = HealthResult(
            url=entry["url"], name=entry["name"], category=entry.get("type", "mix")
        )
        start = time.monotonic()
        try:
            resp = self.session.get(
                entry["url"], timeout=REQUEST_TIMEOUT, allow_redirects=True
            )
            result.latency_ms = (time.monotonic() - start) * 1000
            result.status_code = resp.status_code
            if resp.status_code != 200:
                result.error = f"HTTP {resp.status_code}"
                return result
            text = resp.text.strip()

            if entry.get("type") == "live_m3u":
                if "#EXTM3U" not in text:
                    result.error = "不是有效的 M3U"
                    return result
                result.lives_count = 1
                result.ok = True
                return result
            if entry.get("type") == "live_txt":
                if len(text.splitlines()) < 3:
                    result.error = "TXT 内容过少"
                    return result
                result.lives_count = 1
                result.ok = True
                return result

            data = json.loads(text)
            sites = data.get("sites") or []
            lives = data.get("lives") or []
            result.sites_count = len(sites) if isinstance(sites, list) else 0
            result.lives_count = len(lives) if isinstance(lives, list) else 0
            if result.sites_count == 0 and result.lives_count == 0:
                result.error = "sites 和 lives 均为空"
                return result
            result.payload = data
            result.ok = True
        except requests.Timeout:
            result.error = "超时"
        except json.JSONDecodeError as e:
            result.error = f"JSON 解析失败: {e.msg}"
        except Exception as e:
            result.error = f"{type(e).__name__}: {str(e)[:80]}"
        finally:
            if not result.latency_ms:
                result.latency_ms = (time.monotonic() - start) * 1000
        return result

    def check_many(self, entries: list[dict], log_func=None) -> list[HealthResult]:
        results: list[HealthResult] = []
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
            futures = {pool.submit(self.check, e): e for e in entries}
            for fut in as_completed(futures):
                try:
                    results.append(fut.result())
                except Exception as e:
                    entry = futures[fut]
                    results.append(
                        HealthResult(
                            url=entry["url"],
                            name=entry["name"],
                            category=entry.get("type", "mix"),
                            error=f"检查异常: {e}",
                        )
                    )
        results.sort(key=lambda r: (not r.ok, r.latency_ms))
        return results


class ConfigGenerator:
    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    @staticmethod
    def _dedupe_by_key(items: list[dict], key_field: str = "key") -> list[dict]:
        seen, out = set(), []
        for item in items:
            if not isinstance(item, dict):
                continue
            k = item.get(key_field) or item.get("name") or item.get("api") or ""
            if not k or k in seen:
                continue
            seen.add(k)
            out.append(item)
        return out

    def build_single(self, results: list[HealthResult], category: str) -> dict:
        all_sites, all_lives = [], []
        for r in results:
            if not r.ok or not r.payload:
                continue
            sites = r.payload.get("sites")
            if isinstance(sites, list):
                all_sites.extend(sites)
            lives = r.payload.get("lives")
            if isinstance(lives, list):
                all_lives.extend(lives)

        config = {
            "spider": "",
            "sites": self._dedupe_by_key(all_sites),
            "lives": self._dedupe_by_key(all_lives, key_field="name"),
            "parses": [],
            "flags": ["电影", "电视剧", "综艺", "动漫", "直播"],
            "ijk": [
                {
                    "group": "软解码",
                    "options": [{"category": 4, "name": "opensles", "value": "0"}],
                }
            ],
        }
        if category == "live" and not config["lives"]:
            raise RuntimeError("直播类型未获得有效 lives")
        if category != "live" and not config["sites"]:
            raise RuntimeError("未获得有效 sites，请检查网络或源清单")
        return config

    def build_multi(self, single_configs: dict[str, dict]) -> list[dict]:
        return [
            {"name": f"AutoGen-{cat}", "url": f"./{cat}.json"}
            for cat in single_configs
        ]

    def write(self, category: str, single: dict, multi: list[dict]) -> dict[str, str]:
        paths = {}
        single_path = os.path.join(self.output_dir, f"{category}.json")
        with open(single_path, "w", encoding="utf-8") as f:
            json.dump(single, f, ensure_ascii=False, indent=2)
        paths["single"] = single_path
        multi_path = os.path.join(self.output_dir, "multi.json")
        with open(multi_path, "w", encoding="utf-8") as f:
            json.dump(multi, f, ensure_ascii=False, indent=2)
        paths["multi"] = multi_path
        return paths


# ============================================================
# GUI
# ============================================================
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext


class TVBoxGUI:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("TVBox 接口自动生成工具 v1.0")
        self.root.geometry("820x640")
        self.root.minsize(720, 560)

        self.engine = TVBoxEngine(log_func=self.append_log)
        self._build_ui()

    def _build_ui(self):
        # 顶部：资源类型选择
        frame_top = ttk.LabelFrame(self.root, text="1. 选择资源类型")
        frame_top.pack(fill="x", padx=10, pady=8)

        self.var_category = tk.StringVar(value="mix")
        options = [
            ("综合（mix）", "mix"),
            ("电影（movie）", "movie"),
            ("电视剧（tv）", "tv"),
            ("直播（live）", "live"),
            ("全部类型", "all"),
        ]
        for i, (label, val) in enumerate(options):
            ttk.Radiobutton(
                frame_top, text=label, value=val, variable=self.var_category
            ).grid(row=0, column=i, padx=10, pady=8, sticky="w")

        # 按钮区
        frame_btn = ttk.Frame(self.root)
        frame_btn.pack(fill="x", padx=10, pady=4)

        self.btn_generate = ttk.Button(
            frame_btn, text="▶ 生成配置", command=self.on_generate
        )
        self.btn_generate.pack(side="left", padx=4)

        self.btn_auto = ttk.Button(
            frame_btn, text="⏱ 启动定时更新", command=self.on_toggle_auto
        )
        self.btn_auto.pack(side="left", padx=4)

        self.btn_open = ttk.Button(
            frame_btn, text="📂 打开输出目录", command=self.on_open_output
        )
        self.btn_open.pack(side="left", padx=4)

        self.btn_clear = ttk.Button(
            frame_btn, text="🧹 清空日志", command=lambda: self.txt_log.delete("1.0", tk.END)
        )
        self.btn_clear.pack(side="left", padx=4)

        # 进度条
        self.progress = ttk.Progressbar(self.root, mode="indeterminate")
        self.progress.pack(fill="x", padx=10, pady=4)

        # 日志区
        frame_log = ttk.LabelFrame(self.root, text="2. 运行日志")
        frame_log.pack(fill="both", expand=True, padx=10, pady=8)

        self.txt_log = scrolledtext.ScrolledText(
            frame_log, wrap="word", height=20, state="normal"
        )
        self.txt_log.pack(fill="both", expand=True, padx=4, pady=4)

        # 底部状态栏
        self.status_var = tk.StringVar(value="就绪")
        status_bar = ttk.Label(
            self.root, textvariable=self.status_var, anchor="w", relief="sunken"
        )
        status_bar.pack(fill="x", side="bottom")

        self._auto_running = False

    # ---------- 事件 ----------
    def append_log(self, msg: str):
        ts = datetime.now().strftime("%H:%M:%S")
        self.txt_log.insert(tk.END, f"[{ts}] {msg}\n")
        self.txt_log.see(tk.END)

    def _set_busy(self, busy: bool, text: str = ""):
        if busy:
            self.progress.start(10)
            self.btn_generate.config(state="disabled")
            self.status_var.set(text or "处理中…")
        else:
            self.progress.stop()
            self.btn_generate.config(state="normal")
            self.status_var.set(text or "就绪")

    def on_generate(self):
        category = self.var_category.get()

        def worker():
            self._set_busy(True, f"正在生成 {category} …")
            try:
                if category == "all":
                    self.engine.generate_all()
                    self.append_log("✅ 全部类型生成完成")
                else:
                    r = self.engine.generate(category)
                    self.append_log(
                        f"✅ 生成完成：{r['paths']['single']} "
                        f"(sites={r['sites']}, lives={r['lives']})"
                    )
                self.status_var.set("生成完成")
            except Exception as e:
                self.append_log(f"❌ 失败：{e}")
                messagebox.showerror("生成失败", str(e))
                self.status_var.set("生成失败")
            finally:
                self._set_busy(False)

        threading.Thread(target=worker, daemon=True).start()

    def on_toggle_auto(self):
        if not self._auto_running:
            self.engine.start_scheduler()
            self._auto_running = True
            self.btn_auto.config(text="⏸ 停止定时更新")
            self.status_var.set("定时更新运行中")
        else:
            self.engine.stop_scheduler()
            self._auto_running = False
            self.btn_auto.config(text="⏱ 启动定时更新")
            self.status_var.set("定时更新已停止")

    def on_open_output(self):
        if os.name == "nt":
            os.startfile(OUTPUT_DIR)
        else:
            import subprocess

            subprocess.Popen(["xdg-open", OUTPUT_DIR])


def main():
    root = tk.Tk()
    # 高 DPI 适配（Windows）
    try:
        from ctypes import windll

        windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass
    app = TVBoxGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
