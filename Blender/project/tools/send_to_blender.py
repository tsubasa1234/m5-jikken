"""VSCode で開いている Python スクリプトを Blender に送信して実行するクライアント

使い方:
    python3 tools/send_to_blender.py <実行するファイル> [プロジェクトルート]

Blender 側で vscode_blender_server アドオンが待機している必要がある。
標準ライブラリのみ使用 (追加インストール不要)。
"""

import argparse
import json
import os
import socket
import struct
import sys

HOST = "127.0.0.1"
DEFAULT_PORT = 52525  # vscode_blender_server.py の DEFAULT_PORT と合わせる
CONNECT_TIMEOUT = 3.0
RESULT_TIMEOUT = 600.0


def _recv_exact(sock, size):
    buf = bytearray()
    while len(buf) < size:
        chunk = sock.recv(size - len(buf))
        if not chunk:
            raise ConnectionError("Blender との接続が途中で切断されました")
        buf.extend(chunk)
    return bytes(buf)


def send_request(request, port):
    data = json.dumps(request, ensure_ascii=False).encode("utf-8")
    with socket.create_connection((HOST, port), timeout=CONNECT_TIMEOUT) as sock:
        sock.settimeout(RESULT_TIMEOUT)
        sock.sendall(struct.pack(">I", len(data)) + data)
        (length,) = struct.unpack(">I", _recv_exact(sock, 4))
        return json.loads(_recv_exact(sock, length).decode("utf-8"))


def build_sys_paths(filepath, project_root):
    """Blender 側の sys.path に追加するディレクトリ (先頭ほど優先)

    - スクリプト自身のディレクトリ : 同じフォルダのモジュールを import できる
    - プロジェクトルート            : `from mylib import xxx` のようにルート基準で import できる
    - プロジェクトルート/src        : src レイアウトの場合 (存在するときのみ)
    """
    paths = [os.path.dirname(filepath)]
    if project_root:
        paths.append(project_root)
        src = os.path.join(project_root, "src")
        if os.path.isdir(src):
            paths.append(src)
    result = []
    for p in paths:
        p = os.path.abspath(p)
        if p not in result:
            result.append(p)
    return result


def print_error(error, filepath):
    if error.get("traceback"):
        print(error["traceback"], end="", file=sys.stderr)
    # tasks.json の problemMatcher が拾えるよう「ファイル:行: error: メッセージ」形式でも出力。
    # 送信したファイル内の最も深いフレームを優先し、無ければ一番深いフレームを使う。
    frames = [f for f in error.get("frames", []) if f.get("file") and f.get("line")]
    target = next((f for f in reversed(frames) if os.path.abspath(f["file"]) == filepath), None)
    if target is None and frames:
        target = frames[-1]
    location = f'{target["file"]}:{target["line"]}' if target else filepath
    print(f'{location}: error: {error.get("type")}: {error.get("message")}', file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(description="Python スクリプトを Blender に送信して実行する")
    parser.add_argument("file", help="実行する Python ファイル")
    parser.add_argument("project_root", nargs="?", default=None,
                        help="プロジェクトルート (sys.path に追加される)")
    parser.add_argument("--port", type=int,
                        default=int(os.environ.get("BLENDER_VSCODE_PORT", DEFAULT_PORT)))
    args = parser.parse_args()
    # stdout と stderr の表示順がずれないよう行単位で出力
    sys.stdout.reconfigure(line_buffering=True)

    filepath = os.path.abspath(args.file)
    if not filepath.endswith(".py"):
        print(f"Python ファイルではありません: {filepath}", file=sys.stderr)
        return 2
    try:
        with open(filepath, encoding="utf-8") as f:
            code = f.read()
    except OSError as exc:
        print(f"ファイルを読み込めません: {exc}", file=sys.stderr)
        return 2

    request = {
        "code": code,
        "filepath": filepath,
        "sys_paths": build_sys_paths(filepath, args.project_root),
    }

    print(f"▶ Blender ({HOST}:{args.port}) へ送信: {os.path.basename(filepath)}")
    try:
        response = send_request(request, args.port)
    except ConnectionRefusedError:
        print(f"Blender に接続できません ({HOST}:{args.port})。\n"
              "Blender が起動していて、アドオン「VSCode Code Runner Server」が有効か確認してください。",
              file=sys.stderr)
        return 1
    except (socket.timeout, TimeoutError):
        print("Blender からの応答がタイムアウトしました。", file=sys.stderr)
        return 1

    if response.get("output"):
        print(response["output"], end="" if response["output"].endswith("\n") else "\n")
    if response.get("ok"):
        print("✔ 実行完了")
        return 0
    print_error(response.get("error") or {}, filepath)
    print("✘ 実行エラー", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
