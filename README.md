# pfplay-streaming

1. git repo 셋팅
2. python 3.11 설치
3. ffmpeg 설치
   1. video 포맷 변환, mp4 -> m3u8
   2. apt install ffmpeg
4. nginx-rtmp 설치
   1. nginx 스트리밍 extension
   2. apt install libnginx-mod-rtmp
5. nginx 셋팅
   1. /etc/nginx/nginx.conf 내용 수정
      1. resources/nginx.conf 내용으로 변경
