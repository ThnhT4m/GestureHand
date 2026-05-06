#  Gesture Hand Recognition

Hệ thống nhận diện cử chỉ tay sử dụng **MediaPipe + OpenCV + Python** để điều khiển thiết bị (ESP32).
---
## Thông tin
* Code nhúng vào ESP32 được upload và build trên PlatformIO.
---

## 📸 Demo

![Demo](images/demo1.jpg)

---

## 🎯 Tính năng

* Nhận diện ngón tay theo thời gian thực
* Gửi dữ liệu qua socket tới ESP32

---

## ⚙️ Công nghệ sử dụng

* Python
* OpenCV
* MediaPipe
* Socket (UDP)
* ESP32

---
## 🔧 Cách lắp đặt cánh tay

### Bước 1
![Bước 1](images/cre1.jpg)

### Bước 2
![Bước 2](images/cre2.jpg)

### Bước 3
![Bước 3](images/cre3.jpg)

### Bước 4
![Bước 4](images/cre4.jpg)

### Bước 5
![Bước 5](images/cre5.jpg)

### Bước 6
![Bước 6](images/cre6.jpg)

### Bước 7
![Bước 7](images/cre7.jpg)

### Bước 8
![Bước 8](images/cre8.jpg)

---
## 🚀 Cài đặt 

```bash
pip install opencv-python mediapipe numpy
```
* thêm thư viện json vào file platformio.ini
```bash
lib_deps =
    bblanchon/ArduinoJson
```

---

## ▶️ Chạy chương trình

```bash
python hand_tracking.py
```

---

## 📡 Kết nối ESP32

* IP: `192.168.1.xxx`
* Port: `4210`

---

## 👨‍💻 Tác giả

* ThnhT4m
