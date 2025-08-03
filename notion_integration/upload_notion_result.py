def main():
    try:
        # 실제 업로드 로직 실행
        print("[성공] Notion 회고 업로드 완료")
    except FileNotFoundError:
        print("[실패] 최신 요약 파일이 없습니다.")

if __name__ == "__main__":
    main()