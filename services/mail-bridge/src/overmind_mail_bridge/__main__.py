import uvicorn


def main():
    uvicorn.run(
        "overmind_mail_bridge.server:app",
        host="0.0.0.0",
        port=8025,
        log_level="info",
    )


if __name__ == "__main__":
    main()
