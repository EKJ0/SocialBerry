/**
 * Place search via Photon (OpenStreetMap), https://photon.komoot.io
 */
(function () {
    var PHOTON = 'https://photon.komoot.io/api/';

    function zoomFromProps(p) {
        if (!p) return 12;
        var t = (p.type || '').toLowerCase();
        var v = (p.osm_value || '').toLowerCase();
        if (t === 'house' || v === 'house') return 17;
        if (t === 'street' || p.osm_key === 'highway') return 14;
        if (t === 'district' || t === 'suburb' || t === 'neighbourhood') return 13;
        if (t === 'city' || t === 'town' || v === 'city' || v === 'town') return 11;
        if (t === 'state' || t === 'region') return 7;
        if (t === 'country') return 5;
        return 12;
    }

    /**
     * Photon returns extent as [minLon, maxLat, maxLon, minLat].
     * MapLibre wants southwest then northeast: [[minLon, minLat], [maxLon, maxLat]].
     */
    function extentToBounds(ext) {
        if (!ext || ext.length !== 4) return null;
        var minLon = ext[0];
        var maxLat = ext[1];
        var maxLon = ext[2];
        var minLat = ext[3];
        return [[minLon, minLat], [maxLon, maxLat]];
    }

    function setMsg(el, text, tone) {
        if (!text) {
            el.hidden = true;
            el.textContent = '';
            el.removeAttribute('data-tone');
            return;
        }
        el.hidden = false;
        el.textContent = text;
        if (tone) el.setAttribute('data-tone', tone);
        else el.removeAttribute('data-tone');
    }

    function init() {
        var map = window.map;
        if (!map) return;

        var form = document.getElementById('sb-place-search');
        var input = document.getElementById('sb-search-input');
        var btn = document.getElementById('sb-search-submit');
        var msg = document.getElementById('sb-search-msg');
        if (!form || !input || !btn || !msg) return;

        form.addEventListener('submit', function (e) {
            e.preventDefault();
            var q = (input.value || '').trim();
            setMsg(msg, '');

            if (!q) {
                setMsg(msg, 'Enter a place name to search.');
                return;
            }

            btn.disabled = true;
            var url = PHOTON + '?q=' + encodeURIComponent(q) + '&limit=1';

            fetch(url)
                .then(function (r) {
                    if (!r.ok) throw new Error('Search failed (' + r.status + ')');
                    return r.json();
                })
                .then(function (data) {
                    var features = data && data.features;
                    if (!features || !features.length) {
                        setMsg(msg, 'No results for “' + q + '”. Try another spelling or add a country.');
                        return;
                    }

                    var feat = features[0];
                    var coords = feat.geometry && feat.geometry.coordinates;
                    if (!coords || coords.length < 2) {
                        setMsg(msg, 'Could not read coordinates for that result.');
                        return;
                    }

                    var lon = coords[0];
                    var lat = coords[1];
                    var p = feat.properties || {};
                    var label = [p.name, p.city || p.town, p.country]
                        .filter(Boolean)
                        .join(', ');
                    var bounds = extentToBounds(p.extent);

                    var pitch = map.getPitch();
                    var bearing = map.getBearing();

                    if (bounds) {
                        map.fitBounds(bounds, {
                            padding: 56,
                            maxZoom: 17,
                            duration: 1600,
                            pitch: pitch,
                            bearing: bearing
                        });
                    } else {
                        map.flyTo({
                            center: [lon, lat],
                            zoom: zoomFromProps(p),
                            pitch: pitch,
                            bearing: bearing,
                            essential: true
                        });
                    }

                    if (label) {
                        setMsg(msg, label, 'info');
                    }
                })
                .catch(function () {
                    setMsg(msg, 'Could not reach the search service. Check your connection and try again.');
                })
                .finally(function () {
                    btn.disabled = false;
                });
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
