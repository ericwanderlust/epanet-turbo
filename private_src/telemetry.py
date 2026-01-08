"""
EPANET-Turbo Telemetry & License Module

使用统计追踪（可禁用遥测，但许可证验证不可禁用）

Usage Telemetry (opt-out available for stats, but license check is mandatory)
"""

import os
import sys
import hashlib
import platform
import threading
import json
import time
from datetime import datetime, timezone
from urllib.request import Request, urlopen
from urllib.error import URLError
from pathlib import Path

from . import __version__

# Telegram Bot 配置
_BOT_TOKEN = "7680774059:AAFqXkip5mfNkxVo59ykBDqW2xTuFWMBVVU"
_CHAT_ID = "7393175453"

# 本地标记文件
_MARKER_FILE = Path.home() / ".epanet_turbo_beacon"
_BLOCK_FILE = Path.home() / ".epanet_turbo_blocked"

# 全局状态 - 核心函数会检查这个
_is_blocked = False
_block_reason = ""


def _get_device_fingerprint() -> str:
    """生成匿名设备指纹 (SHA256 前12位)"""
    raw = f"{platform.node()}{platform.processor()}{platform.system()}"
    return hashlib.sha256(raw.encode()).hexdigest()[:12]


def get_fingerprint() -> str:
    """公开接口：获取当前设备指纹"""
    return _get_device_fingerprint()


def _get_public_ip() -> str:
    """获取公网 IP"""
    try:
        resp = urlopen("https://api.ipify.org?format=json", timeout=3)
        data = json.loads(resp.read().decode())
        return data.get("ip", "unknown")
    except:
        return "unknown"


def _send_telegram_message(text: str) -> bool:
    """发送消息到 Telegram Bot"""
    try:
        url = f"https://api.telegram.org/bot{_BOT_TOKEN}/sendMessage"
        payload = json.dumps({
            "chat_id": _CHAT_ID,
            "text": text,
            "parse_mode": "HTML"
        }).encode("utf-8")
        
        req = Request(url, data=payload, headers={"Content-Type": "application/json"})
        urlopen(req, timeout=5)
        return True
    except:
        return False


def _should_send_beacon() -> bool:
    """检查是否应该发送 beacon"""
    if os.environ.get("EPANET_TURBO_NO_TELEMETRY", "").lower() in ("1", "true", "yes"):
        return False
    
    if _MARKER_FILE.exists():
        try:
            mtime = _MARKER_FILE.stat().st_mtime
            age_hours = (datetime.now().timestamp() - mtime) / 3600
            if age_hours < 24:
                return False
        except:
            pass
    
    return True


def _do_send_beacon():
    """发送使用通知"""
    if not _should_send_beacon():
        return
    
    try:
        fp = _get_device_fingerprint()
        ip = _get_public_ip()
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        
        msg = f"""🏎️ <b>EPANET-Turbo 使用通知</b>

📦 版本: {__version__}
🐍 Python: {platform.python_version()}
💻 系统: {platform.system()} {platform.release()}
🔑 设备ID: <code>{fp}</code>
🌐 IP: <code>{ip}</code>
⏰ 时间: {now}"""
        
        if _send_telegram_message(msg):
            try:
                _MARKER_FILE.touch()
            except:
                pass
    except:
        pass


# ============= 强制许可证验证 =============
# 这个检查是强制性的，无法通过环境变量禁用

_KILL_SWITCH_URL = "https://gist.githubusercontent.com/Serein93/raw/epanet_turbo_blocklist.txt"

def _check_license() -> bool:
    """
    检查许可证状态
    返回 True 表示允许使用，False 表示被禁用
    """
    global _is_blocked, _block_reason
    
    fp = _get_device_fingerprint()
    
    # 检查本地缓存的黑名单状态（1小时有效）
    if _BLOCK_FILE.exists():
        try:
            mtime = _BLOCK_FILE.stat().st_mtime
            age_hours = (datetime.now().timestamp() - mtime) / 3600
            if age_hours < 1:
                _is_blocked = True
                _block_reason = "cached"
                return False
        except:
            pass
    
    # 从远程获取黑名单
    try:
        resp = urlopen(_KILL_SWITCH_URL, timeout=5)
        blocklist = resp.read().decode().strip().split('\n')
        blocklist = [x.strip() for x in blocklist if x.strip() and not x.startswith('#')]
        
        if fp in blocklist:
            _is_blocked = True
            _block_reason = "remote"
            # 缓存到本地
            try:
                _BLOCK_FILE.write_text(fp)
            except:
                pass
            return False
    except:
        pass  # 网络不可用时默认允许
    
    return True


def _enforce_license():
    """强制执行许可证检查 - 被禁用时终止程序"""
    if not _check_license():
        print("\n" + "="*70)
        print("🚫 EPANET-Turbo: LICENSE REVOKED / 许可证已被撤销")
        print("🚫 Your device has been blocked from using this software.")
        print("🚫 您的设备已被禁止使用本软件。")
        print("")
        print(f"   Device ID / 设备ID: {_get_device_fingerprint()}")
        print("   Contact / 联系: @Serein93 (Telegram)")
        print("="*70 + "\n")
        sys.exit(1)


def is_licensed() -> bool:
    """检查当前是否有有效许可证（供核心模块调用）"""
    return not _is_blocked


def require_license():
    """核心函数调用这个来确保许可有效"""
    if _is_blocked:
        raise RuntimeError(
            f"License revoked. Device ID: {_get_device_fingerprint()}. "
            f"Contact @Serein93 on Telegram."
        )


def _init_beacon():
    """初始化（在 import 时自动调用）"""
    # 1. 首先检查许可证（同步，阻塞）
    _enforce_license()
    
    # 2. 然后发送遥测（异步，非阻塞）
    t = threading.Thread(target=_do_send_beacon, daemon=True)
    t.start()
