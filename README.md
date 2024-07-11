# CodeArt

This project transforms your video into a unique artistic representation using various icons at different brightness levels.

## Installation

To run this project, you'll need to have Python installed on your system. Follow the steps below to get started:

1. Clone the repository:
    ```sh
    git clone https://github.com/derto42/codeart
    ```

2. Navigate to the project directory:
    ```sh
    cd codeart
    ```

3. Install the required dependencies:
    ```sh
    pip install -r requirements.txt
    ```

## Usage

1. Run the script:
    ```sh
    python codeart.py
    ```

2. When prompted, define the box size (1-200), with 200 being a more dense configuration (more boxes).

3. Enter the number of brightness levels and press Enter.

4. Select a video by clicking the "Select video" button.

5. Choose icons for each brightness level by clicking the buttons labeled 1, 2, 3, 4, etc.

6. Use the brightness level sliders to fine-tune the brightness levels for each icon.

7. Press the "Preview" button to get a sample frame of what the processed video will look like.

8. Press the "Start" button to begin processing the entire video.

### Notes

- When creating your own icons, any dimension will work, and any transparency will turn to black.
- When clicking "Start," it may seem like the script isn't working, but it just takes some time if the configuration is complex, so please stay patient.
