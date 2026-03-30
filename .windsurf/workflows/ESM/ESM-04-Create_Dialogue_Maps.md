# Activity: Create Dialogue Maps

**Activity ID**: 20
**Order**: 4
**Phase**: Design
**Dependencies**: Predecessor: Activity 19 (Define Information Architecture)

## Description

Create Dialogue Maps

## Guidance

# Create Dialogue Maps (Screen Flows)

## Objective

Visualize screen-to-screen flows and entity relationships using Draw.io diagrams.

## Artifacts Created

- `docs/ux/2_dialogue-maps/screen-flow.drawio` - Visual flow diagrams

## Process

### 1. Create Domain Model Diagram

- Map core entities (Playbook, Workflow, Phase, Activity, Artifact, Role, Howto)
- Show relationships between entities
- Document cardinality and dependencies
- Use color coding:
  - Blue (#4682B4): FOB screens
  - Green (#82b366): Homebase screens
  - Purple (#9673a6): MCP operations

### 2. Create MVP Flow Diagram

- Create horizontal swimlanes per Act (ACT 0 → ACT 9)
- Add screen boxes with Screen IDs (e.g., `FOB-PLAYBOOKS-LIST+FIND-1`)
- **Bold border for LIST+FIND entry points**
- Add navigation arrows showing screen-to-screen flow
- Bold black arrows for main progression flow
- Document screen states (loading, error, success)

### 3. Validate Diagram Visually

- **Human eye check**: Does it look clear and understandable?
- **Fresh eyes test**: Can someone unfamiliar understand immediately?
- **Arrow clarity test**: Can you trace each flow path without confusion?
- **Primary user path is visually prominent and easy to follow**

## Tools

- Draw.io for diagram creation
- Use tabs: "Domain Model" and "MVP Flow - Local FOB"

## Deliverables

- ✅ Domain model diagram
- ✅ Complete MVP flow with all Acts
- ✅ **Each screen box labeled with Screen ID**: `FOB-{ENTITY}-{OPERATION}-{VERSION}`
- ✅ **LIST+FIND screens have bold borders** (entry points)
- ✅ **Screen IDs match User Journey exactly**
- ✅ **Navigation arrows show screen-to-screen flow**
- ✅ **Grep-able**: Can find screen in diagram by ID
- ✅ Screen state documentation
- ✅ Navigation flow clarity

## Artifacts Produced

None

## Artifacts Consumed

None

## Notes

No additional notes.
