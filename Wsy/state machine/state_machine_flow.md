# State Machine Flow

This document describes the main state transition logic of the robot system.

```text
┌────────────┐
│    INIT    │
└─────┬──────┘
      │ init success
      v
┌────────────┐
│    IDLE    │
└─────┬──────┘
      │ start mission
      v
┌────────────┐
│  MAPPING   │
└─────┬──────┘
      │ map saved + start pose stored
      v
┌────────────────┐
│ SEARCH_OBJECT  │
└─────┬──────────┘
      │ target found
      v
┌────────────────────┐
│ NAVIGATE_TO_OBJECT │
└─────┬──────────────┘
      │ reached grasp position
      v
┌────────────────┐
│  GRASP_OBJECT  │
└─────┬──────────┘
      │
      ├── grasp success
      │       total_count += 1
      │       success_count += 1
      │
      │       if total_count < 3
      │             ↓
      │       SEARCH_OBJECT
      │
      │       if total_count == 3
      │             ↓
      │       NAVIGATE_TO_BIN
      │
      ├── grasp failed
      │       ↓
      │  RETRY_TEST
      │
      └── fail_count == 3
              ↓
          RECOVERY


┌──────────────┐
│  RETRY_TEST  │
└─────┬────────┘
      │
      ├── object still reachable
      │       ↓
      │  GRASP_OBJECT
      │
      ├── object not reachable
      │       total_count += 1
      │       fail_count += 1
      │
      │       if total_count < 3
      │             ↓
      │       SEARCH_OBJECT
      │
      │       if total_count == 3
      │             ↓
      │       NAVIGATE_TO_BIN
      │
      └── fail_count == 3
              ↓
          RECOVERY


┌─────────────────┐
│ NAVIGATE_TO_BIN │
└─────┬───────────┘
      │ reached bin area(start point)
      v
┌──────────────┐
│ PLACE_OBJECT │
└─────┬────────┘
      │
      ├── place success
      │       total_place_count += 1
      │       succeed_place_count += 1
      │
      │       if succeed_place_count < 3
      │             ↓
      │       PLACE_OBJECT
      │
      │       if succeed_place_count == 3
      │             ↓
      │       DONE
      │
      ├── place failed
      │       total_place_count += 1
      │       fail_place_count += 1
      │       retry PLACE_OBJECT
      │
      └── fail_place_count == 3
              ↓
          RECOVERY
```
