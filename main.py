from PyQt5.QtWidgets import QMainWindow,QApplication,QFileDialog
from PyQt5 import uic
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import QFile, QTextStream
from PyQt5.QtCore import QTimer
import cv2
import imutils
import math
import time
import numpy as np
import os
import sys
traffic_record_folder_name = "TrafficRecord"
if not os.path.exists(traffic_record_folder_name):
    os.makedirs(traffic_record_folder_name)
    os.makedirs(traffic_record_folder_name+"//exceeded")
speed_record_file_location = traffic_record_folder_name + "//SpeedRecord.txt"
file = open(speed_record_file_location, "w")
file.write("ID \t SPEED\n------\t-------\n")
file.close() 
class EuclideanDistTracker:
    def __init__(self):
        self.center_points = {}
        self.id_count = 0
        # self.start = 0
        # self.stop = 0
        self.et = 0
        self.s1 = np.zeros((1, 1000))
        self.s2 = np.zeros((1, 1000))
        self.s = np.zeros((1, 1000))
        self.f = np.zeros(1000)
        self.capf = np.zeros(1000)
        self.count = 0
        self.exceeded = 0

    def update(self, objects_rect):
        objects_bbs_ids = []

        # lấy tâm vật
        for rect in objects_rect:
            x, y, w, h = rect
            cx = (x+x+w)/2
            cy = y+h/2

            # kiểm tra vật thể đã detect chưa
            same_object_detected = False

            for id, pt in self.center_points.items():
                dist = math.hypot(cx - pt[0], cy - pt[1])

                if dist < 70:
                    self.center_points[id] = (cx, cy)
                    objects_bbs_ids.append([x, y, w, h, id])
                    same_object_detected = True
                    # bắt đầu đếm giờ
                    if (y >= 410 and y <= 430):
                        self.s1[0, id] = time.time()

                    # dừng đếm giờ và tính hiệu
                    if (y >= 235 and y <= 255):
                        self.s2[0, id] = time.time()
                        self.s[0, id] = self.s2[0, id] - self.s1[0, id]
                    if (y<235):
                        self.f[id]=1
                   
            # detect object mới
            if same_object_detected is False and (y>=235):
                self.center_points[self.id_count] = (cx, cy)
                objects_bbs_ids.append([x, y, w, h, self.id_count])
                self.id_count += 1
                self.s[0, self.id_count] = 0
                self.s1[0, self.id_count] = 0
                self.s2[0, self.id_count] = 0

        # nhập dữ liệu của center mới vào list
        new_center_points = {}
        for obj_bb_id in objects_bbs_ids:
            _, _, _, _, object_id = obj_bb_id
            center = self.center_points[object_id]
            new_center_points[object_id] = center
        self.center_points = new_center_points.copy()
        return objects_bbs_ids
    # hàm tính speed
    def getsp(self, id):
        if (self.s[0, id] != 0):
            s = 214.15 / self.s[0, id]
        else:
            s = 0
        return int(s)
    # lưu dữ liệu
    def capture(self, img, x, y, h, w, sp, id):
        if (self.capf[id] == 0):
            self.capf[id] = 1
            self.f[id] = 0
            crop_img = img[y - 5:y + h + 5, x - 5:x + w + 5]
            n = str(id) + "_speed_" + str(sp)
            file = traffic_record_folder_name + '//' + n + '.jpg'
            cv2.imwrite(file, crop_img)
            self.count += 1
            filet = open(speed_record_file_location, "a")
            if (sp > limit):
                file2 = traffic_record_folder_name + '//exceeded//' + n + '.jpg'
                cv2.imwrite(file2, crop_img)
                filet.write(str(id) + " \t " + str(sp) + "<---exceeded\n")
                self.exceeded += 1
            else:
                filet.write(str(id) + " \t " + str(sp) + "\n")
            filet.close()
    # nhập tổng kết vào text file
    def end(self):
        file = open(speed_record_file_location, "a")
        file.write("\n-------------\n")
        file.write("-------------\n")
        file.write("SUMMARY\n")
        file.write("-------------\n")
        file.write("Total Vehicles :\t" + str(self.count) + "\n")
        file.write("Exceeded speed limit :\t" + str(self.exceeded))
        file.close()
class UI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.login=uic.loadUi("login.ui")
        self.login.show()
        self.main=uic.loadUi("main.ui")
        self.login.btn_start.clicked.connect(lambda:self.CHANGE_UI("main"))
        self.main.out.clicked.connect(lambda:self.LOGOUT_UI("login"))
        self.main.output.clicked.connect(lambda:self.OUTPUT_TEXT("text"))
        self.main.get_limit.clicked.connect(self.RUN)
        self.login.btn_END.clicked.connect(self.END)
        self.main.choose_car.clicked.connect(self.showDialog)
    def showDialog(self):
        self.main.label_5.setScaledContents(True) # Thiết lập label fit với kích thước ảnh
        # Hiển thị hộp thoại để chọn tệp ảnh
        link= r"C:\Users\Nam Blue\Desktop\XLA\XLA\Python\final\Giaodien\Giaodienfinal\TrafficRecord\exceeded"
        fname = QFileDialog.getOpenFileName(self, '', link, 'Image files (*.jpg *.png *.jpeg)')[0]
        # Nếu người dùng đã chọn tệp ảnh
        if fname:
            pixmap = QPixmap(fname) # Tạo QPixmap từ tệp ảnh
            self.main.label_5.setPixmap(pixmap) # Hiển thị QPixmap trên label
    def END(self):
        sys.exit()
    def CHANGE_UI(self,i):
        if i == "main":
            self.login.hide()
            self.main.show()
    def LOGOUT_UI(self,h):
        if h == "login":
            self.login.show()
            self.main.hide()
    def OUTPUT_TEXT(self,g):
        if g == "text":
            filetxt= r"C:\Users\Nam Blue\Desktop\XLA\XLA\Python\final\Giaodien\Giaodienfinal\TrafficRecord\SpeedRecord.txt"
            self.main.file = QFile(filetxt)
            self.main.file.open(QFile.ReadOnly | QFile.Text)
            self.main.stream = QTextStream(self.main.file)
        # Khởi tạo QTimer và kết nối với hàm xử lý update_file
            self.main.timer = QTimer()
            self.main.timer.timeout.connect(self.update_file)
            self.main.timer.start(1000) # cập nhật liên tục sau mỗi giây
    def update_file(self):
                    if self.main.file.isOpen() and not self.main.file.atEnd():
                        self.main.file.reset()
                        content = self.main.stream.readAll()
                        self.main.textEdit.setText(content)
    def RUN(self):
            global limit
            limit = self.main.text_edit.toPlainText()
            limit=int(limit)
            end = 0
            #gọi class
            tracker = EuclideanDistTracker()
            traffic_record_folder_name = "TrafficRecord"
            if not os.path.exists(traffic_record_folder_name):
                os.makedirs(traffic_record_folder_name)
                os.makedirs(traffic_record_folder_name+"//exceeded")
            speed_record_file_location = traffic_record_folder_name + "//SpeedRecord.txt"
            file = open(speed_record_file_location, "w")
            file.write("ID \t SPEED\n------\t-------\n")
            file.close()
            video=r"C:\Users\Nam Blue\Desktop\XLA\XLA\Python\final\traffic4.mp4"
            cap = cv2.VideoCapture(video)
            #detect vật thể
            object_detector = cv2.createBackgroundSubtractorMOG2(history=None,varThreshold=None)
            #100,5
            #KERNALS
            kernalOp = np.ones((3,3),np.uint8)
            kernalOp2 = np.ones((5,5),np.uint8)
            kernalCl = np.ones((11,11),np.uint8)
            fgbg=cv2.createBackgroundSubtractorMOG2(detectShadows=True)
            kernal_e = np.ones((5,5),np.uint8)
            while True:
                ret,frame = cap.read()
                if not ret:
                    break
                frame = cv2.resize(frame, None, fx=0.5, fy=0.5)
                height,width,_ = frame.shape
                #print(height,width)
                #540,960
                #xác định ROI
                roi = frame[50:540,200:960]
                #mask vật thể
                fgmask = fgbg.apply(roi)
                ret, imBin = cv2.threshold(fgmask, 200, 255, cv2.THRESH_BINARY)
                mask1 = cv2.morphologyEx(imBin, cv2.MORPH_OPEN, kernalOp)
                mask2 = cv2.morphologyEx(mask1, cv2.MORPH_CLOSE, kernalCl)
                e_img = cv2.erode(mask2, kernal_e)
                contours,_ = cv2.findContours(e_img,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)
                detections = []
                for cnt in contours:
                    area = cv2.contourArea(cnt)
                    #THRESHOLD
                    if area > 1000 :
                        x,y,w,h = cv2.boundingRect(cnt)
                        cv2.rectangle(roi,(x,y),(x+w,y+h),(0,255,0),3)
                        detections.append([x,y,w,h])
                #hiển thị ID, cập nhập object
                boxes_ids = tracker.update(detections)
                for x,y,w,h,id in boxes_ids:                   
                    if(tracker.getsp(id)<limit):
                        cv2.putText(roi,str(id)+" "+str(tracker.getsp(id)),(x,y-15), cv2.FONT_HERSHEY_PLAIN,1,(255,255,0),2)
                        cv2.rectangle(roi, (x, y), (x + w, y + h), (0, 255, 0), 3)
                    else:
                        cv2.putText(roi,str(id)+ " "+str(tracker.getsp(id)),(x, y-15),cv2.FONT_HERSHEY_PLAIN, 1,(0, 0, 255),2)
                        cv2.rectangle(roi, (x, y), (x + w, y + h), (0, 165, 255), 3)
                    s = tracker.getsp(id)
                    if (tracker.f[id] == 1 and s != 0):
                        tracker.capture(roi, x, y, h, w, s, id)
                # vẽ đường
                cv2.line(roi, (0, 410), (960, 410), (0, 0, 255), 2)
                cv2.line(roi, (0, 430), (960, 430), (0, 0, 255), 2)
                cv2.line(roi, (0, 235), (960, 235), (0, 0, 255), 2)
                cv2.line(roi, (0, 255), (960, 255), (0, 0, 255), 2)
                #cv2.imshow("Mask",mask2)
                #cv2.imshow("Erode", e_img)
                cv2.imshow("ROI", roi)
                key = cv2.waitKey(80)
                if key==27:
                    tracker.end()
                    end=1
                    break
            if(end!=1):
                tracker.end()
            cap.release()
            cv2.destroyAllWindows()
if __name__ == "__main__":
    app=QApplication([])
    ui=UI()
    app.exec_()

