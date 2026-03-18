# Wsy
# Autonomous Robot State Machine
# All of the following content is a draft and may be subject to change at any time.
## Overview
This repository contains the preliminary state machine logic for the robot to navigate, detect, grasp, and place blocks into designated bins. The architecture is divided into four main operational phases: **Preparation**, **Collecting**, **Placing**, and **Recovery**. 

## States
The system operates using the following core states:
* INIT = 0
* IDLE = 1
* MAPPING = 2
* SEARCH_OBJECT = 3
* NAVIGATE_TO_OBJECT = 4
* GRASP_OBJECT = 5
* NAVIGATE_TO_BIN = 6
* PLACE_OBJECT = 7
* RECOVERY = 8

---

## Operational Workflow

### 1. Preparation Phase (INIT)
Handles system initialization.
* **Workflow:** `[*] -> INIT -> IDLE`.
* This phase first ensures that the ROS 2 context is active and creates a node for the robot state machine. It then sets up an action client to communicate with the Nav2 navigation server (navigate_to_pose) and waits for the server to become available within a specified timeout. If the server is not available, the initialization fails to prevent unsafe operation. Additionally, the function subscribes to the LiDAR, camera, arm and any other topics to receive both internal and external sensor data.The IDLE
state serves as a short buffer between operations.
* **Optimization:** Potential target positions are stored during mapping to make subsequent navigation faster and more accurate.

### 2. Collecting Phase (COLLECTING)
Handles locating, navigating to, and grasping the objects.
* **Workflow:** `MAPPING -> SEARCH_OBJECT -> NAVIGATE_TO_OBJECT`.
* **MAPPING:** Moving within the operational area within a specified time limit (will be set according to the mapping function).
* **SEARCH_OBJECT:** For target localisation, the system relies on two possible scenarios during mapping: the target may enter the vision detection range and be directly detected, or the LiDAR may detect the base (white bin) of known dimensions to infer the direction of the target. If a target is found, it transitions to `NAVIGATE_TO_OBJECT`. If not, it adds 30 seconds to continue searching (`SEARCH_OBJECT(+30s)`).
* **NAVIGATE_TO_OBJECT:** Using the map, vision functions are activated when the distance to the target is less than 80cm. Once it reaches the grasp position, it triggers `GRASP_OBJECT`.
* **GRASP_OBJECT:** Since the camera is mounted on the arm, vision is called only once at the beginning to store the position before the arm moves.
    * **Success:** `total_count` and `success_count` increment by 1.
      * If `total_count == 3`, it transitions to `NAVIGATE_TO_BIN`. Otherwise, it returns to `SEARCH_OBJECT`.
    * **Failure:** `total_count` and `fail_count` increment by 1.
      * If `total_count == 3 and fail_count !=3', enters the `NAVIGATE_TO_BIN`
      * If `total_count == 3 and fail_count == 3`, enters the `RECOVERY` state.
        * Plan A: ask for human interruption to reset the 3 or only the last block
        * Plan B:  human interruption and put the blocks directly into the carrier and go to next state 


### 3. Placing Phase (PLACING)
Handles transporting and dropping the collected objects.
* **NAVIGATE_TO_BIN:** Acording to the map, the robot navigates to the designated drop-off location and transitions to `PLACE_OBJECT` upon arrival.
* **PLACE_OBJECT:** Executes the placement routine. Both successes and failures increment the `total_place_count` and their respective trackers (`succeed_place_count` or `fail_place_count`), then proceed to the next object.
* **Completion:** Once `total_place_count == 3 and fail_place_count !=3`, the robot returns to the starting point, completing the mission.

### 4. Recovery Phase (RECOVERY)
Acts as a safety buffer for functionality failures and terrain issues.
* **Triggers:** Activated if the robot gets stuck due to terrain conditions (during Search, Navigate, or Place) or if a manipulation task fails 3 times (`fail_count == 3`).
* **Resolution : Requires Human Interruption**

---

## State Machine Diagram

```mermaid
stateDiagram-v2
    [*] --> PREPARATION

    %% ---------------- preparation----------------
    state PREPARATION {
        INIT --> IDLE
        IDLE --> MAPPING
    }
    
    MAPPING --> COLLECTING : Mapping done

    note right of PREPARATION
        Move within specified time limit
        Use LiDAR to find target direction
        Store potential target positions
    end note

    %% ---------------- collecting----------------
    state COLLECTING {
        SEARCH_OBJECT --> NAVIGATE_TO_OBJECT : Target found
        SEARCH_OBJECT --> SEARCH_OBJECT : Target not found (30s)
        
        NAVIGATE_TO_OBJECT --> GRASP_OBJECT : Reach grasp position
        
        GRASP_OBJECT --> SEARCH_OBJECT : Done (total_count < 3)
        GRASP_OBJECT --> RETRY_TEST : Failed
        
        RETRY_TEST --> GRASP_OBJECT : Within reach retry
        RETRY_TEST --> SEARCH_OBJECT : Out of reach next
    }
    
    note right of COLLECTING
        Vision active when distance < 80cm
        Update counts after grasp
        Check bin surface during retry
    end note

    %% ---------------- placing ----------------
    GRASP_OBJECT --> PLACING : Done (total_count == 3)
    
    state PLACING {
        NAVIGATE_TO_BIN --> PLACE_OBJECT : Arrived
        PLACE_OBJECT --> PLACE_OBJECT : Done or Failed next item
    }
    
    PLACE_OBJECT --> [*] : succeed_place_count == 3

    note right of PLACING
        Update success and failure counts
    end note

    %% ---------------- recovery ----------------
    SEARCH_OBJECT --> RECOVERY : Stuck
    NAVIGATE_TO_OBJECT --> RECOVERY : Stuck
    GRASP_OBJECT --> RECOVERY : fail_count == 3
    NAVIGATE_TO_BIN --> RECOVERY : Stuck
    PLACE_OBJECT --> RECOVERY : fail_count == 3

    note right of RECOVERY
        Robot stuck due to terrain
        Failures require human intervention
    end note
