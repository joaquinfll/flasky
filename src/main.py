# flask_example.py
import sys, flask, requests, datetime, logging, json_logging
from opentelemetry.trace.span import SpanContext

from flask import Flask, request
from prometheus_flask_exporter import PrometheusMetrics

from opentelemetry import trace
from opentelemetry.exporter.zipkin.json import ZipkinExporter
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor

from decouple import config

MICROSERVICE_NAME = config('MICROSERVICE_NAME', default="flasky")
ENVIRONMENT_NAME = config('ENVIRONMENT_NAME', default="development")

trace.set_tracer_provider(
    TracerProvider(
        resource=Resource.create({SERVICE_NAME: MICROSERVICE_NAME})
    )
)
tracer = trace.get_tracer(__name__)

zipkin_exporter = ZipkinExporter(
    # version=Protocol.V2
    # optional:
    # endpoint="http://localhost:9411/api/v2/spans",
    # local_node_ipv4="192.168.0.1",
    # local_node_ipv6="2001:db8::c001",
    # local_node_port=31313,
    # max_tag_value_length=256
    # timeout=5 (in seconds)
)

span_processor = BatchSpanProcessor(zipkin_exporter)
trace.get_tracer_provider().add_span_processor(span_processor)

app = flask.Flask(__name__)

# static information as metric
metrics = PrometheusMetrics(app)
metrics.info('app_info', 'Application info', version='1.0.3')

FlaskInstrumentor().instrument_app(app)
RequestsInstrumentor().instrument()
json_logging.init_flask(enable_json=True)
json_logging.init_request_instrument(app)
logger = logging.getLogger("logger")
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler(sys.stdout))


@app.route("/")
def start():
     with tracer.start_as_current_span("main"):
        span = trace.get_current_span()
        logger.info(msg="Main action", extra={'props': {'trace_id': span.context.trace_id, 'span_id': span.context.span_id}})
     return "What are you doing here?"

@app.route("/hello")
def hello():
    with tracer.start_as_current_span("hello"):
        span = trace.get_current_span()
        logger.info(msg="Hello action", extra={'props': {'trace_id': span.context.trace_id, 'span_id': span.context.span_id}})
        message = "hello " + random_color()
    return message

@app.route("/bye")
def bye():
    with tracer.start_as_current_span("bye"):
        span = trace.get_current_span()
        logger.info(msg="Bye action", extra={'props': {'trace_id': span.context.trace_id, 'span_id': span.context.span_id}})
        message = "bye"
    return message

def random_color():
    with tracer.start_as_current_span("random_color"):
        span = trace.get_current_span()
        logger.info(msg="Random_color action", extra={'props': {'trace_id': span.context.trace_id, 'span_id': span.context.span_id}})
        color = "blue"
    return color


app.run(debug=True, host="0.0.0.0", port=8080)