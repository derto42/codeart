import cv2
import numpy as np
from tkinter import filedialog, messagebox
from tkinter import Tk, Label, Button, StringVar, Toplevel, Frame, Scale, HORIZONTAL, Canvas, Scrollbar, VERTICAL
from PIL import Image, ImageTk
from moviepy.editor import ImageSequenceClip

class Application:
    def __init__(self, window, num_levels):
        self.window = window
        self.window.geometry("450x500")  # Width x Height
        self.video_file = StringVar()
        self.icon_files = [StringVar() for _ in range(num_levels)]
        self.icon_previews = [Label(window) for _ in range(num_levels)]
        self.brightness_levels = [(i * (256 // num_levels)) for i in range(num_levels)]

        # Adding a scrollbar
        self.canvas = Canvas(window)
        self.scrollbar = Scrollbar(window, command=self.canvas.yview)
        self.scrollable_frame = Frame(self.canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(
                scrollregion=self.canvas.bbox("all")
            )
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.grid_size = Scale(self.scrollable_frame, from_=1, to=200, orient=HORIZONTAL, length=400)
        self.grid_size.set(70)
        self.grid_size.bind("<ButtonRelease-1>", lambda event: self.attempt_preview_update())
        self.grid_size.pack()

        self.preview_window = Toplevel(self.window)
        self.preview_window.protocol('WM_DELETE_WINDOW', self.hide_preview)
        self.preview_window.withdraw()
        self.preview_window.resizable(False, False)
        self.preview_label = Label(self.preview_window)
        self.preview_label.pack()

        self.select_video_button = Button(self.scrollable_frame, text="Select video", command=self.select_video)
        self.select_video_button.pack()

        self.video_label = Label(self.scrollable_frame, text="")
        self.video_label.pack()

        self.icon_frame = Frame(self.scrollable_frame)
        self.icon_frame.pack()

        # Setting up grid wrapping for icons
        icons_per_row = 5
        for i in range(num_levels):
            level_frame = Frame(self.icon_frame)
            button = Button(level_frame, text=f"Icon {i + 1}", command=lambda i=i: self.select_icon(i))
            button.pack(side="top")
            self.icon_previews[i] = Label(level_frame)
            self.icon_previews[i].pack(side="bottom")
            level_frame.grid(row=i // icons_per_row, column=i % icons_per_row, padx=5, pady=5)

        for i in range(num_levels):
            slider_frame = Frame(self.scrollable_frame)
            level_label = Label(slider_frame, text=str(i + 1))
            level_label.pack(side="left")

            scale = Scale(slider_frame, from_=0, to=255, orient=HORIZONTAL, length=400)
            scale.set(self.brightness_levels[i])
            scale.bind("<ButtonRelease-1>", lambda event, i=i, scale=scale: self.update_brightness_level(i, scale.get()))
            scale.pack(side="right")

            slider_frame.pack()

        self.preview_button = Button(self.scrollable_frame, text="Preview", command=self.show_preview)
        self.preview_button.pack()

        self.start_button = Button(self.scrollable_frame, text="Start", command=self.start_processing)
        self.start_button.pack()

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

    def hide_preview(self):
        self.preview_window.withdraw()

    def show_preview(self):
        if not self.video_file.get():
            messagebox.showerror("Error", "Please select a video file.")
            return
        if not all(icon.get() for icon in self.icon_files):
            messagebox.showerror("Error", "Please select all icon files.")
            return
        self.preview_window.deiconify()
        self.preview_window.geometry("")
        self.attempt_preview_update()

    def select_video(self):
        filename = filedialog.askopenfilename()
        if filename:
            self.video_file.set(filename)
            self.video_label.config(text=filename.split("/")[-1])
            self.attempt_preview_update()

    def select_icon(self, level):
        filename = filedialog.askopenfilename()
        if filename:
            self.icon_files[level].set(filename)
            icon_preview = Image.open(filename)
            icon_preview.thumbnail((25, 25), Image.LANCZOS)
            tk_icon_preview = ImageTk.PhotoImage(icon_preview)
            self.icon_previews[level].config(image=tk_icon_preview)
            self.icon_previews[level].image = tk_icon_preview
            self.attempt_preview_update()

    def update_brightness_level(self, level, value):
        self.brightness_levels[level] = int(value)
        self.attempt_preview_update()

    def attempt_preview_update(self):
        if self.preview_window.state() == 'normal':  # Check if the preview window is visible
            if self.video_file.get() and all(icon.get() for icon in self.icon_files):
                self.preview_frame()

    def preview_frame(self):
        if not self.video_file.get():
            return  # No video file selected
        vid = cv2.VideoCapture(self.video_file.get())
        if not vid.isOpened():
            return  # Failed to open video
        total_frames = int(vid.get(cv2.CAP_PROP_FRAME_COUNT))
        vid.set(cv2.CAP_PROP_POS_FRAMES, total_frames // 2)  # Set position to the middle frame

        ret, frame = vid.read()
        vid.release()
        if ret:
            frame = process_frame_from_array(frame, [icon.get() for icon in self.icon_files if icon.get()], self.brightness_levels, self.grid_size.get())
            preview = Image.fromarray(frame)
            preview.thumbnail((800, 800), Image.LANCZOS)
            tkimage = ImageTk.PhotoImage(preview)

            self.preview_label.config(image=tkimage)
            self.preview_label.image = tkimage
            self.preview_window.geometry(f"{tkimage.width()}x{tkimage.height()}")

        vid.release()

    def start_processing(self):
        if not self.video_file.get():
            messagebox.showerror("Error", "Please select a video file.")
            return
        if not all(icon.get() for icon in self.icon_files):
            messagebox.showerror("Error", "Please select all icon files.")
            return
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
