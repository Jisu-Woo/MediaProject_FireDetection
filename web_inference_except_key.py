from datetime import datetime
from roboflow import Roboflow
import cv2
import base64
import os
import requests
import json
from PIL import Image
from io import BytesIO
import time
import boto3
import tempfile
import yt_dlp
import gradio as gr


def is_fire(classes) -> bool:
    return "fire" in classes or "smoke" in classes


def process_video(youtube_url=None, video_file=None):
    # ROBOFLOW 설정
    api = os.getenv("ROBOFLOW_API_KEY")
    rf = Roboflow(api_key=api)
    project = rf.workspace("WORKSPACE_NAME").project("PROJECT_NAME")
    model = project.version("VERSION_NUMBER").model
    confidence = 20

    # kakao access_token 입력 (kakao_access_token.py로 발급하기)
    access_token = "KAKAO_API_ACCESS_TOKEN"

    video_path = None

    # YouTube URL을 통해 영상을 가져오는 경우
    if youtube_url:
        ydl_opts = {
            "format": "best",
            "outtmpl": tempfile.NamedTemporaryFile(suffix=".mp4").name,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(youtube_url, download=True)
            video_path = ydl.prepare_filename(info_dict)

    # 로컬 비디오 파일을 가져오는 경우
    elif video_file:
        video_path = video_file

    if not video_path:
        return "비디오를 열 수 없습니다."

    video = cv2.VideoCapture(video_path)
    base64Frames = []  # 프레임 저장 변수

    cnt = 0
    while video.isOpened():
        fps = video.get(cv2.CAP_PROP_FPS)
        frame_count = video.get(cv2.CAP_PROP_FRAME_COUNT)
        success, frame = video.read()
        cnt += 1

        # 프레임 건너뛰기
        if cnt % 15:  # 0.5초씩 건너뛰기
            continue

        if not success:
            break
        # 현재 프레임 번호
        current_frame = int(video.get(cv2.CAP_PROP_POS_FRAMES))

        # 현재 초 계산
        current_time = current_frame / fps

        print(f"{current_time:.2f} sec")

        _, buffer = cv2.imencode(".jpg", frame)
        base64_image_string = base64.b64encode(buffer).decode("utf-8")

        # API 엔드포인트 URL 구성 --------------------------------------------------------------------------------------------------

        infer_url = f"ROBOFLOW_INFERENCE_URL"
        response = requests.post(
            infer_url,
            data=base64_image_string,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        result = response.json()

        predictions = result.get("predictions", [])
        print("Predictions:", predictions)
        classes = [prediction["class"] for prediction in result["predictions"]]
        print(classes)

        # base64로 인코딩된 시각화 이미지 추출
        base64_image = result.get("visualization", "")

        image_data = base64.b64decode(base64_image)

        # AWS S3 클라이언트 설정 -----------------------------------------------------------------------

        if not is_fire(classes):  # 화재 관련 객체 미감지 시 건너뛰기
            continue

        s3_client = boto3.client(
            "s3",
            aws_access_key_id="AWS_ACCESS_KEY_ID",
            aws_secret_access_key="AWS_SECRET_ACCESS_KEY",
            region_name="REGION_NAME",
        )
        # S3 버킷 이름 및 파일 이름 설정

        bucket_name = "BUCKET_NAME"
        file_name = f"uploaded_image_{datetime.now().strftime('%m_%d_%Y_%H:%M:%S')}.jpg"

        # S3에 업로드
        s3_client.put_object(
            Bucket=bucket_name,
            Key=file_name,
            Body=image_data,
            ContentType="image/jpeg",
        )
        image_url = f"https://{bucket_name}.s3.{s3_client.meta.region_name}.amazonaws.com/{file_name}"
        print("Image URL:", image_url)

        # 카카오 API 요청 ---------------------------------------------------------------------------

        url = "https://kapi.kakao.com/v2/api/talk/memo/default/send"
        headers = {"Authorization": f"Bearer {access_token}"}
        data = {
            "template_object": json.dumps(
                {
                    "object_type": "feed",
                    "content": {
                        "title": f"🔥 {classes} 발견",
                        "description": "화재 감지됨",
                        "image_url": image_url,
                        "image_width": 640,
                        "image_height": 640,
                        "link": {"web_url": image_url, "mobile_web_url": image_url},
                    },
                }
            )
        }
        response = requests.post(url, headers=headers, data=data)
        if response.json().get("result_code") == 0:
            print("메시지를 성공적으로 보냈습니다.")
        else:
            print("메시지 전송 실패:", response.json())
        time.sleep(1)

    video.release()
    return "처리가 완료되었습니다."


# Gradio 인터페이스 생성 --------------------------------------------------------------------------
iface = gr.Interface(
    fn=process_video,
    inputs=[
        gr.Textbox(label="YouTube URL"),
        gr.File(label="로컬 비디오 파일 선택"),
    ],
    outputs="text",
    title="화재 감지 프로그램",
    description="YouTube URL / 로컬 비디오 파일을 입력",
)

iface.launch()
