Autonomous Robot Simulation
![Model](https://github.com/tomo1000cmd/Robospace/blob/main/Screenshot%20from%202025-09-30%2018-09-43.png) 
This project simulates a multi-robot system for autonomous navigation and room coverage in a predefined house layout. The system is built using Python and Pygame, allowing users to interact with robots, assign tasks, and visualize their movements in a grid-based environment.

System Overview

The simulation involves multiple robots navigating a house layout with rooms and doors, performing tasks such as moving to specific locations or covering entire rooms. The system includes a task manager for assigning tasks, a communication channel for message passing, and a user interface for controlling and monitoring robots.
Key Features

Multi-Robot Navigation: Two robots navigate a grid-based house layout, avoiding obstacles and other robots.
Task Assignment: Users can assign tasks (e.g., go to a location or cover a room) via a text input or mouse clicks.
Dynamic Pathfinding: Robots use the A* algorithm to find optimal paths, considering static and dynamic obstacles.
Room Coverage: Robots can cover entire rooms using a predefined coverage path.
Interactive UI: A Pygame-based interface displays robot status, logs, and allows task control.
Real-Time Monitoring: Logs and coverage percentages are updated in real-time.

System Architecture


The system is modular, with components interacting through a communication channel. Below is a schematic of the system architecture:

+---------------------+       +---------------------+       +---------------------+
|      Pygame UI      |<----->|    CommChannel     |<----->|      TaskManager    |
| - RobotControlPanel |       | - Publishes messages|       | - Assigns tasks     |
| - InputBox          |       | - Stores messages   |       | - Tracks robot status|
| - Global Buttons    |       |                     |       | - Manages rooms     |
+---------------------+       +---------------------+       +---------------------+
                                     |
                                     |
                                     v
+---------------------+       +---------------------+       +---------------------+
|      Robot(s)       |<----->|      Agents        |       |     Environment     |
| - Position          |       | - VehicleOperating |       | - Grid layout       |
| - Visited cells     |       | - MonitoringLogging|       | - Rooms & Doors     |
| - Draws itself      |       | - Configuration     |       | - Obstacles         |
+---------------------+       | - Cooperative       |       | - Cleanable cells   |
                              | - Forecasting       |       +---------------------+
                              +---------------------+
                                     |
                                     v
+---------------------+       +---------------------+
|     Pathfinding     |       |    House Layout    |
| - A* algorithm      |       | - ROOMS dict       |
| - Coverage path     |       | - DOORS list       |
+---------------------+       +---------------------+


Component Descriptions

Pygame UI (ui.py, launch.py):

Displays the grid, robots, and control panels.
Handles user input (mouse clicks, text input) to assign tasks or add obstacles.
Includes RobotControlPanel for robot-specific controls, InputBox for task input, and global buttons (Send Task, Reset).


CommChannel (launch.py):

A message-passing system that allows components (robots, agents, UI) to communicate.
Supports broadcasting commands like "go_to", "cover_room", "start", and "stop".


TaskManager (task_manager.py):

Manages task assignment to robots based on their status and proximity to room centers.
Tracks robot states (idle/busy) and room assignments.
Publishes tasks to the CommChannel.


Robot (robot.py):

Represents a robot with position, color, and visited cells.
Draws itself and its path on the Pygame surface.
Interacts with agents to update status and execute tasks.


Agents (agents.py):

VehicleOperatingAgent: Handles robot movement, pathfinding, and task execution (go_to, cover_room).
MonitoringLoggingAgent: Logs commands for each robot, displayed in the UI.
ConfigurationAgent, CooperativeAgent, ForecastingAgent: Placeholder agents for future extensions (currently minimal functionality).


Environment (environment.py):

Defines the grid-based house layout with rooms, walls, and doors.
Manages obstacles and cleanable cells.
Provides methods for validating positions and drawing the grid.


Pathfinding (pathfinding.py):

Implements the A* algorithm for navigation, considering static (walls) and dynamic (other robots) obstacles.
Generates coverage paths for room cleaning tasks.


House Layout (house_layout.py):

Defines the house structure with rooms (e.g., kitchen, living room) and doors.
Used by Environment to set up the grid and obstacles.



How It Works

Initialization:

The App class in launch.py initializes Pygame, the environment, robots, agents, and UI elements.
Robots are placed at starting positions (e.g., (1, 1) and (38, 38)).
The TaskManager is set up with robot IDs and room centers.


User Interaction:

Users can select a robot via the control panel and assign tasks:
Mouse Click: Left-click on the grid to send a "go_to" command to a valid position.
Text Input: Enter a task tuple (e.g., ("go_to", (10, 10)) or ("cover_room", (5, 5))) in the input box and click "Send Task".
Buttons: Start/stop robot movement or reset the simulation.


Right-clicking adds obstacles to the grid, clearing the path cache.


Task Processing:

The TaskManager assigns "cover_room" tasks to idle robots, prioritizing the closest unassigned room.
The VehicleOperatingAgent processes commands, computing paths using A* or coverage paths for rooms.
Robots move along paths at a fixed interval (0.2 seconds), updating their position and coverage percentage.


Dynamic Obstacle Avoidance:

The VehicleOperatingAgent uses status messages from other robots to avoid collisions by treating their positions (and adjacent cells) as dynamic obstacles.


Rendering and Logging:

The UI updates every frame, showing robot positions, paths, status, and logs.
The MonitoringLoggingAgent records commands, limited to the last 5 entries per robot.
Coverage percentage is calculated based on visited cleanable cells.



Running the Simulation
Prerequisites

Python 3.8+
Pygame (pip install pygame)

Instructions

Clone the repository or save all provided files in a directory.
Ensure house_layout.py, environment.py, robot.py, pathfinding.py, agents.py, task_manager.py, ui.py, and launch.py are in the same directory.
Run the simulation:python launch.py


Interact with the simulation:
Click on a robot’s control panel to select it.
Left-click on the grid to send a "go_to" task.
Right-click to add obstacles.
Enter task tuples in the input box (e.g., ("go_to", (10, 10)) or ("cover_room", (5, 5))) and click "Send Task".
Use "Start" and "Stop" buttons to control robot movement.
Click "Reset Simulation" to restart.



Example Usage

To send a robot to a specific position:
Select a robot by clicking its panel.
Enter ("go_to", (15, 15)) in the input box and click "Send Task".


To assign a room coverage task:
Enter ("cover_room", (5, 5)) (kitchen center) in the input box.
The robot will navigate to the room and cover it systematically.


To add an obstacle:
Right-click a grid cell to block it, forcing robots to replan paths.



Future Improvements

Enhance CooperativeAgent for better robot coordination.
Implement ForecastingAgent for predictive task planning.
Add more complex task types (e.g., multi-room coverage).
Improve UI with task history and detailed robot stats.

License
This project is for educational purposes and provided as-is. Feel free to modify and extend it for your needs.
