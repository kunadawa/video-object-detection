# imports
import logging
import os
import argparse
import sys
import json
import cv2
import object_detection.object_detection as obj_detect
import numpy as np
import tempfile
import object_detection.utils.visualization_utils as vis_utils
import object_detection.utils.label_map_util as label_utils

CUT_OFF_SCORE = 90
SAMPLE_RATE = 5

def determine_samplerate(args):
    try:
        """ check for sample rate in args, if absent return default """
        return args.samplerate
    except AttributeError:
        return SAMPLE_RATE

def determine_source(args, video_reader):
    """
    parameters:
        args: a namespace object from argparse.ArgumentParser.parse_args().
            The source attribute determine which source the video is to be read load_frozen_model_into_memory and can be any of the following values
                '-' (hyphen): standard input
                digit: webcam
                URL: file path
        video_reader: the class/function to use to read video from file or camera, useful for mocking

        returns a file object
    """
    if args.source == '-':
        return video_reader(sys.stdin)
    elif args.source.isnumeric():
        return video_reader(args.source)
    elif os.path.exists(args.source):
        return video_reader(args.source)

def detect_video_stream(args):
    """ detect objects in video stream """
    # __dict__ trick from https://stackoverflow.com/a/3768975/315385
    if args.dryrun:
        sys.stdout.writelines(json.dumps(args.__dict__))
        return
    # generate dict from labels
    category_index = label_utils.create_category_index_from_labelmap(args.path_to_label_map, use_display_name=True)
    # logging.debug(f"category_index: {category_index}")
    # TODO validate args
    detection_graph = obj_detect.load_frozen_model_into_memory(args.path_to_frozen_graph)
    # determine sample rate
    sample_rate = determine_samplerate(args.samplerate)
    # loop over frames in video
    # adapted from https://github.com/juandes/pikachu-detection/blob/master/detection_video.py
    cap = determine_source(args, cv2.VideoCapture)
    # TODO accept a switch that will change from video output to text output
    # discovered there via ffprobe - https://unix.stackexchange.com/a/323094/198026
    output_video_file_path = tempfile.NamedTemporaryFile(suffix='.avi', delete=False).name
    # output_video_file_path = "/tmp/testing_video_detection.avi"
    logging.info(f'writing output video to {output_video_file_path}')
    video_out = cv2.VideoWriter(output_video_file_path,
                                fourcc=cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'),
                                apiPreference=cv2.CAP_ANY,
                                fps=10,
                                frameSize=(int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)), int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))))
    frame_count = 0
    while (cap.isOpened()):
        ret, frame = cap.read()
        # only consider frames that are a multiple of the sample rate
        if frame_count % sample_rate == 0:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img_to_array = np.expand_dims(frame, axis=0)
            # image = object_detection.load_image_into_numpy_array(img_to_array)
            # run inference
            output_dict = obj_detect.run_inference_for_single_image(img_to_array, detection_graph)
            # TODO filter for classes, cut off score
            # TODO convert output dict to JSON - there's an error writing nd_arrays into json
            # TODO implement with switch from args - write output dict to stdout
            # sys.stdout.write(str(output_dict))
            # OR write image to video out
            # credit - https://github.com/juandes/pikachu-detection/blob/master/detection_video.py
            vis_utils.visualize_boxes_and_labels_on_image_array(
                img_to_array,
                output_dict['detection_boxes'],
                output_dict['detection_classes'],
                output_dict['detection_scores'],
                category_index,
                instance_masks=output_dict.get('detection_masks'),
                use_normalized_coordinates=True,
                line_thickness=10)
            cv2.imshow('frame', img_to_array)
            output_rgb = cv2.cvtColor(img_to_array, cv2.COLOR_RGB2BGR)
            out.write(output_rgb)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
            frame_count += 1

    video_out.release()
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    logging.getLogger().setLevel(logging.DEBUG)
    parser = argparse.ArgumentParser(description="detect objects in video")
    # credit for adding required arg - https://stackoverflow.com/a/24181138/315385
    parser.add_argument("source", help="- for standard input, path to file or a numeral that represents the webcam device number")
    parser.add_argument("path_to_frozen_graph", help="path to frozen model graph")
    parser.add_argument("path_to_label_map", help="path to label map")
    parser.add_argument("--cutoff", help="cut off detection score (%%)")
    parser.add_argument("--dryrun", help="echo a params as json object, don't process anything", action="store_true")
    parser.add_argument("--classes",
            help="space separated list of object classes to detect as specified in label mapping")
    parser.add_argument("--samplerate", help="how often to retrieve video frames for object detection")
    args = parser.parse_args()
    detect_video_stream(args)
