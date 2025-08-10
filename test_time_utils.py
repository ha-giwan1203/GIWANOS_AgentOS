from modules.core.time_utils import now_utc, now_kst, iso_utc, monotonic

print("UTC:", iso_utc())
print("KST:", now_kst().isoformat())

t0 = monotonic()
for _ in range(300000):
    pass
print("elapsed_ms:", int((monotonic() - t0) * 1000))
