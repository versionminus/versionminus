from versionminus.core.config import get_settings
import uvicorn


def main():  # pragma: no cover
    settings = get_settings()
    uvicorn.run(
        "versionminus.api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        log_level=settings.log_level.lower(),
        reload=False,
    )


if __name__ == "__main__":  # pragma: no cover
    main()
