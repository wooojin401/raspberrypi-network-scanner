
import subprocess
import re

devices = {
    "ipTIME 공유기": "192.168.0.1",
    "Windows 컴퓨터": "192.168.0.10",
}

print("=== Raspberry Pi Network Scanner ===")

for name, ip in devices.items():
    result = subprocess.run(
        ["ping", "-c", "2", "-W", "1", ip],
        capture_output=True,
        text=True,
        timeout=5
    )

    match = re.search(r"time[=<]([\d.]+)", result.stdout)

    print(f"\n기기: {name}")
    print(f"IP 주소: {ip}")

    if result.returncode == 0:
        print("상태: Ping 응답")
        if match:
            print(f"응답 시간: {match.group(1)} ms")
    else:
        print("상태: Ping 미응답")
        print("응답 시간: 측정 불가")

print("\n스캔 완료!")
