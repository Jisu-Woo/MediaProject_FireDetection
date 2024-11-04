from roboflow import Roboflow
import cv2
import base64
import os

api = os.getenv('ROBOFLOW_API_KEY')

rf = Roboflow(api_key=api)
project = rf.workspace("js-0pept").project("fire-detector-fmlk5")
model = project.version(1).model


cctv_url = ""



# 동영상 파일 열기
video = cv2.VideoCapture(cctv_url)

    
base64Frames = [] # 프레임 저장 변수

while video.isOpened():
    success, frame = video.read()
    if not success:
      break
    _, buffer = cv2.imencode(".jpg", frame)
    base64Frames.append(base64.b64encode(buffer).decode("utf-8"))

video.release()
print(len(base64Frames), "프레임을 읽었습니다.")


# infer on a local image
# print(model.predict("D:/TestData_MediaProject/test/1.jpg", confidence=30, overlap=30).json())

# visualize your prediction
# model.predict("D:/TestData_MediaProject/1.jpg", confidence=30, overlap=30).save("D:/TestData_MediaProject/predict/prediction.jpg")

# infer on an image hosted elsewhere
print(model.predict("https://i.imghippo.com/files/yHT6115Nac.jpg", hosted=True, confidence=30, overlap=30).json())


