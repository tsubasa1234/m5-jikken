"""VSCode -> Blender コード実行サーバー (Blender アドオン)

localhost の TCP ポートで待機し、VSCode 側クライアント (send_to_blender.py) から
送られてきた Python コードを Blender のメインスレッドで実行して結果を返す。

通信プロトコル (1 リクエスト = 1 接続):
    [4 byte big-endian 長さ][UTF-8 JSON]  を送り合う
    リクエスト: {"code": str, "filepath": str, "sys_paths": [str, ...]}
    レスポンス: {"ok": bool, "output": str, "error": {...} | None}
"""

bl_info = {
    "name": "VSCode Code Runner Server",
    "author": "Tsubasa Ishida",
    "version": (1, 0, 0),
    "blender": (4, 2, 0),
    "location": "3D Viewport > Sidebar (N) > VSCode",
    "description": "VSCode から TCP で受信した Python コードを即座に実行する",
    "category": "Development",
}

import io
import json
import os
import queue
import socket
import struct
import sys
import threading
import traceback
from contextlib import redirect_stderr, redirect_stdout

import bpy

HOST = "127.0.0.1"  # 外部から接続されないようローカルホストのみで待機
DEFAULT_PORT = 52525  # 動的/プライベートポート範囲 (49152-65535) から選択
EXEC_TIMEOUT = 600.0  # メインスレッドでの実行完了を待つ最大秒数
MAX_MESSAGE_SIZE = 64 * 1024 * 1024

_server = None  # 実行中の _CodeServer インスタンス


# ---------------------------------------------------------------------------
# 送受信ヘルパー
# ---------------------------------------------------------------------------
def _recv_exact(conn, size):
    buf = bytearray()
    while len(buf) < size:
        chunk = conn.recv(size - len(buf))
        if not chunk:
            raise ConnectionError("接続が途中で切断されました")
        buf.extend(chunk)
    return bytes(buf)


def _recv_message(conn):
    (length,) = struct.unpack(">I", _recv_exact(conn, 4))
    if length > MAX_MESSAGE_SIZE:
        raise ValueError(f"メッセージが大きすぎます: {length} bytes")
    return json.loads(_recv_exact(conn, length).decode("utf-8"))


def _send_message(conn, obj):
    data = json.dumps(obj, ensure_ascii=False).encode("utf-8")
    conn.sendall(struct.pack(">I", len(data)) + data)


# ---------------------------------------------------------------------------
# コード実行 (必ずメインスレッドで呼ぶ)
# ---------------------------------------------------------------------------
class _Tee(io.TextIOBase):
    """出力をバッファに溜めつつ、Blender のコンソールにも流す"""

    def __init__(self, original):
        self._original = original
        self._buffer = io.StringIO()

    def write(self, s):
        self._buffer.write(s)
        try:
            self._original.write(s)
        except Exception:
            pass
        return len(s)

    def flush(self):
        try:
            self._original.flush()
        except Exception:
            pass

    def getvalue(self):
        return self._buffer.getvalue()


def _purge_project_modules(paths):
    """プロジェクト配下からインポートされたモジュールを sys.modules から外す。

    こうしておくと、import 先のモジュールを編集した場合も次回実行時に
    再読み込みされる (Blender を再起動しなくてよい)。
    """
    roots = [os.path.normcase(os.path.abspath(p)) + os.sep for p in paths]
    for name, module in list(sys.modules.items()):
        module_file = getattr(module, "__file__", None)
        if not module_file:
            continue
        module_file = os.path.normcase(os.path.abspath(module_file))
        if any(module_file.startswith(root) for root in roots):
            del sys.modules[name]


def _execute(request):
    code = request.get("code", "")
    filepath = request.get("filepath") or "<vscode>"
    sys_paths = [p for p in request.get("sys_paths", []) if p and os.path.isdir(p)]

    # sys.path の先頭にスクリプトのディレクトリ / プロジェクトルートを追加
    added = []
    for p in reversed(sys_paths):
        if p not in sys.path:
            sys.path.insert(0, p)
            added.append(p)
    _purge_project_modules(sys_paths)

    script_globals = {
        "__name__": "__main__",
        "__file__": filepath,
        "__builtins__": __builtins__,
        "bpy": bpy,
    }
    out = _Tee(sys.stdout)
    err = _Tee(sys.stderr)
    error = None
    try:
        with redirect_stdout(out), redirect_stderr(err):
            exec(compile(code, filepath, "exec"), script_globals)
    except SystemExit:
        pass  # スクリプト内の sys.exit() で Blender ごと終了しないようにする
    except BaseException as exc:  # noqa: BLE001 - 何が起きても結果は返す
        tb = traceback.TracebackException.from_exception(exc)
        # このアドオン自身の exec 呼び出しフレームはユーザーに不要なので除く
        tb.stack = traceback.StackSummary.from_list(
            [f for f in tb.stack if f.filename != __file__])
        frames = [{"file": f.filename, "line": f.lineno} for f in tb.stack]
        if isinstance(exc, SyntaxError):
            frames.append({"file": exc.filename or filepath, "line": exc.lineno or 1})
        error = {
            "type": type(exc).__name__,
            "message": str(exc),
            "frames": frames,
            "traceback": "".join(tb.format()),
        }
        print(error["traceback"], file=sys.stderr)
    finally:
        for p in added:
            if p in sys.path:
                sys.path.remove(p)

    return {"ok": error is None, "output": out.getvalue() + err.getvalue(), "error": error}


# ---------------------------------------------------------------------------
# TCP サーバー
#   bpy はスレッドセーフではないので、ソケットは別スレッドで受け付け、
#   実際の実行は bpy.app.timers 経由でメインスレッドに回す。
# ---------------------------------------------------------------------------
class _Job:
    def __init__(self, request):
        self.request = request
        self.result = None
        self.done = threading.Event()


class _CodeServer:
    def __init__(self, port):
        self.port = port
        self._jobs = queue.Queue()
        self._stop = threading.Event()
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._sock.bind((HOST, port))
        self._sock.listen(5)
        self._sock.settimeout(0.5)
        self._thread = threading.Thread(target=self._accept_loop, daemon=True)
        # bpy.app.timers は関数オブジェクトの同一性で管理するので、束縛メソッドを1つに固定
        self._timer_fn = self._process_jobs

    def start(self):
        self._thread.start()
        bpy.app.timers.register(self._timer_fn, persistent=True)
        print(f"[VSCode Server] {HOST}:{self.port} で待機中")

    def stop(self):
        self._stop.set()
        self._thread.join(timeout=2.0)
        self._sock.close()
        if bpy.app.timers.is_registered(self._timer_fn):
            bpy.app.timers.unregister(self._timer_fn)
        # 待たせているリクエストがあればエラーで返す
        while not self._jobs.empty():
            job = self._jobs.get_nowait()
            job.result = {"ok": False, "output": "", "error": {
                "type": "ServerStopped", "message": "サーバーが停止しました",
                "frames": [], "traceback": ""}}
            job.done.set()
        print("[VSCode Server] 停止しました")

    def _accept_loop(self):
        while not self._stop.is_set():
            try:
                conn, _ = self._sock.accept()
            except socket.timeout:
                continue
            except OSError:
                break
            threading.Thread(target=self._handle, args=(conn,), daemon=True).start()

    def _handle(self, conn):
        with conn:
            try:
                conn.settimeout(10.0)
                request = _recv_message(conn)
                if request.get("command") == "ping":
                    _send_message(conn, {"ok": True, "output": "pong", "error": None})
                    return
                job = _Job(request)
                self._jobs.put(job)
                if not job.done.wait(EXEC_TIMEOUT):
                    raise TimeoutError("Blender 側の実行がタイムアウトしました")
                conn.settimeout(None)
                _send_message(conn, job.result)
            except Exception as exc:  # noqa: BLE001
                try:
                    _send_message(conn, {"ok": False, "output": "", "error": {
                        "type": type(exc).__name__, "message": str(exc),
                        "frames": [], "traceback": ""}})
                except Exception:
                    pass

    def _process_jobs(self):
        """bpy.app.timers から定期的に呼ばれる (メインスレッド)"""
        while True:
            try:
                job = self._jobs.get_nowait()
            except queue.Empty:
                break
            print(f"[VSCode Server] 実行: {job.request.get('filepath')}")
            try:
                job.result = _execute(job.request)
            except Exception as exc:  # noqa: BLE001
                job.result = {"ok": False, "output": "", "error": {
                    "type": type(exc).__name__, "message": str(exc),
                    "frames": [], "traceback": traceback.format_exc()}}
            job.done.set()
        return 0.1  # 0.1 秒ごとにキューを確認


def start_server(port=None):
    global _server
    if _server is not None:
        return True
    if port is None:
        port = _get_prefs().port if _get_prefs() else DEFAULT_PORT
    port = int(os.environ.get("BLENDER_VSCODE_PORT", port))
    try:
        _server = _CodeServer(port)
    except OSError as exc:
        print(f"[VSCode Server] ポート {port} を開けませんでした: {exc}")
        _server = None
        return False
    _server.start()
    return True


def stop_server():
    global _server
    if _server is not None:
        _server.stop()
        _server = None


def is_running():
    return _server is not None


# ---------------------------------------------------------------------------
# UI (プリファレンス / オペレーター / サイドバーパネル)
# ---------------------------------------------------------------------------
def _get_prefs():
    addon = bpy.context.preferences.addons.get(__name__)
    return addon.preferences if addon else None


class VSCODESERVER_AP_preferences(bpy.types.AddonPreferences):
    bl_idname = __name__

    port: bpy.props.IntProperty(
        name="ポート", default=DEFAULT_PORT, min=1024, max=65535)
    auto_start: bpy.props.BoolProperty(
        name="起動時に自動でサーバーを開始", default=True)

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "port")
        layout.prop(self, "auto_start")


class VSCODESERVER_OT_start(bpy.types.Operator):
    bl_idname = "vscode_server.start"
    bl_label = "サーバー開始"

    def execute(self, context):
        if start_server():
            self.report({"INFO"}, f"VSCode サーバー開始 (port {_server.port})")
            return {"FINISHED"}
        self.report({"ERROR"}, "サーバーを開始できません (ポート使用中?)")
        return {"CANCELLED"}


class VSCODESERVER_OT_stop(bpy.types.Operator):
    bl_idname = "vscode_server.stop"
    bl_label = "サーバー停止"

    def execute(self, context):
        stop_server()
        self.report({"INFO"}, "VSCode サーバー停止")
        return {"FINISHED"}


class VSCODESERVER_PT_panel(bpy.types.Panel):
    bl_label = "VSCode Server"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "VSCode"

    def draw(self, context):
        layout = self.layout
        if is_running():
            layout.label(text=f"待機中: {HOST}:{_server.port}", icon="CHECKMARK")
            layout.operator("vscode_server.stop", icon="PAUSE")
        else:
            layout.label(text="停止中", icon="X")
            layout.operator("vscode_server.start", icon="PLAY")


_classes = (
    VSCODESERVER_AP_preferences,
    VSCODESERVER_OT_start,
    VSCODESERVER_OT_stop,
    VSCODESERVER_PT_panel,
)


def _auto_start():
    prefs = _get_prefs()
    if prefs is None or prefs.auto_start:
        start_server()
    return None  # 1 回だけ実行


def register():
    for cls in _classes:
        bpy.utils.register_class(cls)
    # register() 中はプリファレンスが読み込み途中のことがあるので少し遅らせる
    bpy.app.timers.register(_auto_start, first_interval=0.5)


def unregister():
    if bpy.app.timers.is_registered(_auto_start):
        bpy.app.timers.unregister(_auto_start)
    stop_server()
    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    # テキストエディタから直接実行した場合
    register()
