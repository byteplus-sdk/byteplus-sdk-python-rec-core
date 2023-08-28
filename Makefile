gen_sdk_metrics:
	protoc --python_out=byteplus_rec_core/metrics/protocol -I=byteplus_rec_core/metrics/protocol byteplus_rec_sdk_metrics.proto