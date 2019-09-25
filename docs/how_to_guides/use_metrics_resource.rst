.. _use_metrics_resource:


How to use metrics resource
===========================

All Tamarco meters implement the Flyweight pattern, this means that no matter where you instantiate the meter if two
or more meters have the same characteristics they are going to be the same object. You don't need to be careful about
using the same object in multiple places.



Counter
-------

A counter is a cumulative metric that represents a single numerical value that only goes up. The counter is reseated
when the server restart. A counter can be used to count requests served, events, tasks completed, errors occurred, etc.

.. code-block:: python

    cats_counter = Counter('cats', 'animals')
    meows_counter = Counter('meows', 'sounds')
    jumps_counter = Counter('jumps', 'actions')

    class Cat:

        def __init__(self):
            cats_counter.inc()

        # It can work as a decorator, every time a function is called, the counter is increased in one.
        @meows_counter
        def meow(self):
            print('meow')

        # Similarly it can be used as a decorator of coroutines.
        @jumps_counter
        async def jump(self):
            print("jump")

Gauge
-----

A gauge is a metric that represents a single numerical value. Unlike the counter, it can go down. Gauges are typically
used for measured values like temperatures, current memory usage, coroutines, CPU usage, etc. You need to take into
account that this kind of data only save the last value when it is reported.

It is used similarly to the counter, a simple example:

.. code-block:: python

    ws_connections_metric = Gauge("websocket_connections", "connections")

    class WebSocketServer:

        @ws_connections_metric
        def on_open(self):
            ...

        def on_close(self):
            ws_connections_metric.dec()
            ...


Summary
-------

A summary samples observations over sliding windows of time and provides instantaneous insight into their distributions,
frequencies, and sums). They are typically used to get feedback about quantities where the distribution of the data is
important, as the processing times.

The default quantiles are: [0.5, 0.75, 0.9, 0.95, 0.99].

Timer
-----

Gauge and Summary can be used as timers. The timer admits to be used as a context manager and as a decorator:

.. code-block:: python

    request_processing_time = Summary("http_requests_processing_time", "time")

    @request_processing_time.timeit()
    def http_handler(request):
        ...


.. code-block:: python

    import time

    my_task_processing_time_gauge = Gauge("my_task_processing_time", "time")

    with my_task_processing_time_gauge.timeit()
         my_task()



Labels
------

The metrics admit labels to attach additional information in a counter. For example, the status code of an HTTP response
can be used as a label to monitoring the amount of failed requests.

A meter with labels:

.. code-block:: python

    http_requests_ok = Counter('http_requests', 'requests', labels={'status_code': 200})

    def http_request_ping(request):
        http_requests_ok.inc()
        ...

To add a label to an already existent meter:
