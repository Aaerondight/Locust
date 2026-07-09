import sys
from locust import HttpUser, task

class HelloWorldUser(HttpUser):

    @task
    def hello_world(self):
        self.client.get("/")

    @task
    def sla(self):
        with self.client.get("/contact-us", catch_response=True) as response:
            if response.request_meta["response_time"] > 1200:
                response.failure("Exceeded SLA")





