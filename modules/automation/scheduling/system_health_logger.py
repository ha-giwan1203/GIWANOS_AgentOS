import psutil, GPUtil, socket, requests

TEMPLATE = {
    ...,
    "gpu_percent": 0.0,
    "net_sent_mb": 0.0,
    "net_recv_mb": 0.0,
}
def current_stats():
    s = TEMPLATE.copy()
    ...
    # GPU (첫 카드 기준)
    try:
        g = GPUtil.getGPUs()[0]
        s["gpu_percent"] = g.load * 100
    except Exception: pass

    # 네트워크
    try:
        io = psutil.net_io_counters()
        s["net_sent_mb"]  = round(io.bytes_sent  / 1_048_576, 2)
        s["net_recv_mb"]  = round(io.bytes_recv  / 1_048_576, 2)
    except Exception: pass
    return s
