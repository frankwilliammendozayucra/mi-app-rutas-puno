import streamlit as st
import osmnx as ox
import folium
from streamlit_folium import st_folium
import heapq

# --- Estado ---
for key in ("origin", "destination", "route_coords", "distance", "select_mode"):
    if key not in st.session_state:
        st.session_state[key] = None

# --- Algoritmo Dijkstra ---
def dijkstra(graph, source, target):
    dist = {node: float('inf') for node in graph}
    prev = {node: None for node in graph}
    dist[source] = 0
    visited = set()
    heap = [(0, source)]
    while heap:
        d_u, u = heapq.heappop(heap)
        if u in visited:
            continue
        visited.add(u)
        if u == target:
            break
        for v, w_uv in graph.get(u, []):
            if v in visited:
                continue
            alt = d_u + w_uv
            if alt < dist[v]:
                dist[v] = alt
                prev[v] = u
                heapq.heappush(heap, (alt, v))
    path = []
    u = target
    if dist[target] == float('inf'):
        return float('inf'), []
    while u is not None:
        path.append(u)
        u = prev[u]
    path.reverse()
    return dist[target], path

# --- Grafo cacheado ---
@st.cache_resource(ttl=24 * 3600)
def get_graph(center):
    return ox.graph_from_point(center, dist=3000, network_type="drive")

# --- CSS mejorado ---
st.markdown("""
<style>
body, .stApp {background: #e8f0fe;}
.big-title {
    font-size: 2.3rem; font-weight: 700; color: #1863c2;
    text-align: center; margin-bottom: 1.1rem; margin-top: 0.4rem;
}
.subtitle {
    color: #1d3557; font-size: 1.1rem; margin-bottom: 1.4rem; text-align: center;
}
.stButton>button {
    height: 4rem !important; width: 12rem !important; font-size: 1.35rem !important; font-weight: 600;
    background: #1976d2 !important;
    color: #fff !important; border: none; border-radius: 12px; margin-right: 10px !important; margin-bottom: 8px !important;
    transition: 0.1s; box-shadow: 0 2px 12px #1976d222;
}
.stButton>button:hover {
    background: #115293 !important;
    color: #fff !important;
    transform: scale(1.04);
}
.card {
    border-radius: 16px;
    background: #fff;
    padding: 2rem 2rem 1rem 2rem;
    box-shadow: 0 2px 18px #1863c233;
    max-width: 1150px;
    margin: auto;
    margin-top: 10px;
}
.dist-box {
    background: #1976d2;
    color: #fff;
    padding: 1.1rem;
    font-size: 1.45rem;
    font-weight: 600;
    border-radius: 1.4rem;
    margin: 18px auto 10px auto;
    width: fit-content;
    box-shadow: 0 1px 8px #1976d244;
}
@media (max-width: 800px) {
  .card {padding: 0.8rem;}
}
</style>
""", unsafe_allow_html=True)

# --- Página ---
st.markdown('<div class="big-title">🚖 Rutas Óptimas en Puno</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Selecciona un punto de <b>inicio</b> y <b>fin</b> en el mapa.<br>Pulsa los botones según cada paso y encuentra la distancia más corta (en metros).</div>', unsafe_allow_html=True)

# --- Tarjeta principal ---
with st.container():
    st.markdown('<div class="card">', unsafe_allow_html=True)

    cols = st.columns([1, 1, 1, 1], gap="small")
    with cols[0]:
        if st.button("🔵 Inicio"):
            st.session_state.select_mode = "origin"
    with cols[1]:
        if st.button("🔴 Fin"):
            st.session_state.select_mode = "destination"
    with cols[2]:
        if st.button("▶️ Iniciar"):
            if st.session_state.origin and st.session_state.destination:
                with st.spinner("🔄 Calculando ruta…"):
                    G = get_graph(st.session_state.origin)
                    graph = {}
                    for u, v, data in G.edges(data=True):
                        w = data.get("length", 1)
                        graph.setdefault(u, []).append((v, w))
                        graph.setdefault(v, []).append((u, w))
                    src = ox.distance.nearest_nodes(
                        G, st.session_state.origin[1], st.session_state.origin[0],
                    )
                    dst = ox.distance.nearest_nodes(
                        G, st.session_state.destination[1], st.session_state.destination[0],
                    )
                    dist, ruta = dijkstra(graph, src, dst)
                    st.session_state.distance = dist
                    st.session_state.route_coords = [(G.nodes[n]["y"], G.nodes[n]["x"]) for n in ruta]
            else:
                st.warning("❗ Define origen y destino primero.")
    with cols[3]:
        if st.button("🔄 Reiniciar"):
            for key in ("origin", "destination", "route_coords", "distance", "select_mode"):
                st.session_state[key] = None

    # --- Mapa con OpenStreetMap (colorido) ---
    map_center = st.session_state.origin or [-15.84, -70.02]
    m = folium.Map(location=map_center, zoom_start=13, tiles="OpenStreetMap")

    if st.session_state.origin:
        folium.Marker(
            st.session_state.origin,
            popup="Inicio",
            icon=folium.Icon(color="blue", icon="play"),
        ).add_to(m)
    if st.session_state.destination:
        folium.Marker(
            st.session_state.destination,
            popup="Fin",
            icon=folium.Icon(color="red", icon="stop"),
        ).add_to(m)
    if st.session_state.route_coords:
        folium.PolyLine(
            locations=st.session_state.route_coords,
            color="#1976d2",
            weight=6
        ).add_to(m)

    map_data = st_folium(m, width=1100, height=620)
    if map_data and map_data.get("last_clicked"):
        lat, lng = map_data["last_clicked"]["lat"], map_data["last_clicked"]["lng"]
        if st.session_state.select_mode == "origin":
            st.session_state.origin = (lat, lng)
            st.session_state.route_coords = None
            st.session_state.distance = None
            st.session_state.select_mode = None
        elif st.session_state.select_mode == "destination":
            st.session_state.destination = (lat, lng)
            st.session_state.route_coords = None
            st.session_state.distance = None
            st.session_state.select_mode = None

    # --- Distancia final ---
    if st.session_state.distance is not None and st.session_state.distance != float("inf"):
        st.markdown(
            f'<div class="dist-box">Distancia mínima: {st.session_state.distance:.1f} metros</div>',
            unsafe_allow_html=True,
        )
    elif st.session_state.distance == float("inf"):
        st.error("No se encontró ruta posible entre los puntos.")

    st.markdown('</div>', unsafe_allow_html=True) 