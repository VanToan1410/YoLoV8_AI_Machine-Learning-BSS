import os
import sys
import logging
import cv2

# =========================================================
# ĐOẠN CODE SỬA LỖI IMPORT (Dán cái này lên đầu file)
# =========================================================
# 1. Lấy đường dẫn tuyệt đối của thư mục chứa file 'import cv2.py'
current_dir = os.path.dirname(os.path.abspath(__file__))

# 2. Thêm đường dẫn này vào đầu danh sách tìm kiếm của Python
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# 3. Kiểm tra xem thư mục backend có thực sự nằm ở đây không
if not os.path.exists(os.path.join(current_dir, "backend")):
    print(f"❌ CẢNH BÁO: Không thấy thư mục 'backend' tại: {current_dir}")
    print("Vui lòng kiểm tra lại vị trí file 'import cv2.py'!")
# =========================================================

# Bây giờ mới thực hiện import
try:
    from backend.utils.mvs_camera import MVSCamera
    print("✅ KẾT NỐI MODULE SUCCESS!")
except ModuleNotFoundError as e:
    print(f"❌ VẪN LỖI IMPORT: {e}")
    print("Hãy đảm bảo bạn đã có file: backend/utils/__init__.py")
except Exception as e:
    print(f"❌ LỖI KHÁC: {e}")

# ... Giữ nguyên phần run_processor phía dưới ...
import logging
import sys
import os
import sys
import os

# Tự động lấy đường dẫn đến thư mục chứa file này (D:\MVA\BSS\BSS)
# giúp Python tìm thấy thư mục 'backend' nằm ngay tại đó
current_path = os.path.dirname(os.path.abspath(__file__))
if current_path not in sys.path:
    sys.path.insert(0, current_path)

# Bây giờ import sẽ hoạt động vì 'backend' nằm trong 'current_path'
try:
    from backend.utils.mvs_camera import MVSCamera
    print("Kết nối module thành công!")
except Exception as e:
    print(f"Lỗi import: {e}")
log = logging.getLogger("bss.processor")

def run_processor(source, camera_id, headless, max_fps):
    # Logic khởi tạo linh hoạt
    if str(source).lower() == "mvs":
        cap = MVSCamera()
    else:
        src = int(source) if str(source).isdigit() else source
        cap = cv2.VideoCapture(src)

    if not cap.isOpened():
        log.error(f"Không thể mở nguồn video: {source}")
        return

    log.info(f"Đang xử lý luồng từ: {source}")

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                log.warning("Không nhận được frame. Đang thử lại...")
                continue

            # --- LOGIC XỬ LÝ XE (YOLO, License Plate, etc.) TẠI ĐÂY ---
            
            if not headless:
                cv2.imshow(f"BSS Camera {camera_id}", frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
    finally:
        cap.release()
        cv2.destroyAllWindows()