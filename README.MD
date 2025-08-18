Robot 2D Simulation Project
This project is a 2D simulation of a robotic environment where two robots ("robot1" and "robot2") navigate a house layout using pathfinding and autonomous patrol behaviors. The simulation is built with Python and Pygame, featuring a modular, object-oriented design with separate files for different components.
Overview

Purpose: Simulate robot navigation in a 40x40 grid-based house layout with rooms, doors, and obstacles.
Features:
Two robots with distinct roles and behaviors.
Autonomous patrol and manual control modes.
Real-time UI with start/stop buttons, mode toggles, status displays, and logs.
Pathfinding using the A* algorithm.
Modular design with separate files for environment, robots, agents, UI, and pathfinding.


Date Created: August 18, 2025

Requirements

Python 3.x
Pygame library (pip install pygame)

Installation

Clone or download the repository to your local machine.
Ensure all files are in the same directory:
robot2d.py
environment.py
robot.py
agents.py
pathfinding.py
ui.py
house_layout.py


Install the required dependency:pip install pygame


Run the simulation:python launch.py



Usage
Running the Simulation

Launch the script to open a 1200x900 Pygame window.
The grid (40x40 cells) displays the house layout with rooms and obstacles.
Two robots start at (1, 1) and (38, 38).

Controls

UI Panels (right side):
Click a panel to select a robot (Barn Cleaner or Chaser Bin).
Start: Begin movement or patrol.
Stop: Halt the robot.
Mode: Toggle between "Manual" (left-click to move) and "Autonomous" (patrols room centers).
Status: Displays current status, motion, position, mode, and special stat (e.g., "Cleaned Area: 50%").
Logs: Shows the last 5 log entries.


Grid Interaction:
Left-click on the grid to command the selected robot to move to that position (manual mode).
Right-click to add obstacles (clears path cache).


Global Buttons:
Stop All: Stops both robots.
Reset: Clears obstacles, resets the layout, and repositions robots.



Behavior

Autonomous Mode: Robots patrol room centers every 5 seconds.
Manual Mode: Robots move to clicked positions using A* pathfinding.
Special Stats: Barn Cleaner tracks "Cleaned Area," Chaser Bin tracks "Harvest Load" (random values).

Project Structure

robot2d.py: Main application file, orchestrates all components.
environment.py: Defines the Environment class for the grid and house layout.
robot.py: Defines the Robot class with drawing and movement logic.
agents.py: Contains all agent classes (e.g., VehicleOperatingAgent, AnomalyAgent) for robot behavior.
pathfinding.py: Implements the A* pathfinding algorithm.
ui.py: Defines UI components (Button, RobotControlPanel) for interaction.
house_layout.py: Defines the house layout with rooms and doors.

Contributing
Feel free to fork the repository and submit pull requests for enhancements or bug fixes. Suggestions for new features (e.g., additional robots, sensors) are welcome!
License
This project is open-source under the MIT License (see LICENSE file for details, if applicable).
Contact
For questions or support, please open an issue on the repository or contact the project maintainer.