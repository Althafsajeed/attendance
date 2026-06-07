document.querySelectorAll(".location-form").forEach((form) => {
    form.addEventListener("submit", (event) => {
        const latitude = form.querySelector('input[name="latitude"]');
        const longitude = form.querySelector('input[name="longitude"]');

        if (latitude.value && longitude.value) {
            return;
        }

        event.preventDefault();
        if (!navigator.geolocation) {
            alert("Your browser does not support location detection.");
            return;
        }

        navigator.geolocation.getCurrentPosition(
            (position) => {
                latitude.value = position.coords.latitude.toFixed(6);
                longitude.value = position.coords.longitude.toFixed(6);
                form.requestSubmit();
            },
            () => {
                alert("Please allow location access to mark attendance.");
            },
            { enableHighAccuracy: true, timeout: 12000, maximumAge: 0 }
        );
    });
});
