from locust import HttpUser, task, events
import locust.stats


@events.init.add_listener
def on_locust_bootstrap(**kwargs):
    locust.stats.PERCENTILES_TO_CHART = [0.5, 0.9, 0.95, 0.99]


class HelloWorldUser(HttpUser):

    @task(5)
    def hello_world(self):
        self.client.get("/")

    @task
    def sla(self):
        with self.client.get("/contact-us", catch_response=True) as response:
            if response.request_meta["response_time"] > 1200:
                response.failure("Exceeded SLA")

    @task
    def check_pagination(self):
        self.client.get("/shop/residential", name="Shop")
        self.client.get("/shop/cubby-house", name="Shop")
        self.client.get("/shop/work-wellness", name="Shop")





