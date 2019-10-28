import pytest
import grpc
import datetime
import numpy
import logging

from proto.generated import detection_handler_pb2

# to enable log statements on CLI run with python -m pytest samples/stdout_detection_handler-test.py --log-cli-level=DEBUG

def test_create_handle_detection_request():
    # TODO this same data could be made available using a fixture to test the server implementation
    frame_array1 = [5, 2, 3]
    # not sure why the frame from opencv is nested this way
    frame = numpy.array([[frame_array1, [8.4, 7.9, 5.2], [59,  64,  64]]])
    detection_output = {'detection_scores': [0.54], 'detection_classes':[8],
                        'detection_boxes':numpy.array([[0.36190858, 0.11737314, 0.94603133, 0.3205647],
                                            [0.345639  , 0.69829893, 0.38075703, 0.7310691 ]])}
    detection_boxes = detection_handler_pb2.float_array(numbers=detection_output['detection_boxes'].ravel(),
                                                        shape=detection_output['detection_boxes'].shape)
    string_map={'color':'blue', 'music':'classical'}
    float_map={'weight':56.9, 'height':85.4}
    # logging.debug(f"detection_boxes: {detection_boxes}")
    msg = detection_handler_pb2.handle_detection_request(
                start_timestamp = datetime.datetime.now().timestamp(),
                detection_scores = detection_output['detection_scores'],
                detection_classes = detection_output['detection_classes'],
                detection_boxes = detection_boxes,
                instance_name = "testing",
                frame = detection_handler_pb2.float_array(numbers=frame.ravel(), shape=frame.shape),
                frame_count = 1619,
                source = "steam",
                string_map=string_map,
                float_map=float_map)
    assert len(msg.frame.numbers) == 9
    assert msg.frame.shape == [1, 3, 3]

    assert len(msg.detection_boxes.numbers) == 8
    assert msg.detection_boxes.shape == [2, 4]
    ndarray = numpy.array(msg.detection_boxes.numbers).reshape(msg.detection_boxes.shape)
    logging.debug(ndarray)

    assert msg.string_map == string_map
    assert msg.float_map == string_map



def test_create_handle_detection_response():
    response = detection_handler_pb2.handle_detection_response(status=True)
