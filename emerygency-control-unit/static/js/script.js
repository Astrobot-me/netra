// Initialize Firebase when the DOM is ready
document.addEventListener('DOMContentLoaded', function () {
  const firebaseConfig = {
    apiKey: "AIzaSyBEnvJHTOFtd-jPiBaCu2nxgbLA5Ycr0cU",
    authDomain: "traffic-sim-6e506.firebaseapp.com",
    projectId: "traffic-sim-6e506",
    storageBucket: "traffic-sim-6e506.appspot.com",
    messagingSenderId: "1017421602185",
    appId: "1:1017421602185:web:aeb2251728e43277135558",
    measurementId: "G-QH22HW4L1Q"
  };

  if (!firebase.apps.length) {
    firebase.initializeApp(firebaseConfig);
  }

  const db = firebase.firestore();
  initializeApplication(db);
});

async function initializeApplication(db) {
  const socket = io();
  let selectedAccident = null;

  // Fetch the latest accident data
  try {
    const querySnapshot = await db.collection("accidents_data")
      .orderBy("timestamp", "desc")
      .limit(1)
      .get();

    if (!querySnapshot.empty) {
      const latestAccident = querySnapshot.docs[0].data();
      selectedAccident = {
        lat: latestAccident.latitude,
        lng: latestAccident.longitude,
        address: latestAccident.address || "Accident Location",
        frame: latestAccident.frame || null
      };

      console.log("Latest accident data:", selectedAccident);

      // Update the existing HTML elements
      const accidentImage = document.getElementById('accidentImage');
      const accidentAddress = document.getElementById('accidentAddress');

      if (selectedAccident.frame) {
        accidentImage.src = `data:image/png;base64,${selectedAccident.frame}`;
        accidentImage.style.display = 'block';
      } else {
        accidentImage.style.display = 'none';
      }

      accidentAddress.textContent = selectedAccident.address;

    } else {
      console.log("No accidents found in database");
      document.getElementById('map').innerHTML = "<p>No recent accidents detected. The system will activate when an accident is reported.</p>";
      return;
    }
  } catch (error) {
    console.error("Error fetching accident data:", error);
    document.getElementById('map').innerHTML = "<p>Error loading accident data. Please try again later.</p>";
    return;
  }

  const userLatLng = L.latLng(selectedAccident.lat, selectedAccident.lng);
  const map = L.map('map').setView(userLatLng, 15);

  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap contributors'
  }).addTo(map);

  let routingControl = null;

  const ambulanceIcon = L.icon({
    iconUrl: '/static/img/ambulance.png',
    iconSize: [32, 32],
    iconAnchor: [16, 32],
    popupAnchor: [0, -32]
  });

  const trafficIcon = L.icon({
    iconUrl: '/static/img/traffic-light.png',
    iconSize: [24, 36],
    iconAnchor: [12, 36],
    popupAnchor: [0, -36]
  });

  const ambulanceIds = ['ambulance_1', 'ambulance_2', 'ambulance_3', 'ambulance_4'];
  const ambulanceMarkers = [];

  // Place accident marker
  L.marker(userLatLng)
    .addTo(map)
    .bindPopup(`<b>${selectedAccident.address}</b><br>
               Latitude: ${selectedAccident.lat.toFixed(6)}<br>
               Longitude: ${selectedAccident.lng.toFixed(6)}`)
    .openPopup();

  // Fake ambulances
  const fakeAmbulances = Array.from({ length: 4 }, () => ({
    lat: userLatLng.lat + (Math.random() - 0.5) * 0.02,
    lng: userLatLng.lng + (Math.random() - 0.5) * 0.02
  }));

  fakeAmbulances.forEach((amb, idx) => {
    const marker = L.marker([amb.lat, amb.lng], { icon: ambulanceIcon })
      .addTo(map)
      .bindPopup(`Ambulance ${idx + 1}`);
    marker.ambulanceId = ambulanceIds[idx];
    ambulanceMarkers.push(marker);
  });

  function autoSearchAmbulance() {
    const searchRadii = [500, 1000, 1500];
    let attempt = 0;
    let searchCircle = null;

    const trySearch = () => {
      const radius = searchRadii[attempt];

      if (searchCircle) {
        map.removeLayer(searchCircle);
      }

      searchCircle = L.circle(userLatLng, {
        radius: radius,
        color: '#39ff14',
        weight: 2,
        fillColor: '#39ff14',
        fillOpacity: 0.1
      }).addTo(map);

      const nearest = findNearestAmbulanceWithinRadius(userLatLng, ambulanceMarkers, radius);

      if (nearest) {
        nearest.openPopup();

        socket.emit('ambulance-operate', {
          ambulanceId: nearest.ambulanceId,
          trigger: 1
        });

        if (routingControl) {
          map.removeControl(routingControl);
        }

        routingControl = L.Routing.control({
          waypoints: [nearest.getLatLng(), userLatLng],
          lineOptions: { styles: [{ color: 'blue', opacity: 0.6, weight: 4 }] },
          createMarker: () => null,
          addWaypoints: false,
          routeWhileDragging: false,
          showAlternatives: false,
          router: L.Routing.osrmv1({
            serviceUrl: 'https://router.project-osrm.org/route/v1'
          })
        })
          .on('routesfound', function (e) {
            const route = e.routes[0];
            const coordinates = route.coordinates;
            const routeId = db.collection('emergencyRoutes').doc().id;
            storeTrafficLights(routeId, nearest.ambulanceId, coordinates);
          })
          .addTo(map);

      } else {
        attempt++;
        if (attempt < searchRadii.length) {
          setTimeout(trySearch, 2000);
        } else {
          alert("No ambulance found within 1500 meters.");
        }
      }
    };

    trySearch();
  }

  function findNearestAmbulanceWithinRadius(userLL, markers, radius) {
    let nearest = null;
    let minDist = Infinity;
    markers.forEach(marker => {
      const dist = userLL.distanceTo(marker.getLatLng());
      if (dist <= radius && dist < minDist) {
        minDist = dist;
        nearest = marker;
      }
    });
    return nearest;
  }

  async function storeTrafficLights(routeId, ambulanceId, coordinates) {
    try {
      const batch = db.batch();
      const trafficLightsRef = db.collection('trafficLights');
      const trafficList = document.getElementById('trafficList');
      trafficList.innerHTML = '';

      const trafficLights = [];
      const trafficLightsCoordinates = [];

      for (let i = 5; i < coordinates.length - 5; i += 10) {
        const point = coordinates[i];

        const trafficLightData = {
          lat: point.lat,
          lng: point.lng,
          timestamp: firebase.firestore.FieldValue.serverTimestamp(),
          routeId: routeId,
          ambulanceId: ambulanceId,
          accidentLocation: new firebase.firestore.GeoPoint(userLatLng.lat, userLatLng.lng),
          status: 'pending'
        };

        L.marker([point.lat, point.lng], { icon: trafficIcon })
          .addTo(map)
          .bindPopup(`Traffic Light<br>Lat: ${point.lat.toFixed(6)}<br>Lng: ${point.lng.toFixed(6)}`);

        const li = document.createElement('li');
        li.textContent = `Lat: ${point.lat.toFixed(6)}, Lng: ${point.lng.toFixed(6)}`;
        trafficList.appendChild(li);

        const lightRef = trafficLightsRef.doc();
        batch.set(lightRef, trafficLightData);

        trafficLights.push(lightRef.id);
        trafficLightsCoordinates.push(new firebase.firestore.GeoPoint(point.lat, point.lng));
      }

      const routeData = {
        ambulanceId: ambulanceId,
        accidentLocation: new firebase.firestore.GeoPoint(userLatLng.lat, userLatLng.lng),
        startTime: firebase.firestore.FieldValue.serverTimestamp(),
        status: 'active',
        trafficLights,
        trafficLightsCoordinates,
        optimizedPath: coordinates.map(coord => new firebase.firestore.GeoPoint(coord.lat, coord.lng))
      };

      batch.set(db.collection('emergencyRoutes').doc(routeId), routeData);
      await batch.commit();

      console.log('Traffic light data stored successfully');
    } catch (error) {
      console.error('Error storing traffic light data:', error);
    }
  }

  // Button click
  document.getElementById('searchAmbulanceBtn').addEventListener('click', autoSearchAmbulance);

  // Trigger from server
  socket.on('trigger-assigned', data => {
    console.log('Trigger received:', data.trigger);
    autoSearchAmbulance();
  });
}
