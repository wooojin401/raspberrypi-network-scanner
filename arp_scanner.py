
import subprocess
import re

print("=== Raspberry Pi ARP Scanner ===")
print("우리 집 네트워크의 기기를 탐지합니다.\n")

result = subprocess.run(
    [
        "sudo",
        "arp-scan",
        "--interface=wlan0",
        "192.168.0.0/24"
    ],
    capture_output=True,
    text=True,
    timeout=30
)

if result.returncode != 0:
    print("스캔 오류:")
    print(result.stderr)
else:
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

    print(f"{'IP 주소':<18} {'MAC 주소':<20}")
    print("-" * 40)

    for ip, mac in devices:
        print(f"{ip:<18} {mac:<20}")

    print(f"\n총 {len(devices)}개 기기 발견!")
