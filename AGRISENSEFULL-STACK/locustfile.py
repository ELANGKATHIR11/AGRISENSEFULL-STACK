"""
Performance Testing with Locust for AgriSense API
Simulates realistic user load and measures response times
"""
from locust import HttpUser, task, between, TaskSet
import random
import json

class SensorDataTasks(TaskSet):
    """Tasks related to sensor data ingestion and retrieval"""
    
    @task(5)
    def get_recent_readings(self):
        """Get recent sensor readings"""
        self.client.get(
            "/recent",
            params={"limit": 10},
            name="/recent [GET]"
        )
    
    @task(3)
    def post_sensor_reading(self):
        """Post a new sensor reading"""
        payload = {
            "zone_id": f"zone_{random.randint(1, 10)}",
            "plant": random.choice(["tomato", "wheat", "corn", "potato"]),
            "soil_type": random.choice(["loam", "clay", "sandy"]),
            "area_m2": random.uniform(50, 200),
            "ph": random.uniform(5.5, 7.5),
            "moisture_pct": random.uniform(20, 70),
            "temperature_c": random.uniform(15, 35),
            "ec_dS_m": random.uniform(0.5, 2.0),
            "n_ppm": random.uniform(20, 60),
            "p_ppm": random.uniform(10, 30),
            "k_ppm": random.uniform(100, 200),
        }
        self.client.post(
            "/ingest",
            json=payload,
            name="/ingest [POST]"
        )

class RecommendationTasks(TaskSet):
    """Tasks related to crop recommendations"""
    
    @task(10)
    def get_recommendation(self):
        """Get irrigation and fertilizer recommendation"""
        payload = {
            "plant": random.choice(["tomato", "wheat", "corn", "potato", "rice"]),
            "soil_type": random.choice(["loam", "clay", "sandy"]),
            "area_m2": random.uniform(50, 200),
            "ph": random.uniform(5.5, 7.5),
            "moisture_pct": random.uniform(20, 70),
            "temperature_c": random.uniform(15, 35),
        }
        self.client.post(
            "/recommend",
            json=payload,
            name="/recommend [POST]"
        )

class ChatbotTasks(TaskSet):
    """Tasks related to chatbot queries"""
    
    questions = [
        "How much water does tomato need?",
        "What is the best fertilizer for wheat?",
        "When should I harvest corn?",
        "How to prevent potato blight?",
        "What causes leaf yellowing?",
    ]
    
    @task(7)
    def ask_question(self):
        """Ask chatbot a question"""
        question = random.choice(self.questions)
        self.client.post(
            "/chatbot/ask",
            json={"question": question, "top_k": 3},
            name="/chatbot/ask [POST]"
        )

class MonitoringTasks(TaskSet):
    """Tasks related to system monitoring"""
    
    @task(2)
    def health_check(self):
        """Check system health"""
        self.client.get("/health", name="/health [GET]")
    
    @task(1)
    def detailed_health(self):
        """Check detailed health"""
        self.client.get("/health/detailed", name="/health/detailed [GET]")

class AgriSenseUser(HttpUser):
    """
    Simulates a typical AgriSense user
    Mix of sensor data, recommendations, chatbot, and monitoring
    """
    wait_time = between(1, 5)  # Wait 1-5 seconds between tasks
    
    tasks = {
        SensorDataTasks: 30,
        RecommendationTasks: 40,
        ChatbotTasks: 20,
        MonitoringTasks: 10,
    }
    
    def on_start(self):
        """Called when a simulated user starts"""
        # Could add authentication here if needed
        pass

class BurstUser(HttpUser):
    """
    Simulates burst traffic patterns (IoT sensors reporting)
    """
    wait_time = between(0.5, 2)
    
    @task
    def rapid_sensor_posts(self):
        """Rapid sensor data posts (simulating IoT burst)"""
        for _ in range(random.randint(3, 10)):
            payload = {
                "zone_id": f"zone_{random.randint(1, 20)}",
                "plant": random.choice(["tomato", "wheat", "corn"]),
                "soil_type": "loam",
                "area_m2": 100,
                "ph": 6.5,
                "moisture_pct": random.uniform(30, 50),
                "temperature_c": random.uniform(20, 30),
            }
            self.client.post("/ingest", json=payload)

# Run configurations:
# 
# Light load:
#   locust -f locustfile.py --host=http://localhost:8004 --users 10 --spawn-rate 2
# 
# Medium load:
#   locust -f locustfile.py --host=http://localhost:8004 --users 50 --spawn-rate 5
# 
# Heavy load:
#   locust -f locustfile.py --host=http://localhost:8004 --users 200 --spawn-rate 10
# 
# Headless (CI):
#   locust -f locustfile.py --host=http://localhost:8004 --users 50 --spawn-rate 5 \
#          --run-time 5m --headless --html performance_report.html
