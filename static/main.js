function syncColor() {
    console.log("Main JS loaded.");
    const color = document.getElementById("colorPicker").value;
    document.getElementById("selectedColor").style.backgroundColor = color;
}

addEventListener("DOMContentLoaded", function() {
    const colorPicker = document.getElementById("colorPicker");
    if (colorPicker) {
        colorPicker.addEventListener("input", syncColor);
    }
});

