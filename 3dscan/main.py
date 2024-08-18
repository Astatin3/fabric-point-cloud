from threading import  Thread
import cv2
import numpy as np
import ktb
import open3d as o3d
import math

import skeleton

# vis = o3d.visualization.Visualizer()
# vis.create_window()

# reconstruction = o3d.geometry.PointCloud()
# reconstruction.points = o3d.utility.Vector3dVector(np.random.rand(2, 3))

# vis.add_geometry(reconstruction)

running = True

def run_loop():
    k = ktb.Kinect()

    import socket
    clientsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    clientsocket.connect(('localhost', 65000))
    print("Connected!")

    while running:
        points, colors = k.get_ptcld(colorized=True, scale=10)
        
        mask = skeleton.calc_mask(k.get_frame(ktb.DEPTH), cv2.cvtColor(k.get_frame(ktb.COLOR), cv2.COLOR_BGR2RGB))
        cv2.imshow('Person Mask', mask * 255)
        cv2.waitKey(1)
        # mask = mask.flatten().reshape((-1, 1))
        mask = mask.flatten().astype(bool)
        
        points = points.reshape((-1, 3))
        points = points[mask]
        if points.shape[0] == 0:
            continue
        skip_count = math.ceil(points.shape[0]/2000)
        points = points[0::skip_count]
        points = np.trunc(points).astype(int)
        
        colors = colors.reshape((-1, 3))
        colors = colors[mask]
        colors = colors[0::skip_count]
        colors *= 256
        colors = np.trunc(colors).astype(int)
        
        # reconstruction.points = o3d.utility.Vector3dVector(points)
        # reconstruction.colors = o3d.utility.Vector3dVector(colors)
        # vis.update_geometry(reconstruction)
        
        for i in range(len(points)):
            point = points[i]
            color = colors[i]
            clientsocket.send(f'{i},{point[0]},{point[1]},{point[2]},{color[0]},{color[1]},{color[2]}\n'.encode())
 
            # print(f'{i},{(point[0])},{(point[1])},{(point[2])},{color[0]},{color[1]},{color[2]}')
        print("Update!")
        
t = Thread(target=run_loop)
t.start()

# while running:
#     running = vis.poll_events()
#     vis.update_renderer()

t.join()
skeleton.pose.close()