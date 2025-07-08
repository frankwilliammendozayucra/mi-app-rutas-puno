import streamlit as st
import osmnx as ox
import folium
from streamlit_folium import st_folium
import heapq

# --- 0) Inicializar session_state ---
for key in ("origin", "destination", "route_coords", "distance", "select_mode"):
    if key not in st.session_state:
        st.session_state[key] = None

# --- 1) Implementación explícita de Dijkstra ---
def dijkstra(graph, source, target):
    dist = {node: float('inf') for node in graph}
    prev = {node: None for node in graph}
    dist[source] = 0
    visited = set()
    heap = [(0, source)]  # (distancia, nodo)

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

    # Reconstruir la ruta
    path = []
    u = target
    if dist[target] == float('inf'):
        return float('inf'), []
    while u is not None:
        path.append(u)
        u = prev[u]
    path.reverse()
    return dist[target], path

# --- 2) Grafo cacheado (3 km alrededor) ---
@st.cache_resource(ttl=24 * 3600)
def get_graph(center):
    return ox.graph_from_point(center, dist=3000, network_type="drive")

# --- 3) Configuración de la página ---
st.set_page_config(page_title="Calculadora de rutas Puno", layout="wide")
st.title("🚖 Calculadora de la ruta más corta en Puno")
st.markdown(
    "Pulsa **Inicio**, haz clic para fijarlo, pulsa **Fin**, haz clic para fijarlo, "
    "luego **Iniciar**, o **Reiniciar**."
)

# --- 4) CSS para botones grandes y espacio 10px ---
st.markdown(
    """
    <style>
      div.stButton {
        display: inline-block !important;
        margin: 0 10px !important;
      }
      div.stButton > button {
        height: 5rem !important;
        width: 14rem !important;
        font-size: 1.6rem !important;
      }
      div.stButton > button:hover {
        transform: scale(1.05);
      }
    </style>
    """,
    unsafe_allow_html=True,
)

# --- 5) Botones de control ---
if st.button("🔵 Inicio"):
    st.session_state.select_mode = "origin"
if st.button("🔴 Fin"):
    st.session_state.select_mode = "destination"
if st.button("▶️ Iniciar"):
    if st.session_state.origin and st.session_state.destination:
        with st.spinner("🔄 Calculando ruta…"):
            G = get_graph(st.session_state.origin)
            # Construir grafo de adyacencia
            graph = {}
            for u, v, data in G.edges(data=True):
                w = data.get("length", 1)
                graph.setdefault(u, []).append((v, w))
                graph.setdefault(v, []).append((u, w))
            # Obtener nodos origen y destino
            src = ox.distance.nearest_nodes(
                G,
                st.session_state.origin[1],
                st.session_state.origin[0],
            )
            dst = ox.distance.nearest_nodes(
                G,
                st.session_state.destination[1],
                st.session_state.destination[0],
            )
            # Ejecutar Dijkstra
            dist, ruta = dijkstra(graph, src, dst)
            # Guardar resultados
            st.session_state.distance = dist
            st.session_state.route_coords = [
                (G.nodes[n]["y"], G.nodes[n]["x"]) for n in ruta
            ]
    else:
        st.warning("❗ Primero define Origen y Destino.")
if st.button("🔄 Reiniciar"):
    for key in ("origin", "destination", "route_coords", "distance", "select_mode"):
        st.session_state[key] = None

# --- 6) Mapa base y captura de clics ---
map_center = st.session_state.origin or [-15.84, -70.02]
m = folium.Map(location=map_center, zoom_start=13)

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
        color="red",
        weight=5
    ).add_to(m)

map_data = st_folium(m, width=1200, height=700)
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

# --- 7) Mostrar distancia final ---
if st.session_state.distance is not None:
    st.markdown(f"**Distancia mínima:** {st.session_state.distance:.1f} metros")
