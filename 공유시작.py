"""
등촌골프연습장 대시보드 — 외부 공유 (계정 불필요)
====================================================
실행: 이 파일을 더블클릭하거나 cmd에서 python 공유시작.py
종료: Ctrl+C
"""
import subprocess
import sys
import time
import socket
import re
import os

PYTHON = r"C:\Users\win\AppData\Local\Programs\Python\Python312\python.exe"
STREAMLIT = r"C:\Users\win\AppData\Local\Programs\Python\Python312\Scripts\streamlit.exe"
CLOUDFLARED = os.path.join(r"C:\Users\win\Desktop\클로드 모델", "cloudflared.exe")
PORT = 8501
APP_DIR = r"C:\Users\win\Desktop\클로드 모델"


def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "확인불가"


def start_streamlit():
    return subprocess.Popen(
        [STREAMLIT, "run", "app.py",
         "--server.port", str(PORT),
         "--server.address", "0.0.0.0",
         "--server.headless", "true",
         "--browser.gatherUsageStats", "false"],
        cwd=APP_DIR
    )


def start_cloudflare_tunnel():
    """Cloudflare Quick Tunnel — 계정 불필요, 바로 공개 URL 생성"""
    proc = subprocess.Popen(
        [CLOUDFLARED, "tunnel", "--url", f"http://localhost:{PORT}"],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, encoding='utf-8', errors='replace'
    )

    # URL이 나올 때까지 읽기 (최대 30초)
    public_url = None
    start = time.time()
    for line in proc.stdout:
        if "trycloudflare.com" in line:
            urls = re.findall(r'https://[a-zA-Z0-9-]+\.trycloudflare\.com', line)
            if urls:
                public_url = urls[0]
                break
        if time.time() - start > 30:
            break

    return proc, public_url


def main():
    local_ip = get_local_ip()

    print()
    print("=" * 65)
    print("  ⛳ 등촌골프연습장 사업성 분석 대시보드")
    print("  외부 공유 모드 (Cloudflare Tunnel)")
    print("=" * 65)
    print()
    print("  🚀 Streamlit 서버 시작 중...")

    st_proc = start_streamlit()
    time.sleep(6)

    print("  ✅ 서버 시작 완료!")
    print()
    print("  🔗 공개 URL 생성 중 (약 10~15초 소요)...")
    print()

    cf_proc, public_url = start_cloudflare_tunnel()

    print("─" * 65)
    print()
    print(f"  🖥️  이 PC에서:       http://localhost:{PORT}")
    print(f"  🌐 같은 네트워크:   http://{local_ip}:{PORT}")
    print()

    if public_url:
        print(f"  🌍 외부 접속 URL (어디서든 접속 가능):")
        print()
        print(f"     {public_url}")
        print()
        print(f"  📱 위 URL을 카톡/문자로 보내면 누구나 접속할 수 있습니다!")
    else:
        print(f"  ⚠️ 공개 URL 생성에 실패했습니다.")
        print(f"     같은 네트워크에서는 http://{local_ip}:{PORT} 로 접속 가능")

    print()
    print(f"  🔐 로그인 정보:")
    print(f"     아이디: shinjin1145")
    print(f"     비번:   sj3546005")
    print()
    print("─" * 65)
    print("  🛑 종료: Ctrl+C 또는 이 창 닫기")
    print("─" * 65)
    print()

    try:
        st_proc.wait()
    except KeyboardInterrupt:
        print("\n  서버를 종료합니다...")
        st_proc.terminate()
        if cf_proc:
            cf_proc.terminate()


if __name__ == "__main__":
    main()
