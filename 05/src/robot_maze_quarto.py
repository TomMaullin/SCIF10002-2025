import random
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyArrow
import time
from PIL import Image
import io

# Try to import IPython display functions
try:
    from IPython.display import display, clear_output, Image as IPImage
    from IPython import get_ipython
    IPYTHON_AVAILABLE = True
except ImportError:
    IPYTHON_AVAILABLE = False

def is_notebook():
    """Detect if running in a Jupyter notebook (not Quarto)."""
    if not IPYTHON_AVAILABLE:
        return False
    try:
        shell = get_ipython().__class__.__name__
        if shell == 'ZMQInteractiveShell':
            return True  # Jupyter notebook or qtconsole
        elif 'google.colab' in str(get_ipython()):
            return True  # Google Colab
        else:
            return False  # Other type (?)
    except (NameError, AttributeError):
        return False  # Probably standard Python interpreter

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
    
    def __init__(self, maze_size=6, wall_probability=0.4, console_lines=6, max_attempts=1000, auto_visualize=False, delay=0.5, maze_id=None):
        """
        Initialize the robot maze environment.
        
        Args:
            maze_size: Size of the square maze (default 10x10)
            wall_probability: Probability of a square being a wall (0.0 to 1.0)
            console_lines: Number of console lines to display (default 6)
            max_attempts: Maximum attempts to generate a solvable maze (default 1000)
            auto_visualize: Automatically visualize after moves/turns (default False for Quarto)
            delay: Default delay for auto-visualization (default 0.1 seconds)
            maze_id: String ID encoding all maze parameters for reproducibility (default None = random)
        """
        self.console_lines = console_lines
        self.console_buffer = []
        self.auto_visualize = auto_visualize
        self.delay = delay
        self.step_count = 0
        self.max_steps = 100
        self.run_count = 0
        self.out_of_fuel = False
        self.is_notebook_env = is_notebook()
        
        # Frame capture for GIF rendering
        self.frames = []
        self.capture_frames = True  # Always capture frames for render()
        
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
        self.rng = np.random.RandomState(random_seed)
        random.seed(random_seed)
        
        # Set robot start position (top-left)
        self.robot_x = 0
        self.robot_y = 0
        self.robot_heading = self.SOUTH
        
        # Set target position (bottom-right by default)
        self.target_x = self.size - 1
        self.target_y = self.size - 1
        
        # Generate a solvable maze
        attempts = 0
        while attempts < max_attempts:
            attempts += 1
            self.maze = np.ones((self.size, self.size), dtype=int) * self.EMPTY
            
            for i in range(self.size):
                for j in range(self.size):
                    if self.rng.random() < self.wall_probability:
                        self.maze[i, j] = self.WALL
            
            self.maze[0, 0] = self.EMPTY
            self.maze[self.target_y, self.target_x] = self.EMPTY
            
            if self._is_solvable():
                break
        else:
            raise RuntimeError(
                f"Failed to generate a solvable maze after {max_attempts} attempts. "
                f"Try reducing wall_probability (currently {self.wall_probability}) or "
                f"increasing maze_size (currently {self.size})."
            )
        
        self.maze[0, 0] = self.BEEN_THERE
        
        # Capture initial state
        if self.capture_frames:
            self._capture_frame()
    
    def _direction_to_int(self, direction):
        """Convert string direction to internal integer constant."""
        direction_map = {
            "NORTH": self.NORTH, "EAST": self.EAST,
            "SOUTH": self.SOUTH, "WEST": self.WEST,
            "AHEAD": self.AHEAD, "BEHIND": self.BEHIND,
            "LEFT": self.LEFT, "RIGHT": self.RIGHT
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
        return direction
    
    def _int_to_direction(self, direction_int):
        """Convert internal integer constant to string direction."""
        direction_map = {
            self.NORTH: "NORTH", self.EAST: "EAST",
            self.SOUTH: "SOUTH", self.WEST: "WEST",
            self.AHEAD: "AHEAD", self.BEHIND: "BEHIND",
            self.LEFT: "LEFT", self.RIGHT: "RIGHT"
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
        """Print a message to the console area."""
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
        if len(self.console_buffer) > self.console_lines:
            self.console_buffer = self.console_buffer[-self.console_lines:]
        
        if self.auto_visualize:
            self.visualize(delay=0)
        elif self.capture_frames:
            self._capture_frame()
    
    def get_maze_id(self):
        """Returns maze id string for reproducibility."""
        return self.maze_id
    
    def clear_console(self):
        """Clear all messages from the console."""
        self.console_buffer = []
    
    def sense(self, direction):
        """Sense the square in the given direction relative to the robot."""
        direction_int = self._direction_to_int(direction)
        absolute_dir = self._relative_to_absolute(direction_int)
        x, y = self._get_adjacent_position(absolute_dir)
        
        if x < 0 or x >= self.size or y < 0 or y >= self.size:
            return "WALL"
        
        status = self.maze[y, x]
        return self._status_to_string(status)
    
    def get_heading(self):
        """Get the robot's current heading."""
        return self._int_to_direction(self.robot_heading)
    
    def set_heading(self, direction):
        """Set the robot's heading."""
        if self.out_of_fuel:
            self.print("I'm out of fuel! Please restart and try again.")
            self.print("Search unsuccessful: Target not reached by 100 steps.")
            if self.capture_frames:
                self._capture_frame()
            return
        
        self.step_count += 1
        
        if self.step_count >= self.max_steps:
            self.out_of_fuel = True
            self.print("I'm out of fuel! Please restart and try again.")
            self.print("Search unsuccessful: Target not reached by 100 steps.")
            if self.capture_frames:
                self._capture_frame()
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
        """Turn the robot in the specified direction."""
        if self.out_of_fuel:
            self.print("I'm out of fuel! Please restart and try again.")
            self.print("Search unsuccessful: Target not reached by 100 steps.")
            if self.capture_frames:
                self._capture_frame()
            return
        
        self.step_count += 1
        
        if self.step_count >= self.max_steps:
            self.out_of_fuel = True
            self.print("I'm out of fuel! Please restart and try again.")
            self.print("Search unsuccessful: Target not reached by 100 steps.")
            if self.capture_frames:
                self._capture_frame()
            return 
        
        direction_int = self._direction_to_int(direction)
        
        if direction_int == self.AHEAD:
            pass
        elif direction_int == self.BEHIND:
            self.robot_heading = (self.robot_heading + 2) % 4
        elif direction_int == self.LEFT:
            self.robot_heading = (self.robot_heading - 1) % 4
        elif direction_int == self.RIGHT:
            self.robot_heading = (self.robot_heading + 1) % 4
        
        if self.auto_visualize:
            self.visualize(delay=self.delay)
        elif self.capture_frames:
            self._capture_frame()

    def move(self):
        """Move the robot one square forward."""
        if self.out_of_fuel:
            self.print("I'm out of fuel! Please restart and try again.")
            self.print("Search unsuccessful: Target not reached by 100 steps.")
            if self.capture_frames:
                self._capture_frame()
            return 
        
        self.step_count += 1
        
        if self.step_count >= self.max_steps:
            self.out_of_fuel = True
            self.print("I'm out of fuel! Please restart and try again.")
            self.print("Search unsuccessful: Target not reached by 100 steps.")
            if self.capture_frames:
                self._capture_frame()
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
            if self.capture_frames:
                # Save original position
                orig_x, orig_y = self.robot_x, self.robot_y
                
                # Calculate forward offset (reduced to 0.15 squares for subtler effect)
                dx, dy = 0, 0
                if self.robot_heading == self.NORTH:
                    dy = -0.15
                elif self.robot_heading == self.EAST:
                    dx = 0.15
                elif self.robot_heading == self.SOUTH:
                    dy = 0.15
                elif self.robot_heading == self.WEST:
                    dx = -0.15
                
                # Capture "pushed forward" frame
                self.robot_x = orig_x + dx
                self.robot_y = orig_y + dy
                self._capture_frame()
                
                # Capture "bounced back" frame
                self.robot_x = orig_x
                self.robot_y = orig_y
                self._capture_frame()
            
            # Print message after the bump
            self.print("I tried to walk forward... ow that's a wall!")
            
            return
        
        # Normal move - no wall hit
        self.robot_x = new_x
        self.robot_y = new_y
        self.maze[new_y, new_x] = self.BEEN_THERE
        
        if self.at_target():
            self.print(f"Target reached in {self.step_count} steps!")
        
        if self.auto_visualize:
            self.visualize(delay=self.delay)
        elif self.capture_frames:
            self._capture_frame()
        
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
        """Check how much fuel (steps) the robot has remaining."""
        return max(0, self.max_steps - self.step_count)
    
    def reset(self):
        """Reset the robot to starting position for a new run."""
        self.robot_x = 0
        self.robot_y = 0
        self.robot_heading = self.SOUTH
        self.run_count += 1
        self.step_count = 0
        self.out_of_fuel = False
        
        self.maze[self.maze == self.BEEN_THERE] = self.EMPTY
        self.maze[0, 0] = self.BEEN_THERE
        
        # Clear frames for new run
        self.frames = []
        
        if self.auto_visualize:
            self.visualize(delay=0)
        elif self.capture_frames:
            self._capture_frame()
    
    def _capture_frame(self):
        """Capture current state as a frame for GIF rendering."""
        fig = plt.figure(figsize=(5, 6.25))
        ax_maze = plt.subplot2grid((11, 1), (0, 0), rowspan=8)
        ax_console = plt.subplot2grid((11, 1), (8, 0), rowspan=3)
        plt.subplots_adjust(hspace=0.3, left=0.05, right=0.95, top=0.95, bottom=0.05)
        
        self._draw_maze(ax_maze, ax_console)
        
        # Save figure to buffer - reduced DPI keeps file size small
        buf = io.BytesIO()
        fig.savefig(buf, format='png', dpi=64, bbox_inches='tight')
        buf.seek(0)
        
        # Convert to PIL Image
        img = Image.open(buf)
        self.frames.append(img.copy())
        
        buf.close()
        plt.close(fig)
    
    def _draw_maze(self, ax_maze, ax_console):
        """Draw the maze and console on given axes."""
        # Clear and setup maze
        ax_maze.clear()
        ax_maze.set_xlim(-0.5, self.size - 0.5)
        ax_maze.set_ylim(-0.5, self.size - 0.5)
        ax_maze.set_aspect('equal')
        ax_maze.invert_yaxis()
        
        # Draw grid
        for i in range(self.size + 1):
            ax_maze.axhline(i - 0.5, color='gray', linewidth=0.5)
            ax_maze.axvline(i - 0.5, color='gray', linewidth=0.5)
        
        # Draw maze squares
        for y in range(self.size):
            for x in range(self.size):
                if self.maze[y, x] == self.WALL:
                    rect = Rectangle((x - 0.5, y - 0.5), 1, 1, 
                                    facecolor='black', edgecolor='none')
                    ax_maze.add_patch(rect)
                elif self.maze[y, x] == self.BEEN_THERE:
                    rect = Rectangle((x - 0.5, y - 0.5), 1, 1, 
                                    facecolor='lightgray', edgecolor='none')
                    ax_maze.add_patch(rect)
        
        # Draw target
        target_circle = plt.Circle((self.target_x, self.target_y), 0.3, 
                                   color='green', alpha=0.7)
        ax_maze.add_patch(target_circle)
        ax_maze.text(self.target_x, self.target_y, 'T', 
                    ha='center', va='center', fontsize=10, fontweight='bold')
        
        # Draw robot
        robot_circle = plt.Circle((self.robot_x, self.robot_y), 0.35, 
                                 color='red', alpha=0.7)
        ax_maze.add_patch(robot_circle)
        
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
        ax_maze.add_patch(arrow)
        
        ax_maze.set_title(f'Robot Maze - Run #{self.run_count + 1}', 
                         fontsize=10, fontweight='bold')
        ax_maze.set_xticks([])
        ax_maze.set_yticks([])
        
        # Draw console
        ax_console.clear()
        ax_console.set_xlim(0, 1)
        ax_console.set_ylim(0, 1)
        ax_console.axis('off')
        
        console_border = Rectangle((0.01, 0.01), 0.98, 0.98,
                                   facecolor='#f5f5f5',
                                   edgecolor='#333333',
                                   linewidth=2)
        ax_console.add_patch(console_border)
        
        title_bar = Rectangle((0.01, 0.80), 0.98, 0.19,
                              facecolor='#2c3e50',
                              edgecolor='none')
        ax_console.add_patch(title_bar)
        
        ax_console.text(0.5, 0.895, '━━━ Robot Console ━━━',
                       ha='center', va='center',
                       fontsize=11,
                       fontweight='bold',
                       fontfamily='monospace',
                       color='white')
        
        console_text = '\n'.join(self.console_buffer[-self.console_lines:])
        ax_console.text(0.04, 0.76, console_text, 
                       verticalalignment='top',
                       horizontalalignment='left',
                       fontfamily='monospace',
                       fontsize=9,
                       color='#2c3e50',
                       wrap=True)
    

    def render(self, filename='robot_maze.gif', loop=None, pause_duration=5.0, max_frames=500):
        """
        Create and display an animated GIF from all captured frames.

        Args:
            filename: Name of the GIF file to save (default: 'robot_maze.gif')
            loop: Number of times to loop (None = play once, 0 = infinite, 1+ = loop N times, default: None)
            pause_duration: Duration in seconds to hold the final frame (default: 5.0)
            max_frames: Maximum number of frames to render (default: 500)

        Returns:
            The filename of the saved GIF, or None if too many frames
        """
        if not self.frames:
            return None

        # Convert delay to milliseconds for GIF duration
        duration_ms = int(self.delay * 1000)

        # Calculate how many extra frames needed for the pause
        extra_frames = int(pause_duration / self.delay)

        # Calculate total frames
        total_frames = len(self.frames) + extra_frames

        # Check if too many frames
        if total_frames > max_frames:
            print(f"Warning: Too many frames to render ({total_frames} frames). ")
            print(f"Maximum is {max_frames}. Try reducing steps or increasing delay.")
            return None

        # Create frames list with final frame repeated
        frames_to_save = self.frames.copy()
        if extra_frames > 0 and len(self.frames) > 0:
            last_frame = self.frames[-1]
            frames_to_save.extend([last_frame] * extra_frames)

        # Save as GIF - only include loop parameter if specified
        save_kwargs = {
            'save_all': True,
            'append_images': frames_to_save[1:],
            'duration': duration_ms,
            'optimize': False
        }

        if loop is not None:
            save_kwargs['loop'] = loop

        frames_to_save[0].save(filename, **save_kwargs)

        # Display in notebook/Quarto
        if IPYTHON_AVAILABLE:
            display(IPImage(filename=filename))

        # Clear frames for next render, but keep current state as starting frame
        self.frames = []
        self._capture_frame()

        return 
    
    def visualize(self, delay=0.1):
        """Visualize the current state (legacy method for backwards compatibility)."""
        fig = plt.figure(figsize=(5, 6.25))
        ax_maze = plt.subplot2grid((11, 1), (0, 0), rowspan=8)
        ax_console = plt.subplot2grid((11, 1), (8, 0), rowspan=3)
        plt.subplots_adjust(hspace=0.3, left=0.05, right=0.95, top=0.95, bottom=0.05)
        
        self._draw_maze(ax_maze, ax_console)
        
        if self.is_notebook_env and IPYTHON_AVAILABLE:
            display(fig)
            clear_output(wait=True)
        else:
            plt.show()
            plt.close(fig)
        
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
        """Check if the maze has a path from start to target using BFS."""
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
            
            for dx, dy in [(0, -1), (1, 0), (0, 1), (-1, 0)]:
                nx, ny = x + dx, y + dy
                
                if (0 <= nx < self.size and 0 <= ny < self.size and
                    (nx, ny) not in visited and
                    self.maze[ny, nx] != self.WALL):
                    visited.add((nx, ny))
                    queue.append((nx, ny))
        
        return False


def verify_maze_reproducibility(maze_id):
    """Test function to verify maze reproducibility."""
    maze1 = RobotMaze(maze_id=maze_id, auto_visualize=False)
    maze2 = RobotMaze(maze_id=maze_id, auto_visualize=False)
    
    mazes_match = np.array_equal(maze1.maze, maze2.maze)
    
    if mazes_match:
        print(f"SUCCESS: Mazes with ID '{maze_id}' are IDENTICAL")
    else:
        print(f"FAIL: Mazes with ID '{maze_id}' are DIFFERENT")
        print("This should not happen - please report this bug!")
    
    return mazes_match


# Demo
if __name__ == "__main__":
    print("Creating robot maze environment for Quarto...")
    print("\nKey changes:")
    print("  - auto_visualize now defaults to False")
    print("  - Frames are captured automatically during robot operations")
    print("  - Call robot.render() to create and display animated GIF")
    print("  - GIF speed automatically matches robot.delay")
    print("  - Final frame holds for 5 seconds by default")
    print("\nExample usage:")
    print("  robot = RobotMaze(maze_size=10, wall_probability=0.3, delay=0.1)")
    print("  robot.turn('LEFT')")
    print("  robot.move()")
    print("  robot.render()  # Creates and displays robot_maze.gif")
    print("\nCustomize GIF:")
    print("  robot.render(filename='my_robot.gif', pause_duration=3.0)")
    print("="*60)