let socket = new WebSocket("ws://localhost:8000/ws/predictions/");
socket.onmessage = function (e) {
    let predictionData = JSON.parse(e.data);
    // Update HTML content with real-time prediction data
    document.getElementById("prediction-container").innerHTML = predictionData.prediction;
};
