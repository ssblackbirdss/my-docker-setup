# My Docker Setup

This repository contains a Dockerized setup for two distinct services: an audio transcription service using OpenAI's Whisper model and a WordPress content management system. This setup allows for easy deployment and management of both applications using Docker Compose.

## Project Structure

```
.
├── README.md
├── whisper/
│   ├── .dockerignore
│   ├── docker-compose.yml
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── transcribe.py
│   └── audio/
│       ├── processed/
│       └── transcripts/
└── wordpress/
    └── docker-compose.yaml
```

## Features

### Whisper Audio Transcription Service

- **Dockerized Environment:** Run the Whisper transcription service within a Docker container.
- **Python-based:** Utilizes a Python script (`transcribe.py`) to interface with the Whisper model.
- **Automated Transcription:** Designed to process audio files and store their transcripts.

### WordPress CMS

- **Dockerized WordPress:** A standard WordPress installation running in Docker containers.
- **Easy Deployment:** Managed via Docker Compose for quick setup and tear down.
- **Content Management:** Provides a robust platform for website and blog management.

## Prerequisites

Before you begin, ensure you have the following installed on your system:

- [**Docker**](https://docs.docker.com/get-docker/): Docker Engine and Docker Compose.

## Setup and Installation

Follow these steps to get your Dockerized services up and running.

### 1. Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/YOUR_REPOSITORY_NAME.git
cd YOUR_REPOSITORY_NAME
```

(Replace `YOUR_USERNAME` and `YOUR_REPOSITORY_NAME` with your actual GitHub details.)

### 2. Configure Whisper Service

Navigate to the `whisper` directory:

```bash
cd whisper
```

The `Dockerfile` and `requirements.txt` are set up to create an environment for `transcribe.py`.

### 3. Configure WordPress Service

Navigate to the `wordpress` directory:

```bash
cd wordpress
```

The `docker-compose.yaml` file defines the WordPress service along with its database.

### 4. Build and Run Services with Docker Compose

From the root directory of the repository (e.g., `My-Docker-Setup/`), you can bring up both services using Docker Compose.

To start both the Whisper and WordPress services:

```bash
docker-compose -f whisper/docker-compose.yml -f wordpress/docker-compose.yaml up -d
```

This command will:

- Build the Docker image for the Whisper service (if not already built).
- Start the Whisper service.
- Start the WordPress service, including its database.
- Run them in detached mode (`-d`).

### 5. Verify Installation

- **WordPress:** Once the services are up, WordPress should be accessible in your web browser, typically at `http://localhost:8000` (or the port you configured in `wordpress/docker-compose.yaml`). Follow the on-screen instructions to complete the WordPress setup.
- **Whisper Service:** To check if the Whisper container is running, use:
  ```bash
  docker-compose -f whisper/docker-compose.yml ps
  ```

## Usage

### Whisper Audio Transcription

To transcribe an audio file:

1.  Place your audio file (e.g., `example.mp3`) into the `whisper/audio/` directory.
2.  You will need to run the transcription script from within the Docker container. You can execute commands in the running container:

    ```bash
    docker-compose -f whisper/docker-compose.yml exec whisper-service python transcribe.py your_audio_file.mp3
    ```

    (Replace `whisper-service` with the actual service name from `whisper/docker-compose.yml` if different, and `your_audio_file.mp3` with your audio file's name.)

    The transcribed text will be saved in `whisper/audio/transcripts/`.

### WordPress

Access your WordPress instance by navigating to `http://localhost:8000` (or your configured port) in your web browser. You can then log in to the admin dashboard and start managing your content.

## Contributing

Feel free to fork this repository, open issues, and submit pull requests.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
