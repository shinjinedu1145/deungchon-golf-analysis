"""
등촌골프연습장 대시보드 — 공유 실행 스크립트
==============================================
사용법:
  python share.py          → 로컬 + LAN 접속만
  python share.py --public → 로컬 + LAN + 인터넷 공개 URL (ngrok)
"""
import subprocess
import sys
import socket
import time
import threading

PORT = 8501
PYTHON = r"C:\Users\win\AppData\Local\Programs\Python\Python312\python.exe"
STREAMLIT = r"C:\Users\win\AppData\Local\Programs\Python\Python312\Scripts\streamlit.exe"


def get_local_ip():
    """현재 PC의 LAN IP 주소를 가져옵니다."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "알 수 없음"


def start_streamlit():
    """Streamlit 서버를 0.0.0.0으로 시작합니다."""
    cmd = [
        STREAMLIT, "run", "app.py",
        "--server.port", str(PORT),
        "--server.address", "0.0.0.0",
        "--server.headless", "true",
        "--browser.gatherUsageStats", "false",
    ]
    return subprocess.Popen(cmd, cwd=r"C:\Users\win\Desktop\클로드 모델")


def start_ngrok():
    """pyngrok으로 공개 URL을 생성합니다."""
    try:
        from pyngrok import ngrok
        public_url = ngrok.connect(PORT)
        return str(public_url)
    except Exception as e:
        return f"ngrok 실패: {e}"


def main():
    use_public = "--public" in sys.argv
    local_ip = get_local_ip()

    print("=" * 60)
    print("  ⛳ 등촌골프연습장 사업성 분석 대시보드")
    print("=" * 60)
    print()

    # Start Streamlit
    print("🚀 Streamlit 서버 시작 중...")
    proc = start_streamlit()
    time.sleep(5)

    print()
    print("✅ 서버가 시작되었습니다!")
    print()
    print("─" * 50)
    print("  📌 접속 방법")
    print("─" * 50)
    print()
    print(f"  🖥️  이 PC에서 접속:")
    print(f"     → http://localhost:{PORT}")
    print()
    print(f"  🌐 같은 네트워크(사무실)에서 접속:")
    print(f"     → http://{local_ip}:{PORT}")
    print(f"     ※ 같은 Wi-Fi/LAN에 연결되어 있어야 합니다")
    print()

    if use_public:
        print("  🔗 인터넷 공개 URL 생성 중...")
        public_url = start_ngrok()
        if "ngrok 실패" not in public_url:
            print(f"  🌍 외부에서 접속 (어디서든):")
            print(f"     → {public_url}")
            print(f"     ※ 이 URL을 공유하면 누구나 접속 가능")
        else:
            print(f"  ⚠️  {public_url}")
            print(f"     ngrok 계정이 필요합니다:")
            print(f"     1. https://ngrok.com 에서 무료 가입")
            print(f"     2. ngrok config add-authtoken YOUR_TOKEN")
            print(f"     3. 다시 실행")
    else:
        print(f"  💡 인터넷 공개 URL이 필요하면:")
        print(f"     → python share.py --public")

    print()
    print("─" * 50)
    print("  🛑 종료하려면 Ctrl+C를 누르세요")
    print("─" * 50)

    try:
        proc.wait()
    except KeyboardInterrupt:
        print("\n서버를 종료합니다...")
        proc.terminate()
        try:
            from pyngrok import ngrok
            ngrok.kill()
        except Exception:
            pass


if __name__ == "__main__":
    main()
