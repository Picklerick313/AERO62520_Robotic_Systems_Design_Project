import rclpy
from rclpy.node import Node

from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Image
from vision_msgs.msg import Detection2DArray

from cv_bridge import CvBridge
import cv2

import numpy as np

import yaml


class ColorBlobDebugImage(Node):
    """
    ROS2 节点：订阅彩色图像 + 2D blob 检测结果，在图像上叠加可视化信息并发布 debug image。

    输入:
      - image_topic (sensor_msgs/Image): 默认 /camera/camera/color/image_raw
      - blobs_topic (vision_msgs/Detection2DArray): 默认 /color_blobs

    输出:
      - output_topic (sensor_msgs/Image): 默认 /color_blobs/debug_image
    """

    def __init__(self):
        super().__init__("color_blob_debug_image")

        self.declare_parameter("image_topic", "/camera/camera/color/image_raw")
        self.declare_parameter("blobs_topic", "/color_blobs")
        self.declare_parameter("output_topic", "/color_blobs/debug_image")
        self.declare_parameter("draw_center", True)
        self.declare_parameter("thickness", 2)
        self.declare_parameter("font_scale", 0.7)

        self._image_topic = self.get_parameter("image_topic").value
        self._blobs_topic = self.get_parameter("blobs_topic").value
        self._output_topic = self.get_parameter("output_topic").value
        self._draw_center = bool(self.get_parameter("draw_center").value)
        self._thickness = int(self.get_parameter("thickness").value)
        self._font_scale = float(self.get_parameter("font_scale").value)

        # YAML HSV ranges（与 color_blob_detector 保持一致）
        self.declare_parameter("yaml_path", "/home/student24/robotproject/tools/color_ranges.yaml")
        self._yaml_path = self.get_parameter("yaml_path").value
        self._hsv_ranges = self._load_ranges_from_yaml(self._yaml_path)
        self.get_logger().info(f"Loaded HSV ranges from YAML: {list(self._hsv_ranges.keys())}")

        self._bridge = CvBridge()
        self._last_image = None
        self._last_header = None

        # 图像：用 sensor qos
        self._img_sub = self.create_subscription(
            Image,
            self._image_topic,
            self._image_cb,
            qos_profile_sensor_data,
        )

        # 检测：普通 qos 就行
        self._det_sub = self.create_subscription(
            Detection2DArray,
            self._blobs_topic,
            self._det_cb,
            10,
        )

        # debug image 输出
        self._pub = self.create_publisher(
            Image,
            self._output_topic,
            10,
        )

        self.get_logger().info(
            f"color_blob_debug_image started.\n"
            f"  image_topic:  {self._image_topic}\n"
            f"  blobs_topic:  {self._blobs_topic}\n"
            f"  output_topic: {self._output_topic}\n"
            f"  yaml_path: {self._yaml_path}"
        )

    # ----------------------------
    def _image_cb(self, msg: Image):
        try:
            bgr = self._bridge.imgmsg_to_cv2(msg, desired_encoding="bgr8")
        except Exception as e:
            self.get_logger().error(f"Failed to convert image: {e}")
            return

        self._last_image = bgr
        self._last_header = msg.header

    # ----------------------------
    def _det_cb(self, msg: Detection2DArray):
        # 没有最新图像就先不画
        if self._last_image is None or self._last_header is None:
            return

        # 尽量只画同一帧（或接近同一帧）；这里做个“宽松处理”
        img = self._last_image.copy()

        for det in msg.detections:
            # bbox
            cx = float(det.bbox.center.position.x)
            cy = float(det.bbox.center.position.y)
            w = float(det.bbox.size_x)
            h = float(det.bbox.size_y)

            x1 = int(round(cx - w * 0.5))
            y1 = int(round(cy - h * 0.5))
            x2 = int(round(cx + w * 0.5))
            y2 = int(round(cy + h * 0.5))

            # clamp
            H, W = img.shape[:2]
            x1 = max(0, min(W - 1, x1))
            y1 = max(0, min(H - 1, y1))
            x2 = max(0, min(W - 1, x2))
            y2 = max(0, min(H - 1, y2))

            # label/score（Jazzy：在 hypothesis 内）
            label = "blob:unknown"
            score = 0.0
            if det.results:
                hyp = det.results[0]
                label = hyp.hypothesis.class_id
                score = float(hyp.hypothesis.score)

            color_name = label.split(":", 1)[1] if ":" in label else label

            # 给不同颜色一个可区分的框色（BGR）
            box_color = self._bgr_for_color(color_name)

            cv2.rectangle(img, (x1, y1), (x2, y2), box_color, self._thickness)

            ty = y1 - 8 if y1 - 8 > 20 else y1 + 25

            # ----------------------------
            # Debug: 在 bbox ROI 内用 HSV 再提取一次轮廓，画旋转框和中轴线
            # ----------------------------
            roi = self._last_image[y1:y2, x1:x2]
            if roi.size > 0:
                hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
                mask_all = None

                for (lower, upper) in self._hsv_ranges_for_color(color_name):
                    lower = np.array(lower, dtype=np.uint8)
                    upper = np.array(upper, dtype=np.uint8)
                    m = cv2.inRange(hsv, lower, upper)
                    mask_all = m if mask_all is None else cv2.bitwise_or(mask_all, m)

                if mask_all is not None:
                    # 简单去噪
                    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
                    mask_all = cv2.morphologyEx(mask_all, cv2.MORPH_OPEN, kernel, iterations=1)
                    mask_all = cv2.morphologyEx(mask_all, cv2.MORPH_CLOSE, kernel, iterations=2)

                    contours, _ = cv2.findContours(mask_all, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                    if contours:
                        cnt = max(contours, key=cv2.contourArea)
                        if cv2.contourArea(cnt) > 50:  # 避免小噪点
                            angle_deg, box_pts = self._angle_from_contour(cnt)
                            if angle_deg is not None and box_pts is not None:
                                # box_pts 是 ROI 坐标，要平移回整图坐标
                                box_pts[:, 0] += x1
                                box_pts[:, 1] += y1

                                # --- 高对比调试颜色（避开红/黄/蓝，白底也清楚）---
                                BOX_TOP = (255, 0, 255)   # 洋红（Magenta）
                                BOX_BASE = (0, 0, 0)      # 黑色底
                                AXIS_TOP = (255, 0, 255)  # 洋红主轴
                                AXIS_BASE = (0, 0, 0)     # 黑色底

                                # 旋转框：先黑色粗线打底，再洋红细线覆盖
                                cv2.polylines(img, [box_pts], True, BOX_BASE, 5)
                                cv2.polylines(img, [box_pts], True, BOX_TOP, 2)

                                # 画主轴线（蓝色）
                                cx_roi = float(det.bbox.center.position.x)
                                cy_roi = float(det.bbox.center.position.y)

                                theta = np.deg2rad(angle_deg)
                                dx, dy = float(np.cos(theta)), float(np.sin(theta))
                                axis_len = int(max(30.0, min(max(w, h), 180.0) * 0.6))

                                p1 = (int(cx_roi - dx * axis_len), int(cy_roi - dy * axis_len))
                                p2 = (int(cx_roi + dx * axis_len), int(cy_roi + dy * axis_len))

                                H, W = img.shape[:2]
                                p1 = (max(0, min(W-1, p1[0])), max(0, min(H-1, p1[1])))
                                p2 = (max(0, min(W-1, p2[0])), max(0, min(H-1, p2[1])))

                                cv2.line(img, p1, p2, AXIS_BASE, 5)
                                cv2.line(img, p1, p2, AXIS_TOP, 2)

                                # 把角度写出来（在原有 label 后面）
                                text2 = f"ang={angle_deg:.1f}"
                                cv2.putText(
                                    img,
                                    text2,
                                    (x1, ty + 22),
                                    cv2.FONT_HERSHEY_SIMPLEX,
                                    self._font_scale,
                                    (255, 255, 255),
                                    2,
                                    cv2.LINE_AA,
                                )

            if self._draw_center:
                cv2.circle(img, (int(round(cx)), int(round(cy))), 4, box_color, -1)

            text = f"{label} {score:.3f}"
            
            cv2.putText(
                img,
                text,
                (x1, ty),
                cv2.FONT_HERSHEY_SIMPLEX,
                self._font_scale,
                box_color,
                2,
                cv2.LINE_AA,
            )

        # 发布 debug image
        out_msg = self._bridge.cv2_to_imgmsg(img, encoding="bgr8")
        out_msg.header = self._last_header
        self._pub.publish(out_msg)

    def _load_ranges_from_yaml(self, path: str):
        """
        适配你的 YAML 格式：
          red:
            - [h1,s1,v1,h2,s2,v2]
            - [h1,s1,v1,h2,s2,v2]   # 多段（红色常用）
          blue:
            - [h1,s1,v1,h2,s2,v2]
          ...
          color_ratio_threshold: ...  # 忽略
        返回：
          dict[color] -> list[((H,S,V),(H,S,V))]
        """
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
        except Exception as e:
            self.get_logger().error(f"Failed to load YAML {path}: {e}")
            return {}

        if not isinstance(data, dict):
            return {}

        ranges = {}
        for k, v in data.items():
            if k == "color_ratio_threshold":
                continue
            if not isinstance(v, list):
                continue

            segs = []
            for item in v:
                if isinstance(item, list) and len(item) == 6:
                    h1, s1, v1, h2, s2, v2 = item
                    segs.append(((int(h1), int(s1), int(v1)), (int(h2), int(s2), int(v2))))
            if segs:
                ranges[str(k).lower()] = segs

        return ranges

    def _hsv_ranges_for_color(self, color_name: str):
        # 直接按 key 取（red/blue/yellow）
        return self._hsv_ranges.get(color_name.lower(), [])


    def _angle_from_contour(self, cnt):
        """
        返回 grasp_angle_deg（[-90, 90]）和 box_pts（4角点 int32）
        """
        rect = cv2.minAreaRect(cnt)
        (cx, cy), (w, h), raw_angle = rect
        if w <= 1e-6 or h <= 1e-6:
            return None, None

        if w < h:
            grasp_angle = raw_angle
        else:
            grasp_angle = raw_angle - 90.0

        if grasp_angle < -90.0:
            grasp_angle += 180.0
        elif grasp_angle > 90.0:
            grasp_angle -= 180.0

        box = cv2.boxPoints(rect).astype(np.int32)
        return float(grasp_angle), box

    # ----------------------------
    def _bgr_for_color(self, name: str):
        n = name.lower()
        if "red" in n:
            return (0, 0, 255)
        if "blue" in n:
            return (255, 0, 0)
        if "yellow" in n:
            return (0, 255, 255)
        return (0, 255, 0)  # default green


def main(args=None):
    try:
        rclpy.init(args=args)
        node = ColorBlobDebugImage()
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(e)


if __name__ == "__main__":
    main()
