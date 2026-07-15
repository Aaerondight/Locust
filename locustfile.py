from locust import HttpUser, task, events, LoadTestShape, TaskSet, between
import locust.stats

@events.init.add_listener
def on_locust_bootstrap(**_kwargs):
    locust.stats.PERCENTILES_TO_CHART = [0.5, 0.9, 0.95, 0.99]


class UserTasks(TaskSet):
    @task(5)
    def get_root(self):
        self.client.get("/")

    @task(1)
    def contact_us_sla(self):
        with self.client.get("/contact-us", catch_response=True) as response:
            if response.request_meta["response_time"] > 1200:
                response.failure("Exceeded SLA")


class ShopTask(TaskSet):
    @task(2)
    def get_shop(self):
        self.client.get("/shop/residential")

    @task(1)
    def get_shop_two(self):
        self.client.get("/shop/work-wellness")

class RampingUser(HttpUser):
    wait_time = between(0.5, 1.5)
    tasks = [UserTasks]

class User_USA(HttpUser):
    tasks = [UserTasks]

class User_EU(HttpUser):
    wait_time = between(0.5,1)
    tasks = [ShopTask]

class User_AU(HttpUser):
    wait_time = between(3,5)
    tasks = [ShopTask]

# class HelloWorldUser(HttpUser):
#
#     @task(5)
#     def hello_world(self):
#         self.client.get("/")
#
#     @task
#     def sla(self):
#         with self.client.get("/contact-us", catch_response=True) as response:
#             if response.request_meta["response_time"] > 1200:
#                 response.failure("Exceeded SLA")
#
#     @task
#     def check_pagination(self):
#         self.client.get("/shop/residential", name="Shop")
#         self.client.get("/shop/cubby-house", name="Shop")
#         self.client.get("/shop/work-wellness", name="Shop")

class DifferentUserShap(LoadTestShape):

    stages = [
        #Warm up
        {"duration":30, "users":50, "spawn_rate":10, "user_classes": [User_USA]},

        #Low steady load
        {"duration":20, "users":200, "spawn_rate":20, "user_classes": [User_EU]},

        #Expected load
        {"duration":30, "users":400, "spawn_rate":30, "user_classes": [User_AU]},

        #High load but should survive
        {"duration":10, "users":800, "spawn_rate":40, "user_classes": [User_AU, User_EU]},

    ]

    def tick(self):
        run_time = self.get_run_time()

        for stage in self.stages:
            if run_time < stage["duration"]:
                return stage["users"], stage["spawn_rate"], stage["user_classes"]
            run_time -= stage["duration"]
        return None


class RecoveryAfterRamp(LoadTestShape):

    stages = [
        #Warm up
        {"duration":30, "users":50, "spawn_rate":10},

        #Low steady load
        {"duration":10, "users":200, "spawn_rate":20},

        #Expected load
        {"duration":10, "users":400, "spawn_rate":30},

        #High load but should survive
        {"duration":10, "users":800, "spawn_rate":40},

        #Overload (expect degradation)
        {"duration": 10, "users": 1000, "spawn_rate": 50},

        #Recovery test
        {"duration": 10, "users": 300, "spawn_rate": 30}

    ]

    def tick(self):
        run_time = self.get_run_time()

        for stage in self.stages:
            if run_time < stage["duration"]:
                return stage["users"], stage["spawn_rate"]
            run_time -= stage["duration"]

        return None



