import matplotlib

from scistag.vislog import VisualLog
from scistag.logstag.console_stag import Console
from scistag.mediastag.camera_cv2 import CameraCv2

matplotlib.use('Agg')
import matplotlib.pyplot as plt

plt.plot([5, 4])

cv2_cam = CameraCv2(0)
cv2_cam.start()
time_stamp = 0.0

vl = VisualLog("./livelog", "Report", refresh_time_s=1.0 / 30).default_builder
console = Console()
console.progressive = True
vl.target_log.add_console(console)
vl.target_log.log_txt_images = True
frame_counter = 0
vl.add_text_widget("# Webcam Demo")
progress = vl.add_progress_bar(0, -1, "Receiving frames")
progress_2 = vl.add_progress_bar(0.0, 1.0, "Receiving frames")
camera_image = vl.add_image_widget()
while True:
    vl.target_log.set_log_limit(10)
    time_stamp, image = cv2_cam.get_image(timestamp=time_stamp)
    if image is None:
        continue
    image = image.resized_ext(max_size=vl.max_fig_size)
    camera_image.update_image(image)
    frame_counter += 1
    if frame_counter % 5 == 0:
        vl.log(f"Counter: {frame_counter}")
        pass
    progress.update((frame_counter % 200) / 200.0)
    progress_2.update((frame_counter % 200) / 200.0)
