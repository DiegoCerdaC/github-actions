from opentelemetry import trace
from opentelemetry.exporter.cloud_trace import CloudTraceSpanExporter
from opentelemetry.sdk.trace import TracerProvider, SpanProcessor
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource
from opentelemetry.propagate import set_global_textmap
from opentelemetry.trace import Status, StatusCode
from opentelemetry.propagators.cloud_trace_propagator import (
    CloudTraceFormatPropagator,
)

import os


env = os.getenv("ENV", "dev")

global_attributes = {"service.name": f"orbit-{env}"}


class GlobalAttributeSpanProcessor(SpanProcessor):
    def __init__(self, attributes: dict):
        self.attributes = attributes

    def on_start(self, span, parent_context):
        for key, value in self.attributes.items():
            span.set_attribute(key, value)

    def on_end(self, span):
        pass


def init_tracing():
    set_global_textmap(CloudTraceFormatPropagator())

    tracer_provider = TracerProvider(resource=Resource({"service.name": "orbit"}))

    cloud_trace_exporter = CloudTraceSpanExporter()
    tracer_provider.add_span_processor(BatchSpanProcessor(cloud_trace_exporter))
    tracer_provider.add_span_processor(GlobalAttributeSpanProcessor(global_attributes))
    trace.set_tracer_provider(tracer_provider)


init_tracing()

tracer = trace.get_tracer("orbit")


def set_attributes(attrs: dict):
    try:
        current_span = trace.get_current_span()
        if current_span:
            for key, value in attrs.items():
                current_span.set_attribute(key, value)
    except Exception as e:
        print(f"Error setting span attribute: {e}")


def set_status_ok(attrs: dict = {}):
    try:
        current_span = trace.get_current_span()
        if current_span:
            current_span.set_status(Status(StatusCode.OK))
            for key, value in attrs.items():
                current_span.set_attribute(key, value)
        else:
            print("No current span found")
    except Exception as e:
        print(f"Error setting span status: {e}")


def set_status_error(error: Exception, attrs: dict = {}):
    try:
        current_span = trace.get_current_span()
        if current_span:
            print(current_span)
            current_span.set_attribute("error", str(error))
            current_span.set_status(Status(StatusCode.ERROR))
            for key, value in attrs.items():
                current_span.set_attribute(key, value)
            if isinstance(error, Exception):
                current_span.record_exception(error)

                current_span.set_attribute("error.type", type(error).__name__)
                current_span.set_attribute("error.message", str(error))
        else:
            print("No current span found")
    except Exception as e:
        print(f"Error setting span status: {e}")
