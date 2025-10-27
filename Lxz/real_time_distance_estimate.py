"""
Real-Time Color Box Distance Estimator
======================================
Author: Picklerick313
Date: 2025-10-27
Version: 1.0

Features:
- Multi-Space Color Segmentation (LAB + YCbCr + Chromaticity)
- Illumination-Invariant Detection
- Real-time Distance Estimation
- Kalman Filter Tracking
- Camera Calibration System
- Performance Metrics

Requirements:
pip install opencv-python numpy

Usage:
1. Run the script
2. Press 'c' to calibrate camera
3. Press 's' to save results
4. Press 'r' to reset
5. Press 'q' to quit
"""

import cv2
import numpy as np
import time
from collections import deque
import json
import os

# ============================================================================
# COLOR SEGMENTATION CLASSES
# ============================================================================

class LABColorSegmenter:
    """LAB color space segmentation - illumination invariant"""
    
    def __init__(self, color='red'):
        self.color_ranges = {
            'red': {
                'L': [20, 100],
                'A': [20, 127],
                'B': [-20, 80]
            },
            'blue': {
                'L': [20, 100],
                'A': [-20, 20],
                'B': [-128, -20]
            },
            'green': {
                'L': [20, 100],
                'A': [-128, -20],
                'B': [-20, 60]
            },
            'yellow': {
                'L': [50, 100],
                'A': [-20, 30],
                'B': [20, 127]
            }
        }
        self.color = color
    
    def segment_adaptive(self, frame):
        """Segment using A and B channels only (ignore L for max invariance)"""
        lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
        L, A, B = cv2.split(lab)
        
        ranges = self.color_ranges[self.color]
        
        # OpenCV stores LAB as L:[0,255], A/B:[0,255] with 128 offset
        mask_A = cv2.inRange(A, ranges['A'][0] + 128, ranges['A'][1] + 128)
        mask_B = cv2.inRange(B, ranges['B'][0] + 128, ranges['B'][1] + 128)
        
        mask = cv2.bitwise_and(mask_A, mask_B)
        
        # Cleanup
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        
        return mask


class YCbCrColorSegmenter:
    """YCbCr color space segmentation"""
    
    def __init__(self, color='red'):
        self.color_ranges = {
            'red': {
                'Cb': [0, 120],
                'Cr': [150, 255]
            },
            'blue': {
                'Cb': [140, 255],
                'Cr': [0, 120]
            },
            'green': {
                'Cb': [0, 120],
                'Cr': [0, 120]
            },
            'yellow': {
                'Cb': [0, 110],
                'Cr': [130, 170]
            }
        }
        self.color = color
    
    def segment(self, frame):
        """Segment using Cb and Cr channels"""
        ycbcr = cv2.cvtColor(frame, cv2.COLOR_BGR2YCrCb)
        Y, Cr, Cb = cv2.split(ycbcr)
        
        ranges = self.color_ranges[self.color]
        
        mask_Cb = cv2.inRange(Cb, ranges['Cb'][0], ranges['Cb'][1])
        mask_Cr = cv2.inRange(Cr, ranges['Cr'][0], ranges['Cr'][1])
        
        mask = cv2.bitwise_and(mask_Cb, mask_Cr)
        
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        
        return mask


class ChromaticitySegmenter:
    """Normalized RGB (Chromaticity) segmentation"""
    
    def __init__(self, color='red'):
        self.color_ranges = {
            'red': {
                'r': [0.35, 0.6],
                'g': [0.2, 0.4]
            },
            'blue': {
                'r': [0.15, 0.35],
                'g': [0.15, 0.35]
            },
            'green': {
                'r': [0.15, 0.35],
                'g': [0.35, 0.6]
            },
            'yellow': {
                'r': [0.35, 0.5],
                'g': [0.35, 0.5]
            }
        }
        self.color = color
    
    def segment(self, frame):
        """Segment using normalized RGB"""
        frame_float = frame.astype(np.float32)
        B, G, R = cv2.split(frame_float)
        
        sum_rgb = R + G + B + 1e-6
        
        r = R / sum_rgb
        g = G / sum_rgb
        
        ranges = self.color_ranges[self.color]
        
        r_scaled = (r * 255).astype(np.uint8)
        g_scaled = (g * 255).astype(np.uint8)
        
        mask_r = cv2.inRange(r_scaled, 
                            int(ranges['r'][0] * 255), 
                            int(ranges['r'][1] * 255))
        mask_g = cv2.inRange(g_scaled, 
                            int(ranges['g'][0] * 255), 
                            int(ranges['g'][1] * 255))
        
        mask = cv2.bitwise_and(mask_r, mask_g)
        
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        
        return mask


class MultiSpaceSegmenter:
    """Combines multiple color spaces with voting"""
    
    def __init__(self, color='red'):
        self.lab_seg = LABColorSegmenter(color=color)
        self.ycbcr_seg = YCbCrColorSegmenter(color=color)
        self.chroma_seg = ChromaticitySegmenter(color=color)
    
    def segment(self, frame, voting_threshold=2):
        """
        Multi-space segmentation with voting
        voting_threshold: 1, 2, or 3 (how many spaces must agree)
        """
        mask_lab = self.lab_seg.segment_adaptive(frame)
        mask_ycbcr = self.ycbcr_seg.segment(frame)
        mask_chroma = self.chroma_seg.segment(frame)
        
        # Convert to binary
        mask_lab = (mask_lab > 0).astype(np.uint8)
        mask_ycbcr = (mask_ycbcr > 0).astype(np.uint8)
        mask_chroma = (mask_chroma > 0).astype(np.uint8)
        
        # Voting
        votes = mask_lab + mask_ycbcr + mask_chroma
        
        # Apply threshold
        final_mask = (votes >= voting_threshold).astype(np.uint8) * 255
        
        # Final cleanup
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
        final_mask = cv2.morphologyEx(final_mask, cv2.MORPH_CLOSE, kernel)
        final_mask = cv2.morphologyEx(final_mask, cv2.MORPH_OPEN, kernel)
        
        return final_mask, votes


# ============================================================================
# KALMAN FILTER FOR TRACKING
# ============================================================================

class KalmanFilterTracker:
    """Kalman Filter for smooth tracking and prediction"""
    
    def __init__(self):
        self.kf = cv2.KalmanFilter(6, 3)  # 6 state vars, 3 measurements
        
        # State: [x, y, width, dx, dy, dwidth]
        self.kf.transitionMatrix = np.array([
            [1, 0, 0, 1, 0, 0],
            [0, 1, 0, 0, 1, 0],
            [0, 0, 1, 0, 0, 1],
            [0, 0, 0, 1, 0, 0],
            [0, 0, 0, 0, 1, 0],
            [0, 0, 0, 0, 0, 1]
        ], dtype=np.float32)
        
        # Measurement matrix
        self.kf.measurementMatrix = np.array([
            [1, 0, 0, 0, 0, 0],
            [0, 1, 0, 0, 0, 0],
            [0, 0, 1, 0, 0, 0]
        ], dtype=np.float32)
        
        self.kf.processNoiseCov = np.eye(6, dtype=np.float32) * 0.03
        self.kf.measurementNoiseCov = np.eye(3, dtype=np.float32) * 0.5
        
        self.initialized = False
    
    def initialize(self, x, y, width):
        """Initialize with first measurement"""
        self.kf.statePre = np.array([x, y, width, 0, 0, 0], dtype=np.float32)
        self.kf.statePost = np.array([x, y, width, 0, 0, 0], dtype=np.float32)
        self.initialized = True
    
    def predict(self):
        """Predict next state"""
        prediction = self.kf.predict()
        return prediction[0], prediction[1], prediction[2]
    
    def update(self, x, y, width):
        """Update with measurement"""
        measurement = np.array([[x], [y], [width]], dtype=np.float32)
        self.kf.correct(measurement)
        
        state = self.kf.statePost
        return state[0], state[1], state[2]


# ============================================================================
# DISTANCE ESTIMATOR
# ============================================================================

class DistanceEstimator:
    """Pinhole camera model distance estimator"""
    
    def __init__(self, known_width_cm):
        self.known_width = known_width_cm
        self.focal_length = None
        self.calibration_history = []
    
    def calibrate(self, pixel_width, actual_distance_cm):
        """
        Calibrate camera focal length
        Formula: focal_length = (pixel_width × distance) / real_width
        """
        if pixel_width <= 0:
            return False
        
        focal_length = (pixel_width * actual_distance_cm) / self.known_width
        
        # Store calibration
        self.calibration_history.append({
            'pixel_width': pixel_width,
            'distance': actual_distance_cm,
            'focal_length': focal_length
        })
        
        # Average multiple calibrations for better accuracy
        if len(self.calibration_history) > 5:
            self.calibration_history.pop(0)
        
        self.focal_length = np.mean([c['focal_length'] 
                                     for c in self.calibration_history])
        
        return True
    
    def estimate_distance(self, pixel_width):
        """
        Estimate distance to object
        Formula: distance = (real_width × focal_length) / pixel_width
        """
        if self.focal_length is None or pixel_width <= 0:
            return None
        
        distance = (self.known_width * self.focal_length) / pixel_width
        return distance
    
    def save_calibration(self, filename='calibration.json'):
        """Save calibration to file"""
        if self.focal_length is None:
            return False
        
        data = {
            'focal_length': float(self.focal_length),
            'known_width': float(self.known_width),
            'calibration_history': self.calibration_history
        }
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=4)
        
        return True
    
    def load_calibration(self, filename='calibration.json'):
        """Load calibration from file"""
        if not os.path.exists(filename):
            return False
        
        with open(filename, 'r') as f:
            data = json.load(f)
        
        self.focal_length = data['focal_length']
        self.known_width = data['known_width']
        self.calibration_history = data['calibration_history']
        
        return True


# ============================================================================
# MAIN APPLICATION
# ============================================================================

class RealTimeDistanceEstimator:
    """Complete real-time distance estimation system"""
    
    def __init__(self, box_color='red', known_width_cm=10.0, camera_id=0):
        """
        Initialize the system
        
        Args:
            box_color: Color of box to detect ('red', 'blue', 'green', 'yellow')
            known_width_cm: Real-world width of the box in centimeters
            camera_id: Camera device ID (0 for default webcam)
        """
        # Segmentation
        self.segmenter = MultiSpaceSegmenter(color=box_color)
        
        # Tracking
        self.kalman = KalmanFilterTracker()
        
        # Distance estimation
        self.distance_estimator = DistanceEstimator(known_width_cm)
        
        # Camera
        self.cap = cv2.VideoCapture(camera_id)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.cap.set(cv2.CAP_PROP_FPS, 30)
        
        # State
        self.box_color = box_color
        self.known_width = known_width_cm
        self.tracking_initialized = False
        
        # Performance metrics
        self.fps_history = deque(maxlen=30)
        self.distance_history = deque(maxlen=30)
        
        # Try to load previous calibration
        if self.distance_estimator.load_calibration():
            print("✅ Loaded previous calibration!")
            print(f"   Focal length: {self.distance_estimator.focal_length:.2f} pixels")
    
    def find_box_contour(self, mask):
        """Find the largest contour (box) in mask"""
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, 
                                       cv2.CHAIN_APPROX_SIMPLE)
        
        if len(contours) == 0:
            return None
        
        # Get largest contour
        largest_contour = max(contours, key=cv2.contourArea)
        
        # Filter by minimum area
        if cv2.contourArea(largest_contour) < 500:
            return None
        
        return largest_contour
    
    def extract_measurements(self, contour):
        """Extract center and width from contour"""
        # Bounding box
        x, y, w, h = cv2.boundingRect(contour)
        
        # Center using moments (more accurate)
        M = cv2.moments(contour)
        if M["m00"] != 0:
            cx = int(M["m10"] / M["m00"])
            cy = int(M["m01"] / M["m00"])
        else:
            cx = x + w // 2
            cy = y + h // 2
        
        return {
            'center': (cx, cy),
            'bbox': (x, y, w, h),
            'width': w,
            'height': h,
            'area': cv2.contourArea(contour)
        }
    
    def draw_results(self, frame, measurements, distance, predicted_pos=None):
        """Draw detection results on frame"""
        cx, cy = measurements['center']
        x, y, w, h = measurements['bbox']
        
        # Draw bounding box
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
        
        # Draw center point
        cv2.circle(frame, (cx, cy), 5, (0, 0, 255), -1)
        cv2.circle(frame, (cx, cy), 20, (0, 0, 255), 2)
        
        # Draw crosshair
        cv2.line(frame, (cx - 15, cy), (cx + 15, cy), (0, 0, 255), 2)
        cv2.line(frame, (cx, cy - 15), (cx, cy + 15), (0, 0, 255), 2)
        
        # Draw predicted position (Kalman)
        if predicted_pos is not None:
            pred_x, pred_y = map(int, predicted_pos[:2])
            cv2.circle(frame, (pred_x, pred_y), 8, (255, 0, 0), 2)
        
        # Draw info text
        info_lines = [
            f"Width: {w} px",
            f"Center: ({cx}, {cy})",
        ]
        
        if distance is not None:
            info_lines.insert(0, f"Distance: {distance:.1f} cm")
            self.distance_history.append(distance)
            
            # Draw distance on box
            cv2.putText(frame, f"{distance:.1f} cm", (x, y - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        # Draw info panel
        y_offset = 30
        for i, line in enumerate(info_lines):
            cv2.putText(frame, line, (10, y_offset + i * 25),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        return frame
    
    def draw_hud(self, frame):
        """Draw heads-up display with stats"""
        h, w = frame.shape[:2]
        
        # FPS
        if len(self.fps_history) > 0:
            fps = np.mean(self.fps_history)
            cv2.putText(frame, f"FPS: {fps:.1f}", (w - 120, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
        
        # Calibration status
        if self.distance_estimator.focal_length is not None:
            cal_text = f"Calibrated (f={self.distance_estimator.focal_length:.0f}px)"
            cv2.putText(frame, cal_text, (10, h - 40),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        else:
            cv2.putText(frame, "NOT CALIBRATED - Press 'c'", (10, h - 40),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
        
        # Instructions
        instructions = [
            "Controls:",
            "c - Calibrate",
            "s - Save",
            "r - Reset",
            "q - Quit"
        ]
        
        y_start = h - 160
        for i, text in enumerate(instructions):
            cv2.putText(frame, text, (10, y_start + i * 20),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200, 200, 200), 1)
        
        return frame
    
    def calibrate_interactive(self):
        """Interactive calibration mode"""
        print("\n" + "="*60)
        print("CALIBRATION MODE")
        print("="*60)
        print(f"Box color: {self.box_color}")
        print(f"Known box width: {self.known_width} cm")
        print("\n1. Place the box at a known distance from camera")
        print("2. Ensure the box is clearly visible and segmented")
        print("3. Measure the actual distance with a ruler/tape")
        print("\nPress ENTER after measuring...")
        
        input()
        
        try:
            actual_distance = float(input("Enter actual distance (cm): "))
            
            if actual_distance <= 0:
                print("❌ Invalid distance!")
                return False
            
            # Capture frame and detect box
            ret, frame = self.cap.read()
            if not ret:
                print("❌ Could not capture frame!")
                return False
            
            # Segment
            mask, _ = self.segmenter.segment(frame, voting_threshold=2)
            
            # Find contour
            contour = self.find_box_contour(mask)
            
            if contour is None:
                print("❌ Could not detect box! Make sure it's visible.")
                return False
            
            # Measure
            measurements = self.extract_measurements(contour)
            pixel_width = measurements['width']
            
            # Calibrate
            success = self.distance_estimator.calibrate(pixel_width, actual_distance)
            
            if success:
                print(f"✅ Calibration successful!")
                print(f"   Pixel width: {pixel_width} px")
                print(f"   Actual distance: {actual_distance} cm")
                print(f"   Focal length: {self.distance_estimator.focal_length:.2f} px")
                
                # Save calibration
                self.distance_estimator.save_calibration()
                print("   Calibration saved to calibration.json")
                
                return True
            else:
                print("❌ Calibration failed!")
                return False
                
        except ValueError:
            print("❌ Invalid input!")
            return False
    
    def run(self):
        """Main processing loop"""
        print("\n" + "="*60)
        print("REAL-TIME COLOR BOX DISTANCE ESTIMATOR")
        print("="*60)
        print(f"Box color: {self.box_color}")
        print(f"Known width: {self.known_width} cm")
        print("\nPress 'c' to calibrate camera")
        print("Press 's' to save frame")
        print("Press 'r' to reset tracking")
        print("Press 'q' to quit")
        print("="*60 + "\n")
        
        while True:
            start_time = time.time()
            
            # Capture frame
            ret, frame = self.cap.read()
            if not ret:
                print("❌ Could not read frame from camera")
                break
            
            # Segment using multi-space method
            mask, votes = self.segmenter.segment(frame, voting_threshold=2)
            
            # Find box contour
            contour = self.find_box_contour(mask)
            
            predicted_pos = None
            distance = None
            
            if contour is not None:
                # Extract measurements
                measurements = self.extract_measurements(contour)
                
                cx, cy = measurements['center']
                width = measurements['width']
                
                # Initialize or update Kalman filter
                if not self.kalman.initialized:
                    self.kalman.initialize(cx, cy, width)
                else:
                    # Predict
                    pred_x, pred_y, pred_width = self.kalman.predict()
                    predicted_pos = (pred_x, pred_y, pred_width)
                    
                    # Update
                    cx, cy, width = self.kalman.update(cx, cy, width)
                
                # Estimate distance
                distance = self.distance_estimator.estimate_distance(width)
                
                # Draw results
                frame = self.draw_results(frame, measurements, distance, predicted_pos)
            
            else:
                # Lost tracking
                if self.kalman.initialized:
                    # Use prediction
                    pred_x, pred_y, pred_width = self.kalman.predict()
                    cv2.circle(frame, (int(pred_x), int(pred_y)), 15, 
                             (0, 255, 255), 2)
                    cv2.putText(frame, "PREDICTING...", (int(pred_x) - 50, int(pred_y) - 20),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)
            
            # Calculate FPS
            fps = 1.0 / (time.time() - start_time)
            self.fps_history.append(fps)
            
            # Draw HUD
            frame = self.draw_hud(frame)
            
            # Create visualization windows
            votes_vis = (votes / 3.0 * 255).astype(np.uint8)
            votes_colored = cv2.applyColorMap(votes_vis, cv2.COLORMAP_JET)
            
            # Display
            cv2.imshow('Real-Time Distance Estimator', frame)
            cv2.imshow('Segmentation Mask', mask)
            cv2.imshow('Voting Confidence', votes_colored)
            
            # Handle keyboard input
            key = cv2.waitKey(1) & 0xFF
            
            if key == ord('q'):
                print("\n👋 Shutting down...")
                break
                
            elif key == ord('c'):
                # Calibration mode
                self.calibrate_interactive()
                
            elif key == ord('r'):
                # Reset tracking
                self.kalman.initialized = False
                self.tracking_initialized = False
                print("🔄 Tracking reset")
                
            elif key == ord('s'):
                # Save current frame
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                filename = f"capture_{timestamp}.jpg"
                cv2.imwrite(filename, frame)
                print(f"📸 Saved frame to {filename}")
        
        # Cleanup
        self.cap.release()
        cv2.destroyAllWindows()
        
        # Print statistics
        print("\n" + "="*60)
        print("SESSION STATISTICS")
        print("="*60)
        if len(self.fps_history) > 0:
            print(f"Average FPS: {np.mean(self.fps_history):.2f}")
        if len(self.distance_history) > 0:
            print(f"Average distance: {np.mean(self.distance_history):.2f} cm")
            print(f"Min distance: {np.min(self.distance_history):.2f} cm")
            print(f"Max distance: {np.max(self.distance_history):.2f} cm")
        print("="*60)


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

def main():
    """Main function"""
    
    # Configuration
    BOX_COLOR = 'red'          # Change to: 'red', 'blue', 'green', 'yellow'
    KNOWN_WIDTH_CM = 10.0      # Real-world width of your box in centimeters
    CAMERA_ID = 0              # 0 for default webcam, 1 for external
    
    try:
        # Create estimator
        estimator = RealTimeDistanceEstimator(
            box_color=BOX_COLOR,
            known_width_cm=KNOWN_WIDTH_CM,
            camera_id=CAMERA_ID
        )
        
        # Run
        estimator.run()
        
    except KeyboardInterrupt:
        print("\n\n⚠️ Interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()