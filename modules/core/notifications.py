"""
File: C:/giwanos/core/notifications.py

설명:
- 이메일 및 알림 발송 관련 유틸리티
- send_welcome_email, mark_as_adult 함수 구현
"""

import logging

logger = logging.getLogger(__name__)

def send_welcome_email():
    """
    환영 이메일을 발송합니다.
    실제 SMTP 또는 이메일 API 연동 코드를 여기에 구현하세요.
    """
    logger.info("Welcome email sent to user.")
    # TODO: SMTP 서버 설정 또는 이메일 API 호출 추가

def mark_as_adult():
    """
    사용자를 성인으로 마킹합니다.
    실제 사용자 관리 시스템/데이터베이스와 연동하여 처리하세요.
    """
    logger.info("User has been marked as adult in the system.")
    # TODO: DB 업데이트 등 구현
