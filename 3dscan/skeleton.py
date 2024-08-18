import cv2
import numpy as np
import ktb
import mediapipe as mp

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
        return create_person_mask(depth_map, results.pose_landmarks, rgb_image.shape)
    else:
        return np.zeros(rgb_image.shape[:2], dtype=np.uint8)


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
    
    # Get depth values for the pose landmarks
    landmark_depths = []
    for landmark in pose_landmarks.landmark:
        x, y = int(landmark.x * image_shape[1]), int(landmark.y * image_shape[0])
        if 0 <= x < image_shape[1] and 0 <= y < image_shape[0]:
            landmark_depths.append(depth_map[y, x])
    
    # Calculate depth range
    min_depth = np.percentile(landmark_depths, 0)  # 5th percentile to avoid outliers
    max_depth = np.percentile(landmark_depths, 100)  # 95th percentile to avoid outliers
    
    # Refine the mask using depth information
    depth_mask = (depth_map >= min_depth) & (depth_map <= max_depth)
    
    # Combine the initial mask with the depth mask
    final_mask = mask & depth_mask
    
    return final_mask


# while running:
#     # vis.update_geometry(reconstruction)
#     # print("E")
#     if cv2.waitKey(1) & 0xFF == ord('q'):
#         running = False
#     running = vis.poll_events()
#     vis.update_renderer()

