import os

# 환경변수 설정
os.environ.setdefault("APP_LOCALE", "ko-KR")
os.environ.setdefault("VELOS_LANG", "ko")

print("환경변수 설정 완료:")
print(f"APP_LOCALE: {os.getenv('APP_LOCALE')}")
print(f"VELOS_LANG: {os.getenv('VELOS_LANG')}")

# 추가 확인
print(f"\n기존 환경변수 확인:")
print(f"VELOS_LANG: {os.getenv('VELOS_LANG')}")
print(f"LANG: {os.getenv('LANG')}")
print(f"LC_ALL: {os.getenv('LC_ALL')}")
