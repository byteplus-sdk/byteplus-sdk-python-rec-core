# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: sdk_metrics.proto
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor.FileDescriptor(
  name='sdk_metrics.proto',
  package='metric',
  syntax='proto3',
  serialized_options=b'\n&com.byteplus.rec.core.metrics.protocolZAgithub.com/byteplus-sdk/byteplus-sdk-go-rec-core/metrics/protocol',
  create_key=_descriptor._internal_create_key,
  serialized_pb=b'\n\x11sdk_metrics.proto\x12\x06metric\"\x9b\x01\n\x06Metric\x12\x0c\n\x04name\x18\x01 \x01(\t\x12\x0c\n\x04type\x18\x02 \x01(\t\x12\x11\n\ttimestamp\x18\x03 \x01(\x03\x12\r\n\x05value\x18\x04 \x01(\x01\x12&\n\x04tags\x18\x05 \x03(\x0b\x32\x18.metric.Metric.TagsEntry\x1a+\n\tTagsEntry\x12\x0b\n\x03key\x18\x01 \x01(\t\x12\r\n\x05value\x18\x02 \x01(\t:\x02\x38\x01\"0\n\rMetricMessage\x12\x1f\n\x07metrics\x18\x01 \x03(\x0b\x32\x0e.metric.Metric\"J\n\tMetricLog\x12\n\n\x02id\x18\x01 \x01(\t\x12\r\n\x05level\x18\x02 \x01(\t\x12\x11\n\ttimestamp\x18\x03 \x01(\x03\x12\x0f\n\x07message\x18\x04 \x01(\t\":\n\x10MetricLogMessage\x12&\n\x0bmetric_logs\x18\x01 \x03(\x0b\x32\x11.metric.MetricLogBk\n&com.byteplus.rec.core.metrics.protocolZAgithub.com/byteplus-sdk/byteplus-sdk-go-rec-core/metrics/protocolb\x06proto3'
)




_METRIC_TAGSENTRY = _descriptor.Descriptor(
  name='TagsEntry',
  full_name='metric.Metric.TagsEntry',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='key', full_name='metric.Metric.TagsEntry.key', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='value', full_name='metric.Metric.TagsEntry.value', index=1,
      number=2, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=b'8\001',
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=142,
  serialized_end=185,
)

_METRIC = _descriptor.Descriptor(
  name='Metric',
  full_name='metric.Metric',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='name', full_name='metric.Metric.name', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='type', full_name='metric.Metric.type', index=1,
      number=2, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='timestamp', full_name='metric.Metric.timestamp', index=2,
      number=3, type=3, cpp_type=2, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='value', full_name='metric.Metric.value', index=3,
      number=4, type=1, cpp_type=5, label=1,
      has_default_value=False, default_value=float(0),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='tags', full_name='metric.Metric.tags', index=4,
      number=5, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
  ],
  extensions=[
  ],
  nested_types=[_METRIC_TAGSENTRY, ],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=30,
  serialized_end=185,
)


_METRICMESSAGE = _descriptor.Descriptor(
  name='MetricMessage',
  full_name='metric.MetricMessage',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='metrics', full_name='metric.MetricMessage.metrics', index=0,
      number=1, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=187,
  serialized_end=235,
)


_METRICLOG = _descriptor.Descriptor(
  name='MetricLog',
  full_name='metric.MetricLog',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='id', full_name='metric.MetricLog.id', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='level', full_name='metric.MetricLog.level', index=1,
      number=2, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='timestamp', full_name='metric.MetricLog.timestamp', index=2,
      number=3, type=3, cpp_type=2, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
    _descriptor.FieldDescriptor(
      name='message', full_name='metric.MetricLog.message', index=3,
      number=4, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=237,
  serialized_end=311,
)


_METRICLOGMESSAGE = _descriptor.Descriptor(
  name='MetricLogMessage',
  full_name='metric.MetricLogMessage',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='metric_logs', full_name='metric.MetricLogMessage.metric_logs', index=0,
      number=1, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=313,
  serialized_end=371,
)

_METRIC_TAGSENTRY.containing_type = _METRIC
_METRIC.fields_by_name['tags'].message_type = _METRIC_TAGSENTRY
_METRICMESSAGE.fields_by_name['metrics'].message_type = _METRIC
_METRICLOGMESSAGE.fields_by_name['metric_logs'].message_type = _METRICLOG
DESCRIPTOR.message_types_by_name['Metric'] = _METRIC
DESCRIPTOR.message_types_by_name['MetricMessage'] = _METRICMESSAGE
DESCRIPTOR.message_types_by_name['MetricLog'] = _METRICLOG
DESCRIPTOR.message_types_by_name['MetricLogMessage'] = _METRICLOGMESSAGE
_sym_db.RegisterFileDescriptor(DESCRIPTOR)

Metric = _reflection.GeneratedProtocolMessageType('Metric', (_message.Message,), {

  'TagsEntry' : _reflection.GeneratedProtocolMessageType('TagsEntry', (_message.Message,), {
    'DESCRIPTOR' : _METRIC_TAGSENTRY,
    '__module__' : 'sdk_metrics_pb2'
    # @@protoc_insertion_point(class_scope:metric.Metric.TagsEntry)
    })
  ,
  'DESCRIPTOR' : _METRIC,
  '__module__' : 'sdk_metrics_pb2'
  # @@protoc_insertion_point(class_scope:metric.Metric)
  })
_sym_db.RegisterMessage(Metric)
_sym_db.RegisterMessage(Metric.TagsEntry)

MetricMessage = _reflection.GeneratedProtocolMessageType('MetricMessage', (_message.Message,), {
  'DESCRIPTOR' : _METRICMESSAGE,
  '__module__' : 'sdk_metrics_pb2'
  # @@protoc_insertion_point(class_scope:metric.MetricMessage)
  })
_sym_db.RegisterMessage(MetricMessage)

MetricLog = _reflection.GeneratedProtocolMessageType('MetricLog', (_message.Message,), {
  'DESCRIPTOR' : _METRICLOG,
  '__module__' : 'sdk_metrics_pb2'
  # @@protoc_insertion_point(class_scope:metric.MetricLog)
  })
_sym_db.RegisterMessage(MetricLog)

MetricLogMessage = _reflection.GeneratedProtocolMessageType('MetricLogMessage', (_message.Message,), {
  'DESCRIPTOR' : _METRICLOGMESSAGE,
  '__module__' : 'sdk_metrics_pb2'
  # @@protoc_insertion_point(class_scope:metric.MetricLogMessage)
  })
_sym_db.RegisterMessage(MetricLogMessage)


DESCRIPTOR._options = None
_METRIC_TAGSENTRY._options = None
# @@protoc_insertion_point(module_scope)
