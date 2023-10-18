import serial.tools.list_ports
from PyQt5.QtCore import QTimer
from serial import SerialException
import sys
from serial01 import Ui_MainWindow
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QFileDialog, QMessageBox
import _thread
import time
import re

Com_Open_Flag = False  # 串口打开标志
Usb_Open_Flag = False
custom_serial = serial.Serial
Usb_serial = serial.Serial
COM_List = []


# 刷新串口
def port_check(self):
    global COM_List
    COM_List = list(serial.tools.list_ports.comports())  # 获取串口列表
    self.Com_Port.clear()
    self.Com_Port_Usb.clear()
    for i in range(0, len(COM_List)):  # 将列表导入到下拉框
        self.Com_Port.addItem(COM_List[i].description)
        self.Com_Port_Usb.addItem(COM_List[i].name)


# 打开串口
def com_open(self):
    global custom_serial  # 全局变量，需要加global
    global Com_Open_Flag
    if custom_serial.isOpen():
        print("open success")
        Com_Open_Flag = True
        self.Open_Com.setText("关闭串口")
        self.Com_Band.setEnabled(False)  # 串口号和波特率变为不可选择
        self.Com_Port.setEnabled(False)
    else:
        print("open failed")


def usb_open(self):
    global Usb_serial  # 全局变量，需要加global
    global Usb_Open_Flag
    if Usb_serial.isOpen():
        print("open success")
        Usb_Open_Flag = True
        self.Open_Usb.setText("关闭设备")
        self.Com_Band_Usb.setEnabled(False)  # 串口号和波特率变为不可选择
        self.Com_Port_Usb.setEnabled(False)
    else:
        print("open failed")


# 获取串口数据
def Com_Data_Rsv(threadName):
    while True:
        while Com_Open_Flag:
            data = custom_serial.read_all()
            time.sleep(0.1)
            if data == b'':
                continue
            else:
                print("receive : ", data)
                window.Set_Display_Data(data)


def Usb_Data_Rsv(threadName):
    while True:
        while Usb_Open_Flag:
            data = Usb_serial.read_all()
            time.sleep(0.1)
            if data == b'':
                continue
            else:
                print("receive : ", data)
                window.Set_Display_Usb(data)


def savefiles(self):
    dlg = QFileDialog()
    filenames = dlg.getSaveFileName(None, "保存日志文件", None, "Txt files(*.txt)")

    try:
        with open(file=filenames[0], mode='w', encoding='utf-8') as file:
            file.write(self.Data_Display.toPlainText())
    except:
        QMessageBox.critical(self, '日志异常', '保存日志文件失败！')


# 界面UI按键程序重写
class Mywindow(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self):
        super(Mywindow, self).__init__()
        self.setupUi(self)
        port_check(self)
        self.timer_send = QTimer()
        self.timer_send.timeout.connect(self.Send_Data_Click)
        self.SendData_Timer.stateChanged.connect(self.SendData_timer)
        # self.Send_Data_Dsiplay.setPlaceholderText("输入发送数据")
        # self.Data_Display.setPlaceholderText("显示接收数据")

    def refesh_Com_Click(self):
        port_check(self)

    def Open_Com_Click(self):
        global custom_serial  # 全局变量，需要加global
        global Com_Open_Flag

        print("点击了打开串口按钮")
        if self.Open_Com.text() == "打开串口":
            port = COM_List[self.Com_Port.currentIndex()].name
            print(port)
            try:
                custom_serial = serial.Serial(port, int(self.Com_Band.currentText()), timeout=0.5)
                com_open(self)
            except SerialException:
                QMessageBox.critical(self, '串口错误', '串口被占用！')
                print('port already open')
        else:
            Com_Open_Flag = False
            self.Open_Com.setText("打开串口")
            custom_serial.close()
            self.Com_Band.setEnabled(True)  # 串口号和波特率变为可选择
            self.Com_Port.setEnabled(True)

    def Set_Display_Data(self, Data):
        if self.checkBox_3.isChecked():
            s = (time.strftime("[%H:%M:%S]", time.localtime())) + " "
            print(s)
            self.Data_Display.insertPlainText(s)
        try:
            if self.radioButton_2.isChecked():
                self.Data_Display.insertPlainText(str(Data, encoding="utf-8"))
            else:
                hex_str = Data.hex()
                print(hex_str)
                hex_str_upper = hex_str.upper()
                data = re.sub(r'(.{2})', r'\1 ', hex_str_upper)
                self.Data_Display.insertPlainText(data)
        except:
            print("请先打开串口")
        if self.checkBox.isChecked():
            self.Data_Display.insertPlainText('\r\n')

    def Send_Data_Click(self):
        print("点击了发送数据按钮")
        Data_Need_Send = self.Send_Data_Dsiplay.toPlainText()
        try:
            if custom_serial.isOpen():
                if self.checkBox_4.isChecked():
                    msg = self.Send_Command_Dsiplay.toPlainText()
                    Data_Need_Send = msg.replace('<pa>', self.Send_Data_Dsiplay.toPlainText())
                    # Data_Need_Send = self.Send_Command_Display.toPlainText() + self.Send_Data_Display.toPlainText()
                if self.radioButton_4.isChecked():
                    custom_serial.write(Data_Need_Send.encode("gbk"))
                else:
                    hex_data = bytes(Data_Need_Send, encoding="utf-8").hex()
                    print(hex_data)
                    data = bytes.fromhex(hex_data)
                    print(data)
                    custom_serial.write(data)
                if self.checkBox_2.isChecked():
                    window.Set_Display_Data(bytes(Data_Need_Send, encoding="utf-8"))
            else:
                QMessageBox.critical(self, '串口错误', '请先打开串口！')
                print("请先打开串口")
        except:
            QMessageBox.critical(self, '串口错误', '请先打开串口！')
            print("请先打开串口")

    def Open_Usb_click(self):
        global Usb_Open_Flag
        global Usb_serial

        print("点击了打开设备按钮")
        if self.Open_Usb.text() == "打开设备":
            port = COM_List[self.Com_Port_Usb.currentIndex()].name
            print(port)
            try:
                Usb_serial = serial.Serial(port, int(self.Com_Band_Usb.currentText()), timeout=0.5)
                usb_open(self)
            except SerialException:
                QMessageBox.critical(self, '串口错误', '串口被占用！')
                print('port already open')
        else:
            Usb_Open_Flag = False
            self.Open_Usb.setText("打开设备")
            Usb_serial.close()
            self.Com_Band_Usb.setEnabled(True)  # 串口号和波特率变为可选择
            self.Com_Port_Usb.setEnabled(True)

    def Set_Display_Usb(self, Data):
        self.Send_Data_Dsiplay.setPlainText(str(Data, encoding="utf-8"))
        if self.checkBox_5.isChecked():
            self.Send_Data_Click()

    def Send_Data_timer(self):
        self.SendData_timer()

    def Save_Data_Click(self):
        savefiles(self)

    def SendData_timer(self):
        try:
            if 1 <= int(self.spinBox.text()) <= 30000:
                if self.SendData_Timer.isChecked():
                    self.timer_send.start(int(self.spinBox.text()))
                    self.spinBox.setEnabled(False)
                else:
                    self.timer_send.stop()
                    self.spinBox.setEnabled(True)
            else:
                print('定时发送数据周期仅可设置在30秒内！')
        except:
            print('请设置正确的数值类型！')


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = Mywindow()
    window.show()
    _thread.start_new_thread(Com_Data_Rsv, ("Thread-1",))
    _thread.start_new_thread(Usb_Data_Rsv, ("Thread-2",))
    sys.exit(app.exec_())
