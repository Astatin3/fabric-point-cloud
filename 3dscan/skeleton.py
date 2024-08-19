import math

import cv2
import numpy as np
import ktb
import mediapipe as mp
from collections import deque

from scipy.spatial import ConvexHull

running = True

# Initialize MediaPipe Pose
mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils
pose = mp_pose.Pose(static_image_mode=False, min_detection_confidence=0.5, min_tracking_confidence=0.5)


def get_color():
    return k.get_frame(ktb.COLOR)

def get_depth_map():
    return k.get_frame(ktb.DEPTH)

def normalize_depth_map(depth_map):
    min_val, max_val, _, _ = cv2.minMaxLoc(depth_map)
    normalized = cv2.convertScaleAbs(depth_map, alpha=255.0/(max_val-min_val), beta=-min_val * 255.0/(max_val-min_val))
    return normalized

def calc_mask(depth_map, rgb_image):


    # Process the image and get pose landmarks
    results = pose.process(rgb_image)

    if results.pose_landmarks:
        # Create person mask
        print("Found person!")
        # cv2.imshow("Test", generate_distance_map(results.pose_landmarks, rgb_image.shape))
        return create_person_mask(depth_map, results.pose_landmarks, rgb_image.shape)
    else:
        return np.zeros(rgb_image.shape[:2], dtype=np.uint8)

def clamp(x, min_value, max_value):
    return max(min(max_value, x), min_value)


def get_blurred_point_value(image, point, kernel_size=(5, 5), sigma=1.0):
    # Ensure odd kernel size
    kernel_size = tuple(k + 1 if k % 2 == 0 else k for k in kernel_size)

    # Calculate the half size of the kernel
    half_width = kernel_size[0] // 2
    half_height = kernel_size[1] // 2

    # Extract the region of interest (ROI) around the point
    x, y = point
    roi = image[max(0, y - half_height):min(image.shape[0], y + half_height + 1),
          max(0, x - half_width):min(image.shape[1], x + half_width + 1)]

    # Apply Gaussian blur to the ROI
    blurred_roi = cv2.GaussianBlur(roi, kernel_size, sigma)

    # Get the value at the center of the blurred ROI
    center_y, center_x = blurred_roi.shape[0] // 2, blurred_roi.shape[1] // 2
    blurred_value = blurred_roi[center_y, center_x]

    return blurred_value

def gradient_line(mask, x1, y1, x2, y2, depth_1, depth_2, circle_dist=15, step_size=5):
    circle_dist = 10

    cv2.circle(mask, (x1, y1), circle_dist * 2, int(depth_1), thickness=-1)
    # cv2.circle(mask, (x2, y2), circle_dist * 2, int(depth_2), thickness=-1)

    # print(x1, y1, x2, y2)

    distance = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
    step_count = int(distance / step_size)
    print(step_count)

    if step_count <= 0:
        return mask

    distance_x = (x2 - x1) / step_count
    distance_y = (y2 - y1) / step_count

    if distance_x == 0 or distance_y == 0:
        return mask

    color_step_distance = (depth_2 - depth_1) / step_size

    for i in range(int(step_count)):
        x = x1 + i * distance_x
        y = y1 + i * distance_y
        color = depth_1 + color_step_distance * i

        tmp_mask = mask.copy()
        cv2.circle(tmp_mask, (int(x), int(y)), circle_dist * 2, color, thickness=-1)
        mask = cv2.addWeighted(mask, 0.5, tmp_mask, 0.5, 1.0)
        del tmp_mask
    return mask

SKELETON_DEPTH_TO_KINECT = 4096

def generate_distance_map(depth_map, pose_landmarks, image_shape, circle_dist=15, step_size=10):
    # Create a black background
    # mask = np.zeros(image_shape[:2], dtype=np.uint8)
    mask = depth_map

    connections = []

    # Draw pose landmarks and connections
    for connection in mp_pose.POSE_CONNECTIONS:
        start_point = pose_landmarks.landmark[connection[0]]
        end_point = pose_landmarks.landmark[connection[1]]

        x1, y1 = int(clamp(start_point.x, 0, .999) * image_shape[1]), int(clamp(start_point.y, 0, .999) * image_shape[0])
        x2, y2 = int(clamp(end_point.x, 0, .999) * image_shape[1]), int(clamp(end_point.y, 0, .999) * image_shape[0])

        # print(start_point.z, end_point.z)

        # depth_1 = start_point.z * SKELETON_DEPTH_TO_KINECT
        # depth_2 = end_point.z * SKELETON_DEPTH_TO_KINECT

        depth_1 = get_blurred_point_value(depth_map, (x1, y1), kernel_size=(15, 15))
        depth_2 = get_blurred_point_value(depth_map, (x2, y2), kernel_size=(15, 15))

        connections.append({
            "x1": x1, "y1": y1, "x2":x2, "y2":y2, "depth_1":depth_1, "depth_2":depth_2
        })

    n = len(connections)  # Get the length of the array
    if n > 1:
        for i in range(1, n):  # Iterate over the array starting from the second element
            key = connections[i]  # Store the current element as the key to be inserted in the right position
            j = i - 1
            while j >= 0 and key["depth_1"] > connections[j]["depth_1"]:  # Move elements greater than key one position ahead
                connections[j + 1] = connections[j]  # Shift elements to the right
                j -= 1
            connections[j + 1] = key  # Insert the key in the correct position


    for c in connections:
        mask = gradient_line(mask, c["x1"], c["y1"], c["x2"], c["y2"], c["depth_1"], c["depth_2"], circle_dist)


    return mask


def create_person_mask(depth_map, pose_landmarks, image_shape, distance_threshold=25):
    # Create an empty mask
    mask = np.zeros(image_shape[:2], dtype=np.uint8)
    
    # Draw pose landmarks and connections
    for connection in mp_pose.POSE_CONNECTIONS:
        start_point = pose_landmarks.landmark[connection[0]]
        end_point = pose_landmarks.landmark[connection[1]]
        
        x1, y1 = int(start_point.x * image_shape[1]), int(start_point.y * image_shape[0])
        x2, y2 = int(end_point.x * image_shape[1]), int(end_point.y * image_shape[0])
        
        cv2.line(mask, (x1, y1), (x2, y2), 1, thickness=distance_threshold*2)
    
    # Dilate the mask to include nearby pixels
    kernel = np.ones((distance_threshold, distance_threshold), np.uint8)
    mask = cv2.dilate(mask, kernel, iterations=1)

    mask_2 = generate_distance_map(depth_map, pose_landmarks, image_shape, distance_threshold)
    cv2.imshow("mask_2", (mask_2 / 2048)*mask)
    
    return mask


# while running:
#     # vis.update_geometry(reconstruction)
#     # print("E")
#     if cv2.waitKey(1) & 0xFF == ord('q'):
#         running = False
#     running = vis.poll_events()
#     vis.update_renderer()

