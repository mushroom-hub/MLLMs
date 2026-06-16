import os
import shutil
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent


def check_command(cmd: str) -> bool:
    return shutil.which(cmd) is not None


def run_command(args, cwd=None) -> int:
    process = subprocess.Popen(
        args,
        cwd=cwd or PROJECT_ROOT,
        stdin=sys.stdin,
        stdout=sys.stdout,
        stderr=sys.stderr,
        shell=False,
    )
    try:
        return process.wait()
    except KeyboardInterrupt:
        process.terminate()
        return process.wait()


def main() -> int:
    os.chdir(PROJECT_ROOT)

    if not check_command("node") or not check_command("npm"):
        print("未检测到 Node.js 或 npm。请先安装 Node.js 并确保它们已加入 PATH。")
        print("https://nodejs.org/")
        return 1

    if not (PROJECT_ROOT / "node_modules").exists():
        print("检测到 node_modules 缺失，正在安装依赖...\n")
        code = run_command(["npm", "install"])
        if code != 0:
            print(f"npm install 失败，退出码：{code}")
            return code

    print("依赖已安装，启动前端开发服务器...\n")
    print("如果你的浏览器没有自动打开，请访问：http://localhost:5173\n")
    return run_command(["npm", "run", "dev"])


if __name__ == "__main__":
    sys.exit(main())
