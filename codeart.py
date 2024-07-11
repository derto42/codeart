import cv2
import numpy as np
from tkinter import filedialog
from tkinter import Tk, Label, Button, StringVar, Toplevel, Frame, Scale, HORIZONTAL
from PIL import Image, ImageTk
from moviepy.editor import ImageSequenceClip

class Application:
    def __init__(self, window, num_levels):
        self.window = window
        self.video_file = StringVar()
        self.icon_files = [StringVar() for _ in range(num_levels)]
        self.icon_previews = [Label(window) for _ in range(num_levels)]  # Create label widgets for icon previews
        self.brightness_levels = [(i * (256 // num_levels)) for i in range(num_levels)]
        self.brightness_scales = [0] * num_levels  # This line is new
        self.grid_size = Scale(window, from_=1, to=200, orient=HORIZONTAL, length=400)
        self.grid_size.set(70)  # set initial value
        self.grid_size.pack()

        self.preview_window = Toplevel(self.window)
        self.preview_window.protocol('WM_DELETE_WINDOW', self.hide_preview)  # override 'x' button functionality
        self.preview_window.withdraw()  # Hide the window until we have something to preview
        self.preview_label = Label(self.preview_window)
        self.preview_label.pack()

        self.select_video_button = Button(window, text="Select video", command=self.select_video)
        self.select_video_button.pack()

        self.icon_frame = Frame(window)  # Create a frame to hold the icon buttons and previews
        self.icon_frame.pack()

        for i in range(num_levels):
            level_frame = Frame(self.icon_frame)  # Create a frame for each level
            button = Button(level_frame, text=str(i + 1), command=lambda i=i: self.select_icon(i))  # Button just shows the level number
            button.pack(side="top")  # Pack button at the top of level_frame
            self.icon_previews[i] = Label(level_frame)  # Set the parent of the label to level_frame
            self.icon_previews[i].pack(side="bottom")  # Pack the label widget for icon preview under the button
            level_frame.pack(side="left")  # Pack each level frame side by side

        for i in range(num_levels):
            slider_frame = Frame(window)  # Create a frame to hold the slider and its associated number
            level_label = Label(slider_frame, text=str(i + 1))  # Label to display the level number
            level_label.pack(side="left")  # Pack the label to the left inside the slider_frame

            scale = Scale(slider_frame, from_=0, to=255, orient=HORIZONTAL, command=self.update_brightness_level(i), length=400)
            scale.set(self.brightness_levels[i])  # Set the initial value
            scale.pack(side="right")  # Pack the slider to the right inside the slider_frame

            self.brightness_scales[i] = scale

            slider_frame.pack()  # Pack the entire slider_frame into the main window

        self.preview_button = Button(window, text="Preview", command=self.preview_frame)
        self.preview_button.pack()

        self.start_button = Button(window, text="Start", command=self.start_processing)
        self.start_button.pack()

    def hide_preview(self):
        self.preview_window.withdraw()

    def select_video(self):
        self.video_file.set(filedialog.askopenfilename())

    def select_icon(self, level):
        self.icon_files[level].set(filedialog.askopenfilename())
        # Update icon preview
        icon_preview = Image.open(self.icon_files[level].get())
        icon_preview.thumbnail((25, 25), Image.LANCZOS)  # Use Image.LANCZOS instead of Image.ANTIALIAS
        tk_icon_preview = ImageTk.PhotoImage(icon_preview)
        self.icon_previews[level].config(image=tk_icon_preview)
        self.icon_previews[level].image = tk_icon_preview

    def update_brightness_level(self, level):
        def update(val):
            self.brightness_levels[level] = int(val)
        return update

    def preview_frame(self):
        vid = cv2.VideoCapture(self.video_file.get())
        total_frames = int(vid.get(cv2.CAP_PROP_FRAME_COUNT))
        vid.set(cv2.CAP_PROP_POS_FRAMES, total_frames // 2)  # set position to the middle frame

        ret, frame = vid.read()
        if ret:
            frame = process_frame_from_array(frame, [icon_file.get() for icon_file in self.icon_files], self.brightness_levels, self.grid_size.get())
            preview = Image.fromarray(frame)
            preview.thumbnail((800, 800), Image.LANCZOS)  # Use Image.LANCZOS instead of Image.ANTIALIAS
            tkimage = ImageTk.PhotoImage(preview)

            self.preview_label.config(image=tkimage)
            self.preview_label.image = tkimage
            self.preview_window.deiconify()  # Show the window

        vid.release()

    def start_processing(self):
        save_path = filedialog.asksaveasfilename(defaultextension=".mp4", filetypes=[("MP4 files", "*.mp4"), ("All files", "*.*")])
        if save_path:
            frame_list = process_video(self.video_file.get(), [icon_file.get() for icon_file in self.icon_files], self.brightness_levels, self.grid_size.get())

            clip = ImageSequenceClip(frame_list, fps=24)
            clip.write_videofile(save_path, codec='libx264')

def get_icon(value, icons, brightness_levels):
    for i in range(len(brightness_levels) - 1, -1, -1):
        if value > brightness_levels[i]:
            return icons[i]
    return icons[0]

def process_frame(file_path, icon_paths, brightness_levels, grid_width):
    vid = cv2.VideoCapture(file_path)
    width = int(vid.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(vid.get(cv2.CAP_PROP_FRAME_HEIGHT))

    cell_width = width // grid_width
    cell_height = cell_width  # Make this the same as cell_width for square cells
    grid_height = height // cell_height  # Calculate grid height based on cell height

    # load icons and resize to cell size
    icon_images = [np.array(Image.open(icon_path).convert('RGB').resize((cell_width, cell_height))) for icon_path in icon_paths]

    ret, frame = vid.read()
    if ret:
        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # process each cell
        for i in range(0, height, cell_height):
            for j in range(0, width, cell_width):
                h = cell_height if i + cell_height <= height else height - i
                w = cell_width if j + cell_width <= width else width - j
                icon = get_icon(np.average(gray_frame[i:i+h, j:j+w]), icon_images, brightness_levels)
                frame[i:i+h, j:j+w] = cv2.resize(icon, (w, h))

    vid.release()
    return frame

def process_frame_from_array(frame, icon_paths, brightness_levels, grid_width):
    height, width = frame.shape[:2]

    cell_width = width // grid_width
    cell_height = cell_width  # Make this the same as cell_width for square cells
    grid_height = height // cell_height  # Calculate grid height based on cell height

    # load icons and resize to cell size
    icon_images = [np.array(Image.open(icon_path).convert('RGB').resize((cell_width, cell_height))) for icon_path in icon_paths]

    gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # process each cell
    for i in range(0, height, cell_height):
        for j in range(0, width, cell_width):
            h = cell_height if i + cell_height <= height else height - i
            w = cell_width if j + cell_width <= width else width - j
            icon = get_icon(np.average(gray_frame[i:i+h, j:j+w]), icon_images, brightness_levels)
            frame[i:i+h, j:j+w] = cv2.resize(icon, (w, h))

    return frame

def process_video(file_path, icon_paths, brightness_levels, grid_width):
    vid = cv2.VideoCapture(file_path)
    width = int(vid.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(vid.get(cv2.CAP_PROP_FRAME_HEIGHT))

    cell_width = width // grid_width
    cell_height = cell_width  # Make this the same as cell_width for square cells
    grid_height = height // cell_height  # Calculate grid height based on cell height

    frame_list = []  # Define frame_list here

    # load icons and resize to cell size
    icon_images = [np.array(Image.open(icon_path).convert('RGB').resize((cell_width, cell_height))) for icon_path in icon_paths]

    while vid.isOpened():
        ret, frame = vid.read()
        if not ret:
            break

        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # process each cell
        for i in range(0, height, cell_height):
            for j in range(0, width, cell_width):
                h = cell_height if i + cell_height <= height else height - i
                w = cell_width if j + cell_width <= width else width - j
                icon = get_icon(np.average(gray_frame[i:i+h, j:j+w]), icon_images, brightness_levels)
                frame[i:i+h, j:j+w] = cv2.resize(icon, (w, h))

        frame_list.append(frame)  # Add frame to the list

    vid.release()
    return frame_list

def main():
    num_levels = int(input("Enter number of brightness levels: "))
    root = Tk()
    app = Application(root, num_levels)
    root.mainloop()

if __name__ == "__main__":
    main()
