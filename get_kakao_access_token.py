import requests
import json

# 카카오톡 메시지 API
url = "https://kauth.kakao.com/oauth/token"
data = {
    "grant_type": "authorization_code",
    "client_id": "68c3e7fe97bb829c0d8138cf99ffe600",
    "redirect_url": "https://localhost:3000",
    "code": "CODE",  # url의 code=뒷부분 입력
}
response = requests.post(url, data=data)
tokens = response.json()
print(tokens)


# kakao_code.json 파일 저장
with open("kakao_code.json", "w") as fp:
    json.dump(tokens, fp)


# 크롬 시크릿모드 창 오픈 후, https://kauth.kakao.com/oauth/authorize?client_id={REST API 키}&redirect_uri=https://localhost:3000&response_type=code&scope=talk_message 검색 -> url에 code 뒷부분을 위 code에 넣고 실행 -> access_token 발급 (약 6시간동안 유효)
