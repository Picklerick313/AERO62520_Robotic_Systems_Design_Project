#! /usr/bin/env python3

import sys
import time
import math
import rclpy
import numpy as np
from enum import Enum

from rclpy.node import Node
from rclpy.action import ActionClient
from rclpy.qos import QoSProfile, QoSDurabilityPolicy, QoSHistoryPolicy, QoSReliabilityPolicy

from action_msgs.msg import GoalStatus
from geometry_msgs.msg import PoseStamped
from nav2_msgs.action import NavigateToPose
from nav_msgs.msg import OccupancyGrid, Odometry
from std_msgs.msg import String 

# --- HARDWARE TUNING ---
OCC_THRESHOLD = 25   
MIN_FRONTIER_SIZE = 8 

class OccupancyGrid2d():
    def __init__(self, map):
        self.map = map
    def getCost(self, mx, my):
        return self.map.data[my * self.map.info.width + mx]
    def getSizeX(self): return self.map.info.width
    def getSizeY(self): return self.map.info.height
    def mapToWorld(self, mx, my):
        wx = self.map.info.origin.position.x + (mx + 0.5) * self.map.info.resolution
        wy = self.map.info.origin.position.y + (my + 0.5) * self.map.info.resolution
        return (wx, wy)
    def worldToMap(self, wx, wy):
        mx = int((wx - self.map.info.origin.position.x) / self.map.info.resolution)
        my = int((wy - self.map.info.origin.position.y) / self.map.info.resolution)
        return (mx, my)

class FrontierPoint():
    def __init__(self, x, y):
        self.classification = 0
        self.mapX, self.mapY = x, y

class PointClassification(Enum):
    MapOpen = 1
    MapClosed = 2
    FrontierOpen = 4
    FrontierClosed = 8

def getNeighbors(point, costmap, cache):
    neighbors = []
    for x in range(point.mapX - 1, point.mapX + 2):
        for y in range(point.mapY - 1, point.mapY + 2):
            if (0 < x < costmap.getSizeX() and 0 < y < costmap.getSizeY()):
                if (x, y) not in cache: cache[(x, y)] = FrontierPoint(x, y)
                neighbors.append(cache[(x, y)])
    return neighbors

def isFrontierPoint(point, costmap, cache):
    if costmap.getCost(point.mapX, point.mapY) != -1: return False
    hasFree = False
    for n in getNeighbors(point, costmap, cache):
        cost = costmap.getCost(n.mapX, n.mapY)
        if cost > OCC_THRESHOLD: return False
        if cost == 0: hasFree = True
    return hasFree

def getFrontiers(pose, costmap):
    cache = {}
    mx, my = costmap.worldToMap(pose.position.x, pose.position.y)
    start = FrontierPoint(mx, my)
    start.classification = PointClassification.MapOpen.value
    queue, frontiers = [start], []

    while queue:
        p = queue.pop(0)
        if p.classification & PointClassification.MapClosed.value: continue
        if isFrontierPoint(p, costmap, cache):
            p.classification |= PointClassification.FrontierOpen.value
            f_queue, f_group = [p], []
            while f_queue:
                q = f_queue.pop(0)
                if q.classification & (PointClassification.MapClosed.value | PointClassification.FrontierClosed.value): continue
                if isFrontierPoint(q, costmap, cache):
                    f_group.append(costmap.mapToWorld(q.mapX, q.mapY))
                    for w in getNeighbors(q, costmap, cache):
                        if not (w.classification & (PointClassification.FrontierOpen.value | PointClassification.FrontierClosed.value | PointClassification.MapClosed.value)):
                            w.classification |= PointClassification.FrontierOpen.value
                            f_queue.append(w)
                q.classification |= PointClassification.FrontierClosed.value
            if len(f_group) > MIN_FRONTIER_SIZE:
                arr = np.array(f_group)
                frontiers.append({'pos': (np.mean(arr[:, 0]), np.mean(arr[:, 1])), 'size': len(f_group)})
        for v in getNeighbors(p, costmap, cache):
            if not (v.classification & (PointClassification.MapOpen.value | PointClassification.MapClosed.value)):
                v.classification |= PointClassification.MapOpen.value
                queue.append(v)
        p.classification |= PointClassification.MapClosed.value
    return frontiers

class UniversalLeoExplorer(Node):
    def __init__(self):
        super().__init__('universal_leo_explorer')
        self.currentPose, self.costmap, self.last_goal = None, None, None
        self.initial_pose_received = False
        self.object_detected = False

        qos_odom = QoSProfile(reliability=QoSReliabilityPolicy.BEST_EFFORT, history=QoSHistoryPolicy.KEEP_LAST, depth=5)
        qos_map = QoSProfile(durability=QoSDurabilityPolicy.TRANSIENT_LOCAL, reliability=QoSReliabilityPolicy.RELIABLE, history=QoSHistoryPolicy.KEEP_LAST, depth=1)

        self.action_client = ActionClient(self, NavigateToPose, 'navigate_to_pose')
        # UPDATED TO USE MERGED_ODOM
        self.create_subscription(Odometry, '/merged_odom', self.pose_cb, qos_odom)
        self.create_subscription(OccupancyGrid, '/map', self.map_cb, qos_map)
        self.create_subscription(String, '/color_detected', self.color_cb, 10)

        self.get_logger().info('Leo Rover Physical Explorer Online...')

    def pose_cb(self, msg):
        self.currentPose = msg.pose.pose
        self.initial_pose_received = True

    def map_cb(self, msg):
        self.costmap = OccupancyGrid2d(msg)

    def color_cb(self, msg):
        if not self.object_detected:
            self.get_logger().warn('Object detected! Stopping exploration.')
            self.object_detected = True

    def start_exploration_step(self):
        if self.currentPose is None or self.costmap is None: return True
        frontiers = getFrontiers(self.currentPose, self.costmap)
        if not frontiers: 
            self.get_logger().info("Mapping complete! No more frontiers.")
            return False

        best_f, min_score = None, float('inf')
        for f in frontiers:
            pos = f['pos']
            dist = math.sqrt((pos[0]-self.currentPose.position.x)**2 + (pos[1]-self.currentPose.position.y)**2)
            score = dist - (f['size'] * 0.015) 
            if self.last_goal:
                score += (math.sqrt((pos[0]-self.last_goal[0])**2 + (pos[1]-self.last_goal[1])**2) * 0.25)
            if score < min_score:
                min_score, best_f = score, pos

        self.last_goal = best_f
        self.navigate_to(best_f)
        return True

    def navigate_to(self, coord):
        goal_msg = NavigateToPose.Goal()
        goal_msg.pose.header.frame_id = 'map'
        goal_msg.pose.header.stamp = self.get_clock().now().to_msg()
        goal_msg.pose.pose.position.x, goal_msg.pose.pose.position.y, goal_msg.pose.pose.orientation.w = coord[0], coord[1], 1.0

        self.get_logger().info(f'Heading to Frontier: x={coord[0]:.2f}, y={coord[1]:.2f}')
        self.action_client.wait_for_server()
        send_goal_future = self.action_client.send_goal_async(goal_msg)
        rclpy.spin_until_future_complete(self, send_goal_future)
        
        goal_handle = send_goal_future.result()
        if not goal_handle.accepted: return

        result_future = goal_handle.get_result_async()
        while rclpy.ok() and not result_future.done():
            rclpy.spin_once(self, timeout_sec=0.1)
            if self.object_detected:
                goal_handle.cancel_goal_async()
                return

def main(args=None):
    rclpy.init(args=args)
    node = UniversalLeoExplorer()
    
    try:
        while rclpy.ok() and (not node.initial_pose_received or node.costmap is None):
            rclpy.spin_once(node, timeout_sec=0.1)

        exploring = True
        while rclpy.ok() and exploring:
            if node.object_detected:
                exploring = False
            else:
                exploring = node.start_exploration_step()

    except KeyboardInterrupt:
        pass

if __name__ == '__main__':
    main()