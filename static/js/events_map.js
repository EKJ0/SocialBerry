(function () {
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

  function extentToBounds(ext) {
    if (!ext || ext.length !== 4) return null;
    var minLon = ext[0], maxLat = ext[1], maxLon = ext[2], minLat = ext[3];
    return [[minLon, minLat], [maxLon, maxLat]];
  }

  async function initMap() {
    const mapEl = document.getElementById('map');
    if (!mapEl || typeof maplibregl === 'undefined') return;

    const map = new maplibregl.Map({
      container: 'map',
      style: 'https://tiles.openfreemap.org/styles/liberty',
      center: [55.2708, 25.2048],
      zoom: 10,
      pitch: 45,
      bearing: -15
    });

    map.addControl(new maplibregl.NavigationControl(), 'top-right');
    window.map = map;

    map.on('load', async function () {
      try {
        const response = await fetch('/api/events');
        const data = await response.json();

        map.addSource('events', { type: 'geojson', data });
        map.addLayer({
          id: 'events-circles',
          type: 'circle',
          source: 'events',
          paint: {
            'circle-radius': 8,
            'circle-color': '#7cab2f',
            'circle-stroke-width': 2,
            'circle-stroke-color': '#ffffff'
          }
        });

        map.addLayer({
          id: 'events-labels',
          type: 'symbol',
          source: 'events',
          layout: {
            'text-field': ['get', 'title'],
            'text-offset': [0, 1.4],
            'text-size': 11
          },
          paint: {
            'text-color': '#22311e'
          }
        });

        map.on('click', 'events-circles', function (e) {
          const feature = e.features[0];
          const props = feature.properties;
          const coords = feature.geometry.coordinates.slice();
          new maplibregl.Popup()
            .setLngLat(coords)
            .setHTML(
              '<div class="sb-event-popup">' +
              '<h3>' + props.title + '</h3>' +
              '<p>' + props.category + '</p>' +
              '<p>' + props.date + ' at ' + props.time + '</p>' +
              '<p>' + props.location + ', ' + props.city + '</p>' +
              '<p>€' + props.price + '</p>' +
              '</div>'
            )
            .addTo(map);
        });

        map.on('mouseenter', 'events-circles', function () {
          map.getCanvas().style.cursor = 'pointer';
        });
        map.on('mouseleave', 'events-circles', function () {
          map.getCanvas().style.cursor = '';
        });
      } catch (err) {
        console.error(err);
      }
    });

    const form = document.getElementById('sb-place-search');
    const input = document.getElementById('sb-search-input');
    const btn = document.getElementById('sb-search-submit');
    const msg = document.getElementById('sb-search-msg');
    if (!form || !input || !btn || !msg) return;

    form.addEventListener('submit', function (e) {
      e.preventDefault();
      const q = (input.value || '').trim();
      setMsg(msg, '');
      if (!q) {
        setMsg(msg, 'Enter a place name to search.');
        return;
      }
      btn.disabled = true;
      fetch('https://photon.komoot.io/api/?q=' + encodeURIComponent(q) + '&limit=1')
        .then(function (r) {
          if (!r.ok) throw new Error();
          return r.json();
        })
        .then(function (data) {
          const features = data && data.features;
          if (!features || !features.length) {
            setMsg(msg, 'No results found for that search.');
            return;
          }
          const feat = features[0];
          const coords = feat.geometry.coordinates;
          const p = feat.properties || {};
          const bounds = extentToBounds(p.extent);
          if (bounds) {
            map.fitBounds(bounds, { padding: 56, maxZoom: 16, duration: 1300 });
          } else {
            map.flyTo({ center: coords, zoom: zoomFromProps(p), essential: true });
          }
          setMsg(msg, [p.name, p.city || p.town, p.country].filter(Boolean).join(', '), 'info');
        })
        .catch(function () {
          setMsg(msg, 'Could not reach the search service.');
        })
        .finally(function () {
          btn.disabled = false;
        });
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initMap);
  } else {
    initMap();
  }
})();
