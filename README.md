# AlgoGym

AlgoGym is a personalized coding practice platform that helps students improve their programming skills through AI-driven learning.

## Features

* Solve programming problems online
* Compile and run code in multiple programming languages using Judge0
* Receive AI-generated feedback on failed submissions
* Track progress through a personalized dashboard
* Detect weak programming concepts using a deep learning model
* Get personalized problem recommendations

## Tech Stack

* **Frontend:** React
* **Backend:** Spring Boot
* **Database:** Supabase (PostgreSQL)
* **AI & Machine Learning:** Python, PyTorch, LightGBM
* **Code Execution:** Judge0
* **AI Feedback:** Groq API

## Repository Structure

```text
frontend/    React application
backend/     Spring Boot API
ai/          Machine learning models and recommendation engine
```
## Configuration

The backend requires a `src/main/resources/application.properties` file (not committed to the repo). It needs the following keys configured:

```properties
spring.application.name=backend
server.port=8080

# Supabase Database (transaction pooler – avoids session-mode 15-client cap)
spring.datasource.url=jdbc:postgresql://<supabase-pooler-host>:6543/postgres?prepareThreshold=0
spring.datasource.username=<supabase-db-username>
spring.datasource.password=<supabase-db-password>
spring.datasource.driver-class-name=org.postgresql.Driver
spring.datasource.hikari.maximum-pool-size=5

# JPA
spring.jpa.hibernate.ddl-auto=update
spring.jpa.show-sql=true
spring.jpa.properties.hibernate.format_sql=true

# Judge0 Configuration
judge0.api.url=https://judge0-ce.p.rapidapi.com
judge0.api.key=<your-rapidapi-key>
judge0.api.host=judge0-ce.p.rapidapi.com

# Logging
logging.level.com.problemsolving=DEBUG

# JWT Configuration
jwt.secret=<base64-secret>
jwt.expiration=86400000

# SendGrid
sendgrid.api-key=${SENDGRID_API_KEY:<your-sendgrid-key>}
sendgrid.from-email=<your-from-email>
sendgrid.from-name=AlgoGym

# Frontend URL (used in reset link)
app.frontend-url=http://localhost:5173

# Password Reset Config
app.password-reset.expiry-minutes=60
app.password-reset.max-requests-per-hour=3

# Groq
groq.api.key=${GROQ_API_KEY:<your-groq-key>}
groq.api.url=https://api.groq.com/openai/v1/chat/completions

spring.servlet.multipart.max-file-size=10MB
spring.servlet.multipart.max-request-size=10MB
server.tomcat.max-http-post-size=10MB
server.tomcat.max-swallow-size=10MB
```

### Services you need accounts/keys for

| Service | Used for | Where to get it |
|---|---|---|
| Supabase | PostgreSQL database | Project Settings → Database → Connection string (use Transaction pooler, port 6543) |
| Judge0 (via RapidAPI) | Code compilation/execution | RapidAPI → Judge0 CE → your `X-RapidAPI-Key` |
| Groq | AI feedback on failed submissions | console.groq.com → API Keys |
| SendGrid | Password reset emails | SendGrid → Settings → API Keys |
| JWT secret | Auth token signing | Any long random base64 string you generate yourself |