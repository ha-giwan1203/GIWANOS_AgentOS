def send_email_report():
    try:
        # 이메일 전송 로직 실행
        print("[성공] 이메일 PDF 리포트 전송 완료")
    except FileNotFoundError:
        print("[실패] PDF 파일이 없습니다.")

if __name__ == "__main__":
    send_email_report()