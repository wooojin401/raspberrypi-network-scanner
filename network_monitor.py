
import subprocess
import re

# 1. ARP로 기기 자동 탐지
def scan_devices():
    result = subprocess.run(
        [
            "arp-scan",
            "--interface=wlan0",
            "192.168.0.0/24"
        ],
        capture_output=True,
        text=True,
        timeout=30
    )

    if result.returncode != 0:
        print("ARP 스캔 오류:", result.stderr)
        return []

    devices = []

    for line in result.stdout.splitlines():
        match = re.match(
            r"^(192\.168\.0\.\d+)\s+"
            r"([0-9a-fA-F:]{17})",
            line
        )

        if match:
            ip = match.group(1)
            mac = match.group(2)
            devices.append((ip, mac))

    return devices


# 2. 각 기기의 Ping 응답 시간 확인
def check_ping(ip):
    try:
        result = subprocess.run(
            ["ping", "-c", "1", "-W", "1", ip],
            capture_output=True,
            text=True,
            timeout=3
        )

        if result.returncode != 0:
            return "미응답", "-"

        match = re.search(
            r"time[=<]([\d.]+)",
            result.stdout
        )

        if match:
            return "응답", match.group(1) + " ms"

        return "응답", "측정 불가"

    except subprocess.TimeoutExpired:
        return "시간 초과", "-"


# 3. 탐지 결과 출력
print("=== Pi Network Monitor ===")
print("네트워크 기기를 탐지하는 중...\n")

devices = scan_devices()

print(
    f"{'IP 주소':<18}"
    f"{'MAC 주소':<20}"
    f"{'Ping 상태':<12}"
    f"응답 시간"
)
print("-" * 65)

for ip, mac in devices:
    status, response_time = check_ping(ip)

    print(
        f"{ip:<18}"
        f"{mac:<20}"
        f"{status:<12}"
        f"{response_time}"
    )

print(f"\n총 {len(devices)}개 기기 발견!")
