FROM python:3.11-slim

WORKDIR /app

# حزمة حاجات النظام عشان بعض المكتبات تعمل
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# نسخ متطلبات المشروع ونثبتها
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# نسخ كود المشروع
COPY OMNI_NEXUS_v11.py .

# المنفذ اللي بيفتح عليه
EXPOSE 8000

# تشغيل الخادم
CMD ["python", "OMNI_NEXUS_v11.py"]
