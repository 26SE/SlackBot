# Oracle Cloud 슬랙봇 서버 구축 보고서

## 개요

| 항목 | 내용 |
|------|------|
| 목적 | Slack Weather & Schedule Bot 서버 구축 |
| 클라우드 | Oracle Cloud Infrastructure (OCI) |
| 리전 | South Korea North (Chuncheon) |
| 날짜 | 2026-05-30 |

---

## 1. Compute Instance 생성

| 항목 | 값 |
|------|-----|
| 인스턴스 이름 | instance-20260530-1400 |
| OS | Canonical Ubuntu 22.04 |
| Shape | VM.Standard.E2.1.Micro (Always Free) |
| 스펙 | 1 core OCPU, 1 GB RAM, 0.48 Gbps |
| Compartment | eyesome25 (root) |
| Availability Domain | AP-CHUNCHEON-1-AD-1 |

---

## 2. 네트워크 설정 (VCN)

### 2-1. Virtual Cloud Network 생성

| 항목 | 값 |
|------|-----|
| VCN 이름 | fuckass |
| IPv4 CIDR Block | 10.0.0.0/16 |
| DNS Label | fuckass |
| DNS Domain | fuckass.oraclevcn.com |

### 2-2. Public Subnet 생성

| 항목 | 값 |
|------|-----|
| 서브넷 이름 | public-subnet |
| IPv4 CIDR Block | 10.0.0.0/24 |
| Subnet Access | Public (Regional) |

### 2-3. Internet Gateway 생성

| 항목 | 값 |
|------|-----|
| 이름 | igw |
| 상태 | Available |

### 2-4. Route Table 설정

Default Route Table for fuckass에 아래 규칙 추가:

| Destination | Target Type | Target | Route Type |
|-------------|-------------|--------|------------|
| 0.0.0.0/0 | Internet Gateway | igw | Static |

---

## 3. SSH 키

- **Generate a key pair for me** 선택
- Private key 다운로드 완료 (`.key` 파일)
- **주의**: Private key는 재다운로드 불가. 분실 시 인스턴스 재생성 필요.

---

## 4. 인스턴스 생성 결과

- 상태: Provisioning → Running 대기 중
- Public IP: 인스턴스 생성 완료 후 Details 탭에서 확인

---

## 5. 다음 단계 (TODO)

### 5-1. Security List 포트 개방

인스턴스 생성 완료 후 OCI 콘솔에서 아래 포트 Ingress 규칙 추가 필요:

| 포트 | 프로토콜 | 용도 |
|------|----------|------|
| 22 | TCP | SSH |
| 80 | TCP | HTTP |
| 443 | TCP | HTTPS |

### 5-2. 서버 초기 설정

SSH 접속 후 실행:

```bash
ssh -i <private-key>.key ubuntu@<PUBLIC_IP>

sudo apt update && sudo apt upgrade -y
sudo apt install -y python3.11 python3.11-venv python3-pip nginx certbot python3-certbot-nginx

# OS 레벨 방화벽 포트 개방
sudo iptables -I INPUT -p tcp --dport 80 -j ACCEPT
sudo iptables -I INPUT -p tcp --dport 443 -j ACCEPT
sudo iptables -I INPUT -p tcp --dport 8000 -j ACCEPT
sudo apt install -y iptables-persistent
sudo netfilter-persistent save
```

### 5-3. 슬랙봇 배포

```bash
git clone <repo-url> /home/ubuntu/slackbot
cd /home/ubuntu/slackbot
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# .env 파일에 환경변수 입력
```

### 5-4. systemd 서비스 등록

`/etc/systemd/system/slackbot.service`:

```ini
[Unit]
Description=Slack Bot
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/slackbot
EnvironmentFile=/home/ubuntu/slackbot/.env
ExecStart=/home/ubuntu/slackbot/venv/bin/uvicorn api:app --host 127.0.0.1 --port 8000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable slackbot
sudo systemctl start slackbot
```

### 5-5. Nginx 설정

`/etc/nginx/sites-available/slackbot`:

```nginx
server {
    listen 80;
    server_name <PUBLIC_IP_OR_DOMAIN>;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/slackbot /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

### 5-6. Slack App Request URL 설정

Slack API 콘솔에서:
- Slash Commands Request URL: `http://<PUBLIC_IP>/slack/events`
- Event Subscriptions URL: `http://<PUBLIC_IP>/slack/events`

---

## 비고

- VM.Standard.E2.1.Micro는 RAM 1GB로 빠듯할 수 있음. 메모리 부족 시 swap 설정 권장.
- 도메인 확보 후 Let's Encrypt로 HTTPS 적용 가능.
