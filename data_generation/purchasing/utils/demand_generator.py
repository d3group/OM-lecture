import random
import datetime


# --- 1. The User's Demand Generator ---
class DemandGenerator:
    def __init__(self, start_date, end_date, dc_count=16):
        self.start = datetime.date.fromisoformat(start_date)
        self.end = datetime.date.fromisoformat(end_date)
        self.dc_count = dc_count
        self.dates = [
            (self.start + datetime.timedelta(days=i)).isoformat()
            for i in range((self.end - self.start).days + 1)
        ]

    def generate(self):
        lines = []
        # Header for easier pandas parsing later
        lines.append("DC,Date,Demand")
        for dc in range(1, self.dc_count + 1):
            base_avg = random.randint(30, 70)
            for date in self.dates:
                noise = random.randint(-15, 15)
                demand = max(0, base_avg + noise)
                lines.append(f"DC{dc},{date},{demand}")
        return lines

