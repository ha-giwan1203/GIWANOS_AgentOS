import datetime
from modules.core.time_utils import now_utc, now_kst, iso_utc, monotonic

class WeeklySystemInsights:
    def generate_weekly_report(self):
        return f"주간 리포트 생성 완료: {datetime.now_utc().date()}"


