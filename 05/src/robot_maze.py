import random
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyArrow
from IPython.display import display, clear_output
import time

class RobotMaze:
    """
    A robot maze environment for pathfinding exercises.
    The robot moves through a square-blocked maze trying to reach a target.
    
    Mazes are fully reproducible - calling get_maze_id() returns a string
    that encodes all maze parameters and can recreate the exact same maze.
    """
    
    # Direction constants (internal use)
    NORTH = 0
    EAST = 1
    SOUTH = 2
    WEST = 3
    AHEAD = 4
    BEHIND = 5
    LEFT = 6
    RIGHT = 7
    
    # Square status constants (internal use)
    WALL = 0
    EMPTY = 1
    BEEN_THERE = 2
    
    def __init__(self, maze_size=10, wall_probability=0.2, console_lines=10, max_attempts=1000, auto_visualize=True, delay=0.1, maze_id=None):
        """
        Initialize the robot maze environment.
        
        Args:
            maze_size: Size of the square maze (default 10x10)
            wall_probability: Probability of a square being a wall (0.0 to 1.0)
            console_lines: Number of console lines to display (default 10)
            max_attempts: Maximum attempts to generate a solvable maze (default 1000)
            auto_visualize: Automatically visualize after moves/turns (default True)
            delay: Default delay for auto-visualization (default 0.1 seconds)
            maze_id: String ID encoding all maze parameters for reproducibility (default None = random)
        """
        self.console_lines = console_lines
        self.console_buffer = []
        self.auto_visualize = auto_visualize
        self.delay = delay
        self.step_count = 0
        self.max_steps = 1000
        self.run_count = 0
        self.out_of_fuel = False
        
        # Parse or generate maze_id
        if maze_id is None:
            # Generate new maze with given parameters
            self.size = maze_size
            self.wall_probability = wall_probability
            random_seed = int(time.time() * 1000000) % 100000
            self.maze_id = f"{self.size}-{int(self.wall_probability*100)}-{random_seed}"
        else:
            # Parse maze_id to extract parameters
            try:
                parts = str(maze_id).split('-')
                self.size = int(parts[0])
                self.wall_probability = int(parts[1]) / 100.0
                random_seed = int(parts[2])
                self.maze_id = maze_id
            except (IndexError, ValueError):
                raise ValueError(
                    f"Invalid maze_id format: '{maze_id}'. "
                    f"Expected format: 'size-wallprob-seed' (e.g., '10-30-12345')"
                )
        
        # Create a dedicated RandomState for this maze instance
        # This is isolated from the global numpy random state
        self.rng = np.random.RandomState(random_seed)
        
        # Also seed Python's random for any operations that might use it
        random.seed(random_seed)
        
        # Set robot start position (top-left)
        self.robot_x = 0
        self.robot_y = 0
        self.robot_heading = self.SOUTH
        
        # Set target position (bottom-right by default)
        self.target_x = self.size - 1
        self.target_y = self.size - 1
        
        # Generate a solvable maze using our dedicated RNG
        attempts = 0
        while attempts < max_attempts:
            attempts += 1
            self.maze = np.ones((self.size, self.size), dtype=int) * self.EMPTY
            
            # Generate random walls using our dedicated RNG
            for i in range(self.size):
                for j in range(self.size):
                    if self.rng.random() < self.wall_probability:
                        self.maze[i, j] = self.WALL
            
            # Ensure start and target are not walls
            self.maze[0, 0] = self.EMPTY
            self.maze[self.target_y, self.target_x] = self.EMPTY
            
            # Check if maze is solvable
            if self._is_solvable():
                break
        else:
            raise RuntimeError(
                f"Failed to generate a solvable maze after {max_attempts} attempts. "
                f"Try reducing wall_probability (currently {self.wall_probability}) or "
                f"increasing maze_size (currently {self.size})."
            )
        
        self.maze[0, 0] = self.BEEN_THERE
        
        # Visualization
        self.fig = None
        self.ax_maze = None
        self.ax_console = None
        
        # Initial visualization
        if self.auto_visualize:
            self.visualize(delay=0)
    
    def _direction_to_int(self, direction):
        """Convert string direction to internal integer constant."""
        direction_map = {
            "NORTH": self.NORTH,
            "EAST": self.EAST,
            "SOUTH": self.SOUTH,
            "WEST": self.WEST,
            "AHEAD": self.AHEAD,
            "BEHIND": self.BEHIND,
            "LEFT": self.LEFT,
            "RIGHT": self.RIGHT
        }
        if isinstance(direction, str):
            direction_upper = direction.upper()
            if direction_upper in direction_map:
                return direction_map[direction_upper]
            else:
                raise ValueError(
                    f"Invalid direction: '{direction}'. "
                    f"Must be one of: LEFT, RIGHT, AHEAD, BEHIND"
                )
        return direction  # If it's already an int, return as-is for internal use
    
    def _int_to_direction(self, direction_int):
        """Convert internal integer constant to string direction."""
        direction_map = {
            self.NORTH: "NORTH",
            self.EAST: "EAST",
            self.SOUTH: "SOUTH",
            self.WEST: "WEST",
            self.AHEAD: "AHEAD",
            self.BEHIND: "BEHIND",
            self.LEFT: "LEFT",
            self.RIGHT: "RIGHT"
        }
        return direction_map.get(direction_int, str(direction_int))
    
    def _status_to_string(self, status):
        """Convert internal status constant to string."""
        status_map = {
            self.WALL: "WALL",
            self.EMPTY: "EMPTY",
            self.BEEN_THERE: "BEEN_THERE"
        }
        return status_map.get(status, str(status))
    
    def print(self, message):
        """
        Print a message to the console area below the maze.

        Args:
            message: String message to display
        """
        # Convert to string and handle special characters
        message_str = str(message)

        # Replace newlines and tabs with spaces
        message_str = message_str.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')

        # Remove other control characters (optional - keeps printable chars only)
        message_str = ''.join(char if char.isprintable() or char == ' ' else '' for char in message_str)

        # Crop to 90 characters
        if len(message_str) > 90:
            message_str = message_str[:90]

        self.console_buffer.append(message_str)

        # Keep only the last N lines
        if len(self.console_buffer) > self.console_lines:
            self.console_buffer = self.console_buffer[-self.console_lines:]

        # Initial visualization
        if self.auto_visualize:
            self.visualize(delay=0)
    
    
    def get_maze_id(self):
        """
        Returns maze id string that encodes all parameters needed to recreate this exact maze.
        Format: 'size-wallprobability-seed' (e.g., '10-30-12345')
        """
        return self.maze_id
    
    def clear_console(self):
        """Clear all messages from the console."""
        self.console_buffer = []
    
    def sense(self, direction):
        """
        Sense the square in the given direction relative to the robot.
        
        Args:
            direction: One of "AHEAD", "BEHIND", "LEFT", "RIGHT"
            
        Returns:
            "WALL", "EMPTY", or "BEEN_THERE"
        """
        direction_int = self._direction_to_int(direction)
        absolute_dir = self._relative_to_absolute(direction_int)
        x, y = self._get_adjacent_position(absolute_dir)
        
        if x < 0 or x >= self.size or y < 0 or y >= self.size:
            return "WALL"
        
        status = self.maze[y, x]
        return self._status_to_string(status)
    
    def get_heading(self):
        """
        Get the robot's current heading.
        
        Returns:
            One of "NORTH", "EAST", "SOUTH", "WEST"
        """
        return self._int_to_direction(self.robot_heading)
    
    def set_heading(self, direction):
        """
        Set the robot's heading.
        
        Args:
            direction: One of "NORTH", "EAST", "SOUTH", "WEST"
        """
        # Check if out of fuel
        if self.out_of_fuel:
            self.print("I can't do that... I'm out of fuel! Restart and try again.")
            self.print("Search unsuccessful: Target not reached by 1000 steps.")
            if self.auto_visualize:
                self.visualize(delay=self.delay)
            return
        
        # Update step count
        self.step_count += 1
        
        # Check step limit
        if self.step_count >= self.max_steps:
            self.out_of_fuel = True
            self.print("I can't do that... I'm out of fuel! Restart and try again.")
            self.print("Search unsuccessful: Target not reached by 1000 steps.")
            if self.auto_visualize:
                self.visualize(delay=self.delay)
            return 
        
        direction_int = self._direction_to_int(direction)
        if direction_int in [self.NORTH, self.EAST, self.SOUTH, self.WEST]:
            self.robot_heading = direction_int
    
    def get_robot_x(self):
        """Get robot's current x coordinate."""
        return self.robot_x
    
    def get_robot_y(self):
        """Get robot's current y coordinate."""
        return self.robot_y
    
    def get_target_x(self):
        """Get target's x coordinate."""
        return self.target_x
    
    def get_target_y(self):
        """Get target's y coordinate."""
        return self.target_y
    
    def turn(self, direction):
        """
        Turn the robot in the specified direction relative to current heading.
        
        Args:
            direction: One of "AHEAD", "BEHIND", "LEFT", "RIGHT"
        """
        # Check if out of fuel
        if self.out_of_fuel:
            self.print("I can't do that... I'm out of fuel! Restart and try again.")
            self.print("Search unsuccessful: Target not reached by 1000 steps.")
            if self.auto_visualize:
                self.visualize(delay=self.delay)
            return
        
        # Update step count
        self.step_count += 1
        
        # Check step limit
        if self.step_count >= self.max_steps:
            self.out_of_fuel = True
            self.print("I can't do that... I'm out of fuel! Restart and try again.")
            self.print("Search unsuccessful: Target not reached by 1000 steps.")
            if self.auto_visualize:
                self.visualize(delay=self.delay)
            return 
        
        direction_int = self._direction_to_int(direction)
        
        if direction_int == self.AHEAD:
            pass  # No change
        elif direction_int == self.BEHIND:
            self.robot_heading = (self.robot_heading + 2) % 4
        elif direction_int == self.LEFT:
            self.robot_heading = (self.robot_heading - 1) % 4
        elif direction_int == self.RIGHT:
            self.robot_heading = (self.robot_heading + 1) % 4
        
        if self.auto_visualize:
            self.visualize(delay=self.delay)
    
    
    def move(self):
        """
        Move the robot one square forward in its current heading.
        Returns True if successful, False if blocked by wall or boundary.
        """
        # Check if out of fuel
        if self.out_of_fuel:
            self.print("I can't do that... I'm out of fuel! Restart and try again.")
            self.print("Search unsuccessful: Target not reached by 1000 steps.")
            if self.auto_visualize:
                self.visualize(delay=self.delay)
            return 

        # Update step count
        self.step_count += 1

        # Check step limit
        if self.step_count >= self.max_steps:
            self.out_of_fuel = True
            self.print("I can't do that... I'm out of fuel! Restart and try again.")
            self.print("Search unsuccessful: Target not reached by 1000 steps.")
            if self.auto_visualize:
                self.visualize(delay=self.delay)
            return 

        new_x, new_y = self._get_adjacent_position(self.robot_heading)

        # Check if hitting a wall
        hit_wall = False
        if new_x < 0 or new_x >= self.size or new_y < 0 or new_y >= self.size:
            hit_wall = True
        elif self.maze[new_y, new_x] == self.WALL:
            hit_wall = True

        if hit_wall:
            # Add jitter effect - temporarily move forward slightly and bounce back
            if self.auto_visualize:
                # Save original position
                orig_x, orig_y = self.robot_x, self.robot_y

                # Calculate forward offset (0.15 squares for subtle effect)
                dx, dy = 0, 0
                if self.robot_heading == self.NORTH:
                    dy = -0.15
                elif self.robot_heading == self.EAST:
                    dx = 0.15
                elif self.robot_heading == self.SOUTH:
                    dy = 0.15
                elif self.robot_heading == self.WEST:
                    dx = -0.15

                # Show "pushed forward" position
                self.robot_x = orig_x + dx
                self.robot_y = orig_y + dy
                self.visualize(delay=self.delay)

                # Show "bounced back" position
                self.robot_x = orig_x
                self.robot_y = orig_y
                self.visualize(delay=self.delay)

            # Print message after the bump
            self.print("I tried to walk forward... ow that's a wall!")
            return

        # Move robot
        self.robot_x = new_x
        self.robot_y = new_y
        self.maze[new_y, new_x] = self.BEEN_THERE

        # Check if target reached
        if self.at_target():
            self.print(f"Target reached in {self.step_count} steps!")

        if self.auto_visualize:
            self.visualize(delay=self.delay)

        return

    def at_target(self):
        """Check if robot has reached the target."""
        return self.robot_x == self.target_x and self.robot_y == self.target_y
    
    def get_run_count(self):
        """Get the number of runs completed."""
        return self.run_count
    
    def get_step_count(self):
        """Get the number of steps taken in current run."""
        return self.step_count
    
    def check_fuel(self):
        """
        Check how much fuel (steps) the robot has remaining.
        
        Returns:
            Number of steps remaining before running out of fuel
        """
        return max(0, self.max_steps - self.step_count)
    
    def reset(self):
        """Reset the robot to starting position for a new run."""
        self.robot_x = 0
        self.robot_y = 0
        self.robot_heading = self.SOUTH
        self.run_count += 1
        self.step_count = 0
        self.out_of_fuel = False
        
        # Clear been_there markers
        self.maze[self.maze == self.BEEN_THERE] = self.EMPTY
        self.maze[0, 0] = self.BEEN_THERE
        
        if self.auto_visualize:
            self.visualize(delay=0)
    
    def visualize(self, delay=0.1):
        """
        Visualize the current state of the maze.
        
        Args:
            delay: Time to pause after drawing (for animation)
        """
        if self.fig is None:
            self.fig = plt.figure(figsize=(8, 10.05))
            # Create two subplots: maze on top, console below
            self.ax_maze = plt.subplot2grid((11, 1), (0, 0), rowspan=8)
            self.ax_console = plt.subplot2grid((11, 1), (8, 0), rowspan=3)
            plt.tight_layout()
        
        # Clear and redraw maze
        self.ax_maze.clear()
        self.ax_maze.set_xlim(-0.5, self.size - 0.5)
        self.ax_maze.set_ylim(-0.5, self.size - 0.5)
        self.ax_maze.set_aspect('equal')
        self.ax_maze.invert_yaxis()
        
        # Draw grid
        for i in range(self.size + 1):
            self.ax_maze.axhline(i - 0.5, color='gray', linewidth=0.5)
            self.ax_maze.axvline(i - 0.5, color='gray', linewidth=0.5)
        
        # Draw maze
        for y in range(self.size):
            for x in range(self.size):
                if self.maze[y, x] == self.WALL:
                    rect = Rectangle((x - 0.5, y - 0.5), 1, 1, 
                                    facecolor='black', edgecolor='none')
                    self.ax_maze.add_patch(rect)
                elif self.maze[y, x] == self.BEEN_THERE:
                    rect = Rectangle((x - 0.5, y - 0.5), 1, 1, 
                                    facecolor='lightgray', edgecolor='none')
                    self.ax_maze.add_patch(rect)
        
        # Draw target
        target_circle = plt.Circle((self.target_x, self.target_y), 0.3, 
                                   color='green', alpha=0.7)
        self.ax_maze.add_patch(target_circle)
        self.ax_maze.text(self.target_x, self.target_y, 'T', 
                    ha='center', va='center', fontsize=16, fontweight='bold')
        
        # Draw robot
        robot_circle = plt.Circle((self.robot_x, self.robot_y), 0.35, 
                                 color='red', alpha=0.7)
        self.ax_maze.add_patch(robot_circle)
        
        # Draw robot heading arrow
        dx, dy = 0, 0
        if self.robot_heading == self.NORTH:
            dx, dy = 0, -0.4
        elif self.robot_heading == self.EAST:
            dx, dy = 0.4, 0
        elif self.robot_heading == self.SOUTH:
            dx, dy = 0, 0.4
        elif self.robot_heading == self.WEST:
            dx, dy = -0.4, 0
        
        arrow = FancyArrow(self.robot_x, self.robot_y, dx, dy,
                          width=0.1, head_width=0.2, head_length=0.15,
                          color='white', zorder=10)
        self.ax_maze.add_patch(arrow)
        
        self.ax_maze.set_title(f'Robot Maze - Run #{self.run_count + 1}', 
                         fontsize=14, fontweight='bold')
        self.ax_maze.set_xticks([])
        self.ax_maze.set_yticks([])
        
        # Draw console
        self.ax_console.clear()
        self.ax_console.set_xlim(0, 1)
        self.ax_console.set_ylim(0, 1)
        self.ax_console.axis('off')
        
        # Draw console border and background
        console_border = Rectangle((0.01, 0.01), 0.98, 0.98,
                                   facecolor='#f5f5f5',
                                   edgecolor='#333333',
                                   linewidth=2)
        self.ax_console.add_patch(console_border)
        
        # Draw console title bar
        title_bar = Rectangle((0.01, 0.80), 0.98, 0.19,
                              facecolor='#2c3e50',
                              edgecolor='none')
        self.ax_console.add_patch(title_bar)
        
        # Console title text
        self.ax_console.text(0.5, 0.895, '━━━ Robot Console ━━━',
                           ha='center', va='center',
                           fontsize=11,
                           fontweight='bold',
                           fontfamily='monospace',
                           color='white')
        
        # Display console text
        console_text = '\n'.join(self.console_buffer[-self.console_lines:])
        self.ax_console.text(0.04, 0.76, console_text, 
                           verticalalignment='top',
                           horizontalalignment='left',
                           fontfamily='monospace',
                           fontsize=9,
                           color='#2c3e50',
                           wrap=True)
        
        display(self.fig)
        clear_output(wait=True)
        
        if delay > 0:
            time.sleep(delay)
    
    def _relative_to_absolute(self, relative_direction):
        """Convert relative direction to absolute direction."""
        if relative_direction == self.AHEAD:
            return self.robot_heading
        elif relative_direction == self.BEHIND:
            return (self.robot_heading + 2) % 4
        elif relative_direction == self.LEFT:
            return (self.robot_heading - 1) % 4
        elif relative_direction == self.RIGHT:
            return (self.robot_heading + 1) % 4
        return self.robot_heading
    
    def _get_adjacent_position(self, direction):
        """Get the position adjacent to robot in given absolute direction."""
        x, y = self.robot_x, self.robot_y
        
        if direction == self.NORTH:
            y -= 1
        elif direction == self.EAST:
            x += 1
        elif direction == self.SOUTH:
            y += 1
        elif direction == self.WEST:
            x -= 1
        
        return x, y
    
    def _is_solvable(self):
        """
        Check if the maze has a path from start (0,0) to target using BFS.
        
        Returns:
            True if a path exists, False otherwise
        """
        from collections import deque
        
        start = (0, 0)
        target = (self.target_x, self.target_y)
        
        if self.maze[0, 0] == self.WALL or self.maze[target[1], target[0]] == self.WALL:
            return False
        
        visited = set()
        queue = deque([start])
        visited.add(start)
        
        while queue:
            x, y = queue.popleft()
            
            if (x, y) == target:
                return True
            
            # Check all four directions
            for dx, dy in [(0, -1), (1, 0), (0, 1), (-1, 0)]:
                nx, ny = x + dx, y + dy
                
                if (0 <= nx < self.size and 0 <= ny < self.size and
                    (nx, ny) not in visited and
                    self.maze[ny, nx] != self.WALL):
                    visited.add((nx, ny))
                    queue.append((nx, ny))
        
        return False



def verify_maze_reproducibility(maze_id):
    """
    Test function to verify that two mazes with the same ID are identical.
    Returns True if mazes match, False otherwise.
    """
    maze1 = RobotMaze(maze_id=maze_id, auto_visualize=False)
    maze2 = RobotMaze(maze_id=maze_id, auto_visualize=False)
    
    # Compare the actual maze arrays
    mazes_match = np.array_equal(maze1.maze, maze2.maze)
    
    if mazes_match:
        print(f"SUCCESS: Mazes with ID '{maze_id}' are IDENTICAL")
    else:
        print(f"FAIL: Mazes with ID '{maze_id}' are DIFFERENT")
        print("This should not happen - please report this bug!")
    
    return mazes_match


# Demo
if __name__ == "__main__":
    print("Creating robot maze environment...")
    print("\nDirections (use as strings):")
    print("  'NORTH', 'EAST', 'SOUTH', 'WEST'")
    print("  'AHEAD', 'BEHIND', 'LEFT', 'RIGHT'")
    print("\nSquare Status (returned as strings):")
    print("  'WALL', 'EMPTY', 'BEEN_THERE'")
    print("\n" + "="*60)
    print("To use in Jupyter:")
    print("  robot = RobotMaze(maze_size=10, wall_probability=0.3)")
    print("  robot.turn('LEFT')  # Use strings!")
    print("  status = robot.sense('AHEAD')  # Returns 'WALL', 'EMPTY', etc.")
    print("  heading = robot.get_heading()  # Returns 'NORTH', 'SOUTH', etc.")
    print("  robot.print('Your message here')  # Print to console")
    print("  run_controller(robot, my_controller)")
    print("\nReproducible mazes:")
    print("  my_seed = robot.get_maze_id()")
    print("  robot2 = RobotMaze(maze_id=my_seed)  # Exact same maze!")
    print("\nVerify reproducibility:")
    print("  verify_maze_reproducibility('10-30-12345')")
    print("\nGraceful interrupt handling:")
    print("  Use run_controller(robot, my_controller)")
    print("  to prevent traceback when pressing stop in Jupyter")
    print("\nAuto-visualization is ON by default.")
    print("To disable: RobotMaze(auto_visualize=False)")
    print("To change delay: robot.delay=0.05")
    print("="*60)