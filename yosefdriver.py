from rose.common import actions
import pynput.keyboard as keyboard
import threading

# Set the driver's name
driver_name = "Michael Schumacher"

# Initialize variables to track the car's movement
current_action = actions.NONE
exit_flag = False

# Define key event handlers
def on_press(key):
    global current_action, exit_flag
    try:
        if key.char == 'a':
            current_action = actions.LEFT
        elif key.char == 'd':
            current_action = actions.RIGHT
        elif key.char == 'w':
            current_action = actions.NONE  # Move forward
    except AttributeError:
        if key == keyboard.Key.space:
            current_action = actions.JUMP
        elif key == keyboard.Key.esc:
            exit_flag = True

# Define the drive function
def drive(world):
    global current_action
    action_to_take = current_action
    current_action = actions.NONE  # Reset action after taking it
    return action_to_take

# Main function to keep the script running and process keyboard events
def main_loop():
    global exit_flag
    print("Press 'A', 'D', 'W', or 'SPACE' to control the car. Press 'ESC' to exit.")
    with keyboard.Listener(on_press=on_press) as listener:
        while not exit_flag:
            time.sleep(0.1)
        listener.stop()

# Run the main loop in a separate thread to avoid blocking the drive function
threading.Thread(target=main_loop).start()
