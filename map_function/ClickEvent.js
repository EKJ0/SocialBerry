(function () {
    var map = window.map;
    if (!map || typeof maplibregl === 'undefined') {
        console.error('ClickEvent.js: open MapView.html (map must be created before this script).');
        return;
    }
    map.on('click', function (e) {
        var lng = e.lngLat.lng;
        var lat = e.lngLat.lat;

        new maplibregl.Popup()
            .setLngLat([lng, lat])
            .setHTML(
                '<div class="sb-event-popup">' +
                '<h3>New Event</h3>' +
                '<p class="sb-coords">Longitude: ' + lng.toFixed(4) + '</p>' +
                '<p class="sb-coords">Latitude: ' + lat.toFixed(4) + '</p>' +
                '</div>'
            )
            .addTo(map);
    });
})();
