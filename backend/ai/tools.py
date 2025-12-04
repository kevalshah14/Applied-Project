from perception.stream import manager

def access_camera() -> str:
    """Accesses the camera to show what the robot sees.
    
    Returns:
        str: Instructions for the model to display the stream.
    """
    try:
        if not manager.running:
            manager.start()
        return "Camera is active. To show the stream, YOU MUST include this exact markdown image in your response: ![Camera Stream](stream)"
    except Exception as e:
        return f"Failed to access camera: {str(e)}"

