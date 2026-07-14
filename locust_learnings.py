"""
Locust learning notes.

This file is a reference/example file. Your real test file is locustfile.py.

Main idea:
Locust sends HTTP requests from simulated users. The numbers in the Locust UI
come from many individual request results being grouped together.


1. HttpUser

HttpUser represents one simulated user.
It gives you self.client, which sends HTTP requests.

Example:
    self.client.get("/")

That sends one GET request to the host you configured in Locust.


2. catch_response=True

By default, Locust decides success/failure from HTTP status codes:
    2xx/3xx = success
    4xx/5xx = failure

catch_response=True lets you manually decide if a request passed or failed.
This is needed when a request returns HTTP 200 but is still too slow.


3. request_meta

response.request_meta is Locust's per-request metadata.
It is data for ONE request, not the final aggregated table.

Common keys:
    request_type      -> "GET", "POST", etc.
    name              -> name shown in the stats table
    response_time     -> Locust response time in milliseconds
    response_length   -> response size in bytes
    exception         -> failure reason, or None
    url               -> full URL
    start_time        -> when the request started
    context           -> extra context data

Important:
    response.request_meta["response_time"]
matches the kind of timing Locust uses for Avg, Min, Max, Median, 95%, 99%.


4. response.elapsed vs request_meta["response_time"]

response.elapsed comes from the Python requests library.
response.request_meta["response_time"] comes from Locust.

If you want to compare against Locust's UI numbers, use:
    response.request_meta["response_time"]


5. Response time units

Locust stats are shown in milliseconds.

    1000 ms = 1 second
    1371 ms = 1.371 seconds

So a 1 second threshold should be written as:
    response_time > 1000


6. response.failure("reason")

response.failure(...) marks that specific request as failed in Locust stats.

Do this:
    response.failure("Exceeded 1 second SLA")

Avoid using sys.exit(1) inside a Locust task to mark request failure.
Locust users run inside greenlets, so sys.exit(1) is not a clean request
failure mechanism and can interrupt reporting.


6a. SLA / Service Level Agreement

SLA means Service Level Agreement.
It is a measurable promise about the quality of a service.

An SLA can include one target, multiple targets, or many targets across
different parts of the service.

Example SLA targets:
    Website uptime must be 99.9% per month.
    95% of requests must finish under 1 second.
    API error rate must stay below 1%.
    Checkout page must be available during business hours.
    Support tickets must receive a first response within 4 hours.

In Locust, you mainly test technical targets such as:
    response time
    failure rate
    requests per second
    behavior under many users

Locust does not directly test business/support targets like:
    support ticket response time
    monthly uptime by itself

If there is no official SLA, you can still define a testing threshold.
Example:
    "Contact page should respond within 1200 ms"

In that case, "performance target" or "threshold" may be more accurate than
"SLA", because an SLA is usually a formal agreement.


7. Median and percentiles

Median = 50th percentile.
It means 50% of requests were this time or faster.

95% means 95% of requests were this time or faster.
99% means 99% of requests were this time or faster.

Example:
    Median = 1300 ms
    95%    = 1600 ms
    99%    = 1800 ms

Meaning:
    50% of requests finished in 1.3s or less
    95% of requests finished in 1.6s or less
    99% of requests finished in 1.8s or less


8. Stability examples

Stable but maybe slow:
    Median = 1300 ms
    95%    = 1600 ms
    99%    = 1800 ms

Unstable:
    Median = 300 ms
    95%    = 1600 ms
    99%    = 1800 ms

The second example is unstable because normal requests are fast, but some
requests are much slower.


9. Common performance patterns

General slowness:
    Median high, 95% high, 99% high.
    Most requests are slow.

Instability:
    Median low, 95% much higher.
    Most requests are okay, but some users get slow responses.

Outlier:
    Median good, 95% good, 99% good, Max huge.
    One or a few requests were unusually slow.

Capacity limit:
    Users increase, but req/s stops increasing.
    Latency rises and failures may start.

Example:
    10 users  -> 100 req/s
    50 users  -> 300 req/s
    100 users -> 310 req/s

This suggests the server is near a limit around 300 req/s.


10. Load testing vs stress testing

Load testing:
    Test expected/normal traffic.
    Check whether performance is acceptable.

Stress testing:
    Push beyond expected traffic.
    Find where the system slows down, fails, or stops scaling.


11. What is a good RPS?

A good req/s number depends on your SLA.

Example SLA:
    95% response time under 1000 ms
    failures under 1%

Your "good RPS" is the highest req/s you can reach while still meeting
those targets.


12. Server location matters

The farther the Locust machine is from the server, the higher the network
latency usually is.

Same region might be very fast.
Australia to US/Europe will usually have much higher minimum latency.


13. What counts as a request?

A request is one HTTP call.

In Locust:
    self.client.get("/contact-us")

That is one request.

In a real browser, opening one page can create many requests:
    GET /contact-us
    GET /static/site.css
    GET /static/app.js
    GET /logo.png
    GET /api/contact-info

Locust does not automatically behave like a browser. It only sends the
requests you write in Python.


14. Locust vs real browser performance

Locust is best for backend/load testing:
    HTTP endpoints
    APIs
    server response times
    req/s
    failure rates
    capacity limits

Locust does not measure real browser rendering:
    CSS rendering
    JavaScript execution
    layout shifts
    paint time
    Lighthouse scores

For real browser page performance, use tools like:
    Chrome Lighthouse
    Chrome DevTools Network/Performance tab
    WebPageTest
    Playwright

Good split:
    Lighthouse/WebPageTest = one-user browser experience
    Locust = many-user backend/load behavior


15. Choosing requests from the browser Network tab

Do not copy every request blindly.

Usually include:
    main HTML page requests
    real /api/... calls
    form submissions
    search, login, checkout, dashboard endpoints
    slow own-domain requests

Usually skip:
    cached files
    analytics/telemetry
    browser extension requests
    tiny icons
    third-party scripts unless you specifically care about them
    framework prefetch noise unless it represents real user behavior

Useful Network tab filters:
    HTML    -> main page request
    XHR     -> API/fetch requests
    JS/CSS  -> important static assets if you care about asset latency
    Images  -> usually skip for Locust unless image delivery is the concern

Sort by:
    Time -> find slow requests
    Size -> find large responses


16. Next.js / React Server Component requests

Requests like this are real HTTP requests:
    /contact-us?_rsc=...
    /residential?_rsc=...
    /boat-shed?_rsc=...

They are often framework-generated route/component fetches.

They can be included in Locust, but do not include all of them just because
they appear in the Network tab. Include them only if they represent the user
journey you want to simulate.

Bad model:
    Every simulated user instantly requests every page.

Better model:
    Some users visit the homepage.
    Some browse product/category pages.
    Fewer visit the contact page.


17. Grouping requests with name=

The name argument changes how Locust groups stats.

Example:
    self.client.get("/product/123", name="/product/:id")
    self.client.get("/product/456", name="/product/:id")

Locust reports both under:
    /product/:id

This is useful for dynamic URLs.

But if you give many different resources the same name:
    self.client.get("/contact-us", name="Contact page")
    self.client.get("/static/site.css", name="Contact page")
    self.client.get("/api/contact-info", name="Contact page")

Locust combines those separate request timings into one row. That is useful
for a broad bucket, but it hides which specific request is slow.

For debugging, use separate names:
    Contact page - HTML
    Contact page - CSS
    Contact page - API


18. Page performance in Locust

Locust can approximate backend/resource behavior for a page by requesting
important page resources and APIs.

But grouped request stats are still per-request timings, not true browser page
load time.

Example:
    HTML = 1000 ms
    API  = 200 ms
    CSS  = 100 ms

If grouped together, Locust may show an average around 433 ms.
That does not mean the page loaded in 433 ms.

For true page load time, use browser tools.


19. wait_time = between(3, 10)

wait_time adds user "think time" between tasks.

    wait_time = between(3, 10)

Means:
    after a user finishes a task, wait a random 3 to 10 seconds before the
    next task.

Without wait_time, each simulated user sends requests as fast as possible.
That is usually closer to stress testing than realistic user behavior.


20. Task weights

You can weight tasks to model realistic behavior.

Example:
    @task(5) homepage       -> common
    @task(2) browse pages   -> less common
    @task(1) contact page   -> least common

This is better than making every user do every page every cycle.


21. Common performance testing types

Assume expected traffic is:
    200 users

That means 200 users is the normal load you expect the system to handle.
The examples below compare each test type against that expected traffic.

Smoke test:
    A very small test to check that the Locust script and app work.
    This is far below expected traffic.
    Example: 5 users for 1 minute.

Load test:
    Tests expected or normal traffic.
    This should match expected traffic.
    Example: 200 users for 30 minutes.

Stress test:
    Pushes above expected traffic to find where the system slows down,
    fails, or stops scaling.
    Example: expected 200 users -> 500 -> 1000 -> 2000 users.

Spike test:
    Sudden jump in traffic, then usually a sudden drop.
    This jumps far above expected traffic very quickly.
    Example: expected 200 users -> sudden 1000 users -> back to 200 users.

Recovery test:
    Overload the system, then return to expected load and check whether
    response times, errors, and queues return to normal.
    Example: expected 200 users -> overload at 1000 users -> back to
    expected 200 users.

Soak test:
    Runs normal load for a long time to find memory leaks or slow degradation.
    This usually runs at expected traffic for a long time.
    Example: expected 200 users for 6 hours.

Ramp-up test:
    Gradually increases traffic.
    This may ramp from below expected traffic to expected traffic, or beyond it.
    Example: 50 -> 100 -> expected 200 -> 400 users.

Scalability test:
    Checks how the system behaves as traffic increases, often while adding
    more servers or resources.
    Example: expected 200 users on 1 server, 500 users on 2 servers,
    1000 users on 4 servers.

Breakpoint test:
    Keeps increasing traffic until the system fails or performance becomes
    unacceptable.
    This starts at or below expected traffic, then keeps going above it.
    Example: expected 200 -> 400 -> 800 -> 1200 users until response time
    or error rate is too high.

Volume test:
    Tests the system with lots of data, not just lots of users.
    User load may stay at expected traffic, but the database/data size is large.
    Example: expected 200 users with a large database, many products/orders,
    or high event volume.

Capacity test:
    Finds the max traffic the system can handle while still meeting targets.
    This tells you whether expected traffic is safe and how much room is left.
    Example: find the max users while 95% response time stays under 1200 ms.
    Result example: system supports 650 users, so expected 200 users has room.
"""

from locust import HttpUser, between, task


class LearningExampleUser(HttpUser):
    """
    Example Locust user that checks a 1 second SLA.

    Run explicitly with:
        locust -f locust_learnings.py

    Your normal file is still:
        locustfile.py
    """

    wait_time = between(3, 10)

    def get_with_sla(self, path: str, threshold_ms: int = 1000) -> None:
        with self.client.get(path, catch_response=True) as response:
            response_time = response.request_meta["response_time"]

            if response_time > threshold_ms:
                response.failure(
                    f"Exceeded SLA: {response_time:.0f} ms > {threshold_ms} ms"
                )

    @task(5)
    def homepage(self) -> None:
        self.get_with_sla("/")

    @task(2)
    def browse_pages(self) -> None:
        self.get_with_sla("/residential")
        self.get_with_sla("/boat-shed")

    @task(1)
    def contact_us(self) -> None:
        self.get_with_sla("/contact-us")
