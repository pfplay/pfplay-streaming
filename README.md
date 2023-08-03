# PFPlay-streaming

PFPlay-streaming is a dedicated service to serve streaming jobs from external sources to party room entities. 

<details>
<summary> Local settings with nginx (will be deprecaated)</summary>

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
      
</details>

<details open>
<summary> Docker Setup </summary>

1. Download [Docker Client](https://www.docker.com/products/docker-desktop/) if you don't have it on your local
2. Make sure Docker client is running on the local
3. Run the following command to build a local image
```bash
docker build -t pfplay-streaming .
```
4. Execute the image on the port as you want 
```bash
docker run --name pfplay-streaming -p 9000:9000 pystreaming
```
5. When you're done with testing, stop the docker image
```bash
docker stop pystreaming
```
6. Whenever you feel like starting the image again, you can start the image
```bash
docker start pystreaming
```
7. We should prune the image if you want to re-build the image in case any updates on the FastAPI or the image.
```bash
docker container prune -f
```

</details>