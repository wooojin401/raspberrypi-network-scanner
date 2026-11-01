
from flask import Flask, jsonify, render_template_string
import subprocess
import re
import threading
import time

app = Flask(__name__)

# 마지막 스캔 결과를 보관하는 공간
latest = {
    "devices": [],
    "updated": "아직 스캔 전",
    "error": None
}
lock = threading.Lock()

HTML = """
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport"
          content="width=device-width, initial-scale=1">
    <title>Pi Network Dashboard</title>
    <style>
        body {
            background: #0f172a;
            color: white;
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 30px;
        }
        h1 { text-align: center; }
        .summary {
            display: flex;
            gap: 15px;
            max-width: 900px;
            margin: 30px auto;
        }
        .card {
            background: #1e293b;
            border-radius: 12px;
            padding: 20px;
            text-align: center;
            flex: 1;
        }
        .number {
            font-size: 32px;
            color: #38bdf8;
            font-weight: bold;
        }
        table {
            width: 100%;
            max-width: 900px;
            margin: auto;
            border-collapse: collapse;
            background: #1e293b;
        }
        th, td {
            padding: 14px;
            border-bottom: 1px solid #334155;
            text-align: left;
        }
        .ok { color: #4ade80; }
        .no { color: #fbbf24; }
        #info {
            text-align: center;
            color: #94a3b8;
            margin: 20px;
        }
        @media (max-width: 600px) {
            body { padding: 12px; }
            .summary { gap: 6px; }
            .card { padding: 12px 5px; }
            .number { font-size: 24px; }
            th, td { padding: 8px 4px; font-size: 12px; }
        }
    </style>
</head>
<body>
    <h1>Pi Network Dashboard</h1>

    <div class="summary">
        <div class="card">
            <p>발견된 기기</p>
            <div class="number" id="total">0</div>
        </div>
        <div class="card">
            <p>Ping 응답</p>
            <div class="number" id="online">0</div>
        </div>
        <div class="card">
            <p>Ping 미응답</p>
            <div class="number" id="offline">0</div>
        </div>
    </div>

    <table>
        <thead>
            <tr>
                <th>IP 주소</th>
                <th>MAC 주소</th>
                <th>Ping 상태</th>
                <th>응답 시간</th>
            </tr>
        </thead>
        <tbody id="device-list"></tbody>
    </table>

    <p id="info">스캔 결과 불러오는 중...</p>

    <script>
        async function updateDashboard() {
            try {
                const response = await fetch("/api/devices");
                if (!response.ok) throw new Error("서버 오류");

                const data = await response.json();
                const devices = data.devices;

                document.getElementById("total").textContent =
                    devices.length;

                const online = devices.filter(
                    d => d.status === "응답"
                ).length;

                document.getElementById("online").textContent =
                    online;

                document.getElementById("offline").textContent =
                    devices.length - online;

                const tbody =
                    document.getElementById("device-list");
                tbody.replaceChildren();

                for (const d of devices) {
                    const row = document.createElement("tr");

                    for (const value of [
                        d.ip, d.mac, d.status, d.latency
                    ]) {
                        const cell = document.createElement("td");
                        cell.textContent = value;
                        row.appendChild(cell);
                    }

                    tbody.appendChild(row);
                }

                document.getElementById("info").textContent =
                    data.error
                    ? "스캔 오류: " + data.error
                    : "마지막 스캔: " + data.updated;

            } catch (error) {
                document.getElementById("info").textContent =
                    "서버 연결 오류";
            }
        }

        updateDashboard();
        setInterval(updateDashboard, 3000);
    </script>
</body>
</html>
"""


def scan_network():
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
        raise RuntimeError(result.stderr.strip())

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

            ping = subprocess.run(
                ["ping", "-c", "1", "-W", "1", ip],
                capture_output=True,
                text=True,
                timeout=3
            )

            status = "응답" if ping.returncode == 0 else "미응답"
            latency = "-"

            if status == "응답":
                found = re.search(
                    r"time[=<]([\d.]+)",
                    ping.stdout
                )
                if found:
                    latency = found.group(1) + " ms"

            devices.append({
                "ip": ip,
                "mac": mac,
                "status": status,
                "latency": latency
            })

    return devices


def background_scanner():
    while True:
        try:
            devices = scan_network()
            with lock:
                latest["devices"] = devices
                latest["updated"] = time.strftime("%H:%M:%S")
                latest["error"] = None
        except Exception as error:
            with lock:
                latest["error"] = str(error)

        time.sleep(30)


@app.route("/")
def home():
    return render_template_string(HTML)


@app.route("/api/devices")
def api_devices():
    with lock:
        return jsonify(latest.copy())


if __name__ == "__main__":
    worker = threading.Thread(
        target=background_scanner,
        daemon=True
    )
    worker.start()

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False
    )
