gen_sdk_metrics:
	protoc --python_out=byteplus_rec_core/metrics/protocol -I=byteplus_rec_core/metrics/protocol sdk_metrics.proto