import pandas as pd
import numpy as np
from tqdm import tqdm
import cv2
import os

def GaussianMask(sizex, sizey, sigma=33, center=None, fix=1):
    x = np.arange(0, sizex, 1, float)
    y = np.arange(0, sizey, 1, float)
    x, y = np.meshgrid(x, y)

    if center is None:
        x0 = sizex // 2
        y0 = sizey // 2
    else:
        if not np.isnan(center[0]) and not np.isnan(center[1]):
            x0 = center[0]
            y0 = center[1]
        else:
            return np.zeros((sizey, sizex))

    return fix * np.exp(-4 * np.log(2) * ((x - x0) ** 2 + (y - y0) ** 2) / sigma ** 2)


def Fixpos2Densemap(fix_arr, width, height, img_file=None, alpha=0.5, threshold=10):
    heatmap_ = np.zeros((height, width), np.float32)

    for n_subject in tqdm(range(fix_arr.shape[0])):
        x, y = fix_arr[n_subject]
        heatmap_ += GaussianMask(width, height, sigma=25, center=(x, y), fix=1)

    # Normalize
    if np.amax(heatmap_) != 0:
        heatmap_ = heatmap_ / np.amax(heatmap_)
        heatmap_ = heatmap_ * 255

    heatmap_ = heatmap_.astype("uint8")

    if img_file is not None:
        h, w, _ = img_file.shape
        heatmap_ = cv2.resize(heatmap_, (w, h))
        heatmap_color = cv2.applyColorMap(heatmap_, cv2.COLORMAP_JET)

        mask = np.where(heatmap_ <= threshold, 1, 0)
        mask = np.reshape(mask, (h, w, 1))
        mask = np.repeat(mask, 3, axis=2)

        merged = img_file * mask + heatmap_color * (1 - mask)
        merged = merged.astype("uint8")
        merged = cv2.addWeighted(img_file, 1 - alpha, merged, alpha, 0)

        return merged
    else:
        return cv2.applyColorMap(heatmap_, cv2.COLORMAP_JET)


def generate_heatmaps(username, img_path='newspp.jpg', csv_file='gazedataeye.csv', output_folder='static/heatmaps'):
    df = pd.read_csv(csv_file)

    try:
        user_data = df[df['username'] == int(username)]
    except:
        user_data = df[df['username'].astype(str) == username]

    img_file = cv2.imread(img_path)

    if user_data.empty:
        print(f"[ERROR] No data for user {username}")
        return None

    if img_file is None:
        print(f"[ERROR] Image file {img_path} not found!")
        return None

    H, W, _ = img_file.shape

    user_data['gaze_x'] = user_data['gaze_x'] - user_data['gaze_x'].min()
    user_data['gaze_y'] = user_data['gaze_y'] - user_data['gaze_y'].min()

    if user_data['gaze_x'].max() > 0:
        user_data['gaze_x'] = user_data['gaze_x'] / user_data['gaze_x'].max() * W
    else:
        user_data['gaze_x'] = 0

    if user_data['gaze_y'].max() > 0:
        user_data['gaze_y'] = user_data['gaze_y'] / user_data['gaze_y'].max() * H
    else:
        user_data['gaze_y'] = 0

    fix_arr = user_data[['gaze_x', 'gaze_y']].values.astype(np.float64)

    heatmap = Fixpos2Densemap(fix_arr, W, H, img_file=img_file, alpha=0.7, threshold=5)

    # Ensure output directory exists
    os.makedirs(output_folder, exist_ok=True)

    output_filename = f"{output_folder}/heatmap_user_{username}.png"
    cv2.imwrite(output_filename, heatmap)

    print(f"[INFO] Heatmap saved at: {output_filename}")
    return output_filename

# ---------- Main entry point (for direct running) ---------- #
if __name__ == '__main__':
    # Example usage
    sample_username = '11224498'
    heatmap_path = generate_heatmaps(sample_username)

    if heatmap_path:
        print(f"[SUCCESS] Heatmap generated: {heatmap_path}")
    else:
        print("[FAILURE] Could not generate heatmap.")
