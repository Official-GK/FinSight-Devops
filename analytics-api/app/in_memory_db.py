import collections
import time
from datetime import datetime
from threading import Lock

# In-memory storage for demonstration purposes
class InMemoryStats:
    def __init__(self):
        self.lock = Lock()
        self.total_transactions = 0
        self.total_risk_score = 0.0
        self.high_risk_transactions = 0
        self.recent_transactions = collections.deque(maxlen=50)
        self.transactions_over_time = collections.deque(maxlen=60) # 1 minute of data
        self.risk_trend = collections.deque(maxlen=60)
        self.risk_distribution = {
            "LOW": 0,
            "MEDIUM": 0,
            "HIGH": 0,
            "CRITICAL": 0
        }
        self.last_tick = int(time.time())
        self.current_second_requests = 0
        self.rps = 0.0
        self.transaction_id_counter = 0

    def get_next_transaction_id(self):
        with self.lock:
            self.transaction_id_counter += 1
            return self.transaction_id_counter

    def record_transaction(self, response):
        with self.lock:
            self.total_transactions += 1
            self.total_risk_score += response.risk_score
            self.recent_transactions.appendleft(response)
            
            risk_level = response.risk_level.value
            if risk_level in ["HIGH", "CRITICAL"]:
                self.high_risk_transactions += 1
            self.risk_distribution[risk_level] = self.risk_distribution.get(risk_level, 0) + 1

            now = int(time.time())
            if now > self.last_tick:
                # Update RPS
                self.rps = self.current_second_requests / max(1, (now - self.last_tick))
                
                time_str = datetime.utcnow().strftime("%H:%M:%S")
                self.transactions_over_time.append({"time": time_str, "value": self.current_second_requests * 60})
                avg_risk = (self.total_risk_score / self.total_transactions) if self.total_transactions > 0 else 0
                self.risk_trend.append({"time": time_str, "value": round(avg_risk, 2)})
                
                self.current_second_requests = 1
                self.last_tick = now
            else:
                self.current_second_requests += 1

db = InMemoryStats()
