
class AppError(Exception):
    """Base exception for application-specific errors with troubleshooting."""
    
    def __init__(self, message: str, troubleshooting_steps: list[str] | None = None):
        super().__init__(message)
        self.troubleshooting_steps = troubleshooting_steps or []


class ConfigurationFormatError(AppError):
    def __init__(self, message: str):
        troubleshooting_steps=[
            "Check if your configuration file is valid JSON format",
            "Try deleting the configuration file to reset to defaults",
            "Restore a backup of your configuration file if available",
            "Check the documentation for the correct configuration format"
        ]
        super().__init__(
            message,
            troubleshooting_steps=troubleshooting_steps
        )