# gemini-storybook-creation

  - **Author**: Haizea Rumayor Lazkano
  - **Last update**: October 2025

------------------------------------------------------------------------

## Overview

This project provides an API that receives information about a person and the type of event where they were met, and uses this data to generate a personalized storybook through the `Gemini LLM`.

The service is containerized with `Docker` and deployed on an `AWS EC2 instance`. The generated stories are stored in both `.`txt` and `.json` formats in an `S3 bucket`, while logs are sent to `CloudWatch`.

## Key Features

- Built with **Flask** as the main web framework.

- Uses **Gemini LLM** to create a short story or _storybook_ based on input data (person and event).

- Stores results in **Amazon S3** as both `.txt` and `.json` files.

- Logs are captured in real time and sent to **AWS CloudWatch**.

- Exposed through a **GET API endpoint** for story generation requests.

## Project Structure

The project is organized as a lightweight Docker application with the following components:

- `src/main.py`: main Flask application file containing the API logic.

- `.env`: environment variables and API keys configuration.

- `requirements.txt`: list of Python dependencies.

- `Dockerfile`: container definition for deployment on AWS EC2.

## Installation

This project is designed for deployment on **AWS**.

An **EC2 instance** is used to host the service, with **Docker** and **CloudWatch agents** installed and configured.
The instance must have the appropriate IAM permissions to write logs to **CloudWatch** and store files in **S3**.

Once deployed, the service can be accessed through a **GET API request** that sends user and event data, triggering the automatic generation of a personalized storybook.


## Execution

To build and run the container:

```bash
docker build -t gemini-storybook-creator .
docker run -d -p 5000:5000 -v /home/ec2-user/app/logs:/usr/local/app/logs --env-file .env gemini-storybook-creator
```

## Postman Request

```
GET http://<EC2-IP>:5000/generar-cuento
HEADER: key = Content-Type  Value = application/json
BODY: 
{
  "KNOWN": 1,
  "NAME": "xxxx",
  "COMPANY": "xxxx",
  "FUNCTION": "xxxx",
  "AREA": "xxxx",
  "EVENT": "xxxxn",
  "PLACE": "xxxx"
}
```

## Responds

Returns a JSON object containing:

- ok: operation status

- time: time taken to generate the story

- generated_story: the generated story text divided into chapters
