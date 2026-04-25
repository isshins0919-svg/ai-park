FROM python:3.11-slim

# ffmpeg + 日本語フォント（Noto CJK）
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    fonts-noto-cjk \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# アップロードディレクトリ作成
RUN mkdir -p video-ai/fv_studio/uploads

ENV PORT=8080
# Cloud Run の stdout ログが遅延しないよう Python を unbuffered で起動
ENV PYTHONUNBUFFERED=1
EXPOSE 8080

# gunicorn: 1ワーカー(job状態をメモリ共有) + 8スレッド(並列リクエスト対応)
# timeout=3600 → 動画生成が長くてもタイムアウトしない
CMD ["gunicorn", \
     "--workers=1", \
     "--threads=8", \
     "--timeout=3600", \
     "--bind=0.0.0.0:8080", \
     "--chdir=video-ai/fv_studio", \
     "app:app"]
