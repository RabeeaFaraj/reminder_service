# Wekan Reminder Service

A microservice that monitors Wekan cards and sends AWS SNS notifications for cards that are due soon.

## Features

- 🔍 Monitors Wekan boards for cards with due dates
- ⏰ Automatically checks for due cards every minute (configurable)
- � Sends notifications via AWS SNS (email, SMS, or other endpoints)
- 🚀 FastAPI REST endpoints for manual triggers and status checks
- 🐳 Fully containerized with Docker Compose
- 🔒 Secure configuration with environment variables
- 📊 Comprehensive logging and error handling
- 🌍 Timezone-aware (supports IDT/Israel Daylight Time)

## Quick Start

### 1. AWS SNS Setup

First, set up AWS SNS for notifications:

1. **Create SNS Topic:**
   - Go to AWS Console → SNS → Create topic
   - Type: Standard
   - Name: `wekan-card-reminders`
   - Create topic

2. **Create Subscription:**
   - In your topic → Subscriptions → Create subscription
   - Protocol: Email
   - Endpoint: your-email@example.com
   - Confirm subscription via email

3. **Configure AWS Credentials:**
   
   You have several options (choose one):
   
   **Option A: AWS CLI (Recommended)**
   ```bash
   aws configure
   # Enter your AWS Access Key ID
   # Enter your AWS Secret Access Key
   # Default region name: eu-west-1
   # Default output format: json
   ```
   
   **Option B: Environment Variables**
   ```bash
   export AWS_ACCESS_KEY_ID=your_access_key
   export AWS_SECRET_ACCESS_KEY=your_secret_key
   ```
   
   **Option C: IAM Role (for EC2/ECS deployment)**
   - Attach an IAM role with SNS permissions to your EC2 instance or ECS task

### 2. Configuration

Update the `.env` file with your settings:

```bash
# Wekan Configuration
WEKAN_URL=http://localhost:80
WEKAN_USER=rabeeaFaraj
WEKAN_PASSWORD=123456789

# AWS SNS Configuration
AWS_REGION=eu-west-1
SNS_TOPIC_ARN=arn:aws:sns:us-east-1:123456789012:wekan-card-reminders

# Application Configuration
SCHEDULER_INTERVAL_MINUTES=1
LOG_LEVEL=INFO
```

**Note:** Replace the SNS_TOPIC_ARN with your actual topic ARN from AWS Console. No need to add AWS access keys to the .env file as boto3 will automatically use your configured AWS credentials.

### 3. Run with Docker Compose

```bash
# Start all services (Wekan, MongoDB, Reminder Service)
docker-compose up -d

# View logs
docker-compose logs -f reminder-service

# Stop all services
docker-compose down
```

### 3. Access the Services

- **Wekan**: http://localhost:80
- **Reminder Service API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## API Endpoints

### GET /status
Get comprehensive service status including scheduler, Wekan connection, and SNS configuration.

### POST /reminders/run
Manually trigger a reminder check and send SNS notifications if due cards are found.

### POST /test/sns
Send a test SNS notification to verify AWS configuration.

### POST /test/wekan
Test Wekan API connection and authentication.

### GET /health
Simple health check endpoint.

## Testing

1. **Setup Wekan**:
   - Access http://localhost:80 (or your Wekan URL)
   - Create an account and login
   - Create a board and add some cards
   - Set due dates on cards (within the next hour for testing)

2. **Test SNS Configuration**:
   ```bash
   curl -X POST http://localhost:8000/test/sns
   ```

3. **Test Wekan Connection**:
   ```bash
   curl -X POST http://localhost:8000/test/wekan
   ```

4. **Manually Trigger Reminder Check**:
   ```bash
   curl -X POST http://localhost:8000/reminders/run
   ```

5. **Check Service Status**:
   ```bash
   curl http://localhost:8000/status
   ```

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Wekan API     │    │ Reminder Service│    │   Gmail SMTP    │
│                 │◄───┤                 ├───►│                 │
│  - Cards        │    │ - FastAPI       │    │ - Email alerts  │
│  - Due dates    │    │ - APScheduler   │    │ - HTML format   │
│  - Boards       │    │ - Logging       │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         ▲                       ▲
         │                       │
┌─────────────────┐    ┌─────────────────┐
│    MongoDB      │    │     Docker      │
│                 │    │   Compose       │
│ - Wekan data    │    │ - Orchestration │
└─────────────────┘    └─────────────────┘
```

## Configuration Options

| Variable | Description | Default |
|----------|-------------|---------|
| `WEKAN_URL` | Wekan instance URL | `http://localhost:80` |
| `WEKAN_USER` | Wekan username | - |
| `WEKAN_PASSWORD` | Wekan password | - |
| `AWS_REGION` | AWS region for SNS | `us-east-1` |
| `SNS_TOPIC_ARN` | SNS topic ARN | - |
| `SCHEDULER_INTERVAL_MINUTES` | Check interval | `1` |
| `LOG_LEVEL` | Logging level | `INFO` |

## Development

### Local Development without Docker

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Set environment variables** (create `.env` file)

3. **Run the service**:
   ```bash
   python app.py
   ```

### Project Structure

```
reminder-service/
├── app.py              # FastAPI main application
├── wekan_client.py     # Wekan API client
├── sns_notifier.py     # AWS SNS notification functionality
├── scheduler.py        # APScheduler integration
├── requirements.txt    # Python dependencies
├── Dockerfile         # Docker image definition
├── docker-compose.yml # Multi-container setup
├── .env              # Environment configuration
├── .gitignore        # Git ignore rules
└── README.md         # This file
```

## Troubleshooting

### Common Issues

1. **AWS SNS Authentication Errors**:
   - Ensure AWS credentials are configured (via `aws configure` or environment variables)
   - Check that the IAM user/role has SNS publish permissions
   - Verify the SNS topic ARN is correct

2. **SNS Subscription Issues**:
   - Confirm you've subscribed to the SNS topic with your email
   - Check your email for confirmation and click the confirmation link
   - Verify the subscription is confirmed in AWS Console

3. **Wekan Connection Issues**:
   - Verify Wekan is accessible at the configured URL
   - Check username/password credentials
   - Ensure Wekan API is enabled

4. **Scheduler Not Running**:
   - Check application logs: `docker-compose logs reminder-service`
   - Verify environment variables are set correctly

4. **No Due Cards Found**:
   - Ensure cards have `dueAt` field set in Wekan
   - Check that due dates are within the next hour
   - Verify you have access to the boards containing the cards

### Logs

View detailed logs for debugging:

```bash
# All services
docker-compose logs

# Just reminder service
docker-compose logs reminder-service

# Follow logs in real-time
docker-compose logs -f reminder-service
```

## Security Considerations

- Use environment variables for all sensitive configuration
- Gmail App Passwords provide better security than regular passwords
- The Docker container runs as a non-root user
- Consider using Docker secrets in production environments

## License

This project is provided as-is for educational and personal use.