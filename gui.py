import dearpygui.dearpygui as dpg
import os
import threading
import queue
import time
from contextforge import compile_project
import tkinter as tk
from tkinter import filedialog

dpg.create_context()

# Create a queue for thread-safe communication
message_queue = queue.Queue()

# Flag to control the update thread
running = True

def browse_project(sender, app_data, user_data):
    root = tk.Tk()
    root.withdraw()
    folder_path = filedialog.askdirectory()
    if folder_path:
        dpg.set_value("project_path", folder_path)
        update_full_path()

def browse_output(sender, app_data, user_data):
    root = tk.Tk()
    root.withdraw()
    file_path = filedialog.asksaveasfilename(defaultextension=".txt")
    if file_path:
        dpg.set_value("output_file", file_path)
        update_full_path()

def update_full_path():
    project_path = dpg.get_value("project_path")
    output_file = dpg.get_value("output_file")
    if project_path and output_file:
        if not os.path.isabs(output_file):
            full_path = os.path.join(project_path, output_file)
        else:
            full_path = output_file
        dpg.set_value("full_path", f'Full path: {full_path}')
    else:
        dpg.set_value("full_path", '')

def compile_project_thread(project_path, output_file, output_format, max_file_size):
    try:
        message_queue.put("Starting compilation...\n")
        message_queue.put(f"Project Path: {project_path}\n")
        message_queue.put(f"Output File: {output_file}\n")
        message_queue.put(f"Output Format: {output_format}\n")
        message_queue.put(f"Max File Size: {max_file_size} bytes\n")

        compile_project(project_path, output_file, output_format, max_file_size)
        
        message_queue.put("Compilation completed successfully.")
    except Exception as e:
        message_queue.put(f"Compilation failed: {str(e)}")

def compile_project_callback(sender, app_data, user_data):
    project_path = dpg.get_value("project_path")
    output_file = dpg.get_value("output_file")
    output_format = dpg.get_value("output_format")
    max_file_size = dpg.get_value("max_file_size")

    if not project_path:
        dpg.set_value("output", "Error: Please specify a project path.")
        return

    dpg.set_value("output", "")  # Clear output
    threading.Thread(target=compile_project_thread, args=(project_path, output_file, output_format, max_file_size)).start()

def clear_output(sender, app_data, user_data):
    dpg.set_value("output", "")

def update_output_thread():
    while running:
        if not message_queue.empty():
            messages = []
            while not message_queue.empty():
                messages.append(message_queue.get_nowait())
            
            # Update GUI in the main thread
            dpg.run_in_main_thread(update_gui, messages)
        time.sleep(0.1)  # Sleep to prevent high CPU usage

def update_gui(messages):
    current_text = dpg.get_value("output")
    for message in messages:
        current_text += message + "\n"
    dpg.set_value("output", current_text)

with dpg.window(label="ContextForge GUI", tag="primary_window"):
    with dpg.group(horizontal=True):
        dpg.add_input_text(label="Project Path", tag="project_path", width=300)
        dpg.add_button(label="Browse", callback=browse_project)
    
    with dpg.group(horizontal=True):
        dpg.add_input_text(label="Output File", tag="output_file", width=300)
        dpg.add_button(label="Browse", callback=browse_output)
    
    dpg.add_text(tag="full_path")
    
    dpg.add_combo(label="Output Format", items=['markdown', 'html', 'json', 'xml'], default_value='markdown', tag="output_format")
    dpg.add_input_int(label="Max File Size (bytes)", default_value=1000000, tag="max_file_size")
    
    with dpg.group(horizontal=True):
        dpg.add_button(label="Compile Project", callback=compile_project_callback)
        dpg.add_button(label="Clear Output", callback=clear_output)
    
    dpg.add_input_text(multiline=True, readonly=True, tag="output", height=200, width=-1)

# Start the update thread
update_thread = threading.Thread(target=update_output_thread, daemon=True)
update_thread.start()

dpg.create_viewport(title='ContextForge GUI', width=600, height=400)
dpg.setup_dearpygui()
dpg.set_primary_window("primary_window", True)

dpg.show_viewport()
dpg.start_dearpygui()

# Signal the update thread to stop
running = False
update_thread.join()

dpg.destroy_context()