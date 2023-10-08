document.addEventListener("DOMContentLoaded", () => {
    const socket = io.connect("http://localhost:5000/video_socket"); // Adjust the server address if needed.

    // Handle processed frames from the server (if needed)
    socket.on("processed_frame", (frame) => {
        const videoElement = document.getElementById("videoElement");
        videoElement.src = `data:image/jpeg;base64,${frame}`;
    });
});
