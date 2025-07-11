import streamlit as st
import osmnx as ox
import folium
from streamlit_folium import st_folium
from geopy.distance import geodesic

# Configuración de la página
st.set_page_config(
    page_title="Rutas Óptimas en Puno",
    page_icon="🚗",
    layout="wide"
)

# --- ESTILOS CSS para profesionalismo ---
st.markdown("""
<style>
body, .stApp {background: #181d2a;}
h1, h2, h3, h4, h5, h6 {color: #e74c3c;}
.bigtxt {font-size:2.4rem;font-weight:800; color:#e74c3c; letter-spacing:-1px;}
.subtitle {font-size:1.18rem;color:#d2dbe5;font-weight:500;margin-bottom:22px;}
.stSelectbox>div>div {font-size:1.05rem !important;}
.result-card {
    background: #222944;
    color: #fff;
    border-radius: 16px;
    box-shadow: 0 2px 16px #171d36aa;
    padding: 2rem 1.5rem 1.5rem 1.5rem;
    margin: 20px 0 28px 0;
    font-size:1.08rem;
}
.dist-box {
    background: #1976d2;
    color: #fff;
    font-size: 1.35rem;
    font-weight:700;
    border-radius: 13px;
    padding: 1.1rem 2rem;
    margin: 8px auto 18px auto;
    box-shadow:0 2px 9px #1976d244;
    width:fit-content;
}
.ruta-pasos {
    background:#131726;
    color:#c4e1f9;
    border-radius: 13px;
    padding: 1.1rem 2rem;
    font-size: 1.14rem;
    font-weight: 500;
    margin-bottom: 20px;
}
.stButton>button {
    background: #e74c3c !important;
    color: #fff !important;
    font-size: 1.11rem;
    border-radius: 10px !important;
    font-weight: 700 !important;
    margin-bottom: 6px;
}
.stButton>button:hover {
    background: #b5331a !important;
    color: #fff !important;
}
</style>
""", unsafe_allow_html=True)

# ---- Diccionario de lugares y coordenadas ----
lugares = {
    "Plaza de Armas": (-15.840660, -70.027979),
    "Universidad Nacional del Altiplano": (-15.824488, -70.016197),
    "Parque Pino": (-15.837954, -70.028065),
    "Terminal Terrestre Puno": (-15.843733, -70.017322),
    "Terminal Zonal Sur Virgen de Fátima": (-15.840935, -70.020578),
    "Mercado Central": (-15.837475, -70.026585),
    "Estadio Enrique Torres Belón": (-15.836865, -70.022104),
    "Catedral de Puno": (-15.840837, -70.028775),
    "Museo Carlos Dreyer": (-15.840548, -70.028945),
    "Iglesia San Juan Bautista": (-15.837834, -70.028405),
    "Parque Mariategui": (-15.839410, -70.024507),
    "Parque Huajsapata": (-15.840968, -70.023360),
    "Centro Comercial Plaza Vea": (-15.836654, -70.025571),
    "Hotel Libertador Lago Titicaca": (-15.827975, -69.99301),
    "Puerto de Puno": (-15.835072, -70.014308),
    "Colegio Glorioso San Carlos": (-15.835377, -70.023954),
    "Colegio María Auxiliadora": (-15.838374, -70.032358),
    "Hotel Casa Andina Premium": (-15.823534, -69.997105),
    "Mirador Kuntur Wasi": (-15.847225, -70.029925)
}

categorias_emojis = {
    "hospital": "🏥", "universidad": "🎓", "plaza": "🏛️", "parque": "🌳",
    "terminal": "🚌", "mercado": "🏬", "estadio": "🏟️", "iglesia": "⛪",
    "catedral": "⛪", "hotel": "🏨", "puerto": "⛴️", "mirador": "🔭",
    "colegio": "🏫", "museo": "🏺", "supermercado": "🛒"
}
def obtener_emoji(nombre):
    nombre_lc = nombre.lower()
    if "hospital" in nombre_lc: return categorias_emojis["hospital"]
    elif "universidad" in nombre_lc: return categorias_emojis["universidad"]
    elif "plaza" in nombre_lc: return categorias_emojis["plaza"]
    elif "parque" in nombre_lc: return categorias_emojis["parque"]
    elif "terminal" in nombre_lc: return categorias_emojis["terminal"]
    elif "mercado" in nombre_lc: return categorias_emojis["mercado"]
    elif "estadio" in nombre_lc: return categorias_emojis["estadio"]
    elif "iglesia" in nombre_lc: return categorias_emojis["iglesia"]
    elif "catedral" in nombre_lc: return categorias_emojis["catedral"]
    elif "hotel" in nombre_lc: return categorias_emojis["hotel"]
    elif "puerto" in nombre_lc: return categorias_emojis["puerto"]
    elif "mirador" in nombre_lc: return categorias_emojis["mirador"]
    elif "colegio" in nombre_lc: return categorias_emojis["colegio"]
    elif "museo" in nombre_lc: return categorias_emojis["museo"]
    elif "supermercado" in nombre_lc or "plaza vea" in nombre_lc: return categorias_emojis["supermercado"]
    else: return "📍"

st.markdown('<div class="bigtxt">🚗 Rutas Óptimas en Puno</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Selecciona el <b>origen</b> y <b>destino</b> entre los lugares principales.<br>Visualiza el trayecto, nodos destacados y pasos.</div>', unsafe_allow_html=True)

col1, col2 = st.columns(2)
with col1:
    origen_nombre = st.selectbox("¿Dónde estás?", list(lugares.keys()), index=0)
with col2:
    destino_nombre = st.selectbox("¿A dónde quieres ir?", list(lugares.keys()), index=1)

coord_origen = lugares[origen_nombre]
coord_destino = lugares[destino_nombre]

st.markdown(
    f"""<div class="result-card">
    <b>Origen:</b> {obtener_emoji(origen_nombre)} <span style='color:#a6d1ff'>{origen_nombre}</span>
    <br><b>Destino:</b> {obtener_emoji(destino_nombre)} <span style='color:#ffd2d2'>{destino_nombre}</span>
    </div>""", unsafe_allow_html=True)

def es_nodo_cercano(coord_nodo, coord_lugar, tolerancia_metros=100):
    return geodesic(coord_nodo, coord_lugar).meters < tolerancia_metros

if origen_nombre == destino_nombre:
    st.warning("Selecciona dos lugares diferentes para calcular la ruta.")
else:
    @st.cache_resource(ttl=24*3600)
    def cargar_grafo(center=(-15.840221, -70.021881)):
        return ox.graph_from_point(center, dist=4000, network_type="drive")
    G = cargar_grafo()

    try:
        src = ox.distance.nearest_nodes(G, coord_origen[1], coord_origen[0])
        dst = ox.distance.nearest_nodes(G, coord_destino[1], coord_destino[0])
        ruta = ox.shortest_path(G, src, dst, weight="length")

        # Calcular la distancia total (metros)
        distancia = 0
        for u, v in zip(ruta[:-1], ruta[1:]):
            data = min(G.get_edge_data(u, v).values(), key=lambda d: d.get("length", 0))
            distancia += data.get("length", 0)

        # Detectar lugares de paso
        nodos_ruta = [(G.nodes[n]["y"], G.nodes[n]["x"]) for n in ruta]
        lugares_en_ruta, ya_agregados = [], set()
        for lat, lon in nodos_ruta:
            for nombre_lugar, coord in lugares.items():
                if nombre_lugar not in ya_agregados and es_nodo_cercano((lat, lon), coord):
                    lugares_en_ruta.append(nombre_lugar)
                    ya_agregados.add(nombre_lugar)
        # Origen y destino siempre aparecen
        if lugares_en_ruta and lugares_en_ruta[0] != origen_nombre:
            lugares_en_ruta = [origen_nombre] + [n for n in lugares_en_ruta if n != origen_nombre]
        if lugares_en_ruta and lugares_en_ruta[-1] != destino_nombre:
            lugares_en_ruta = [n for n in lugares_en_ruta if n != destino_nombre] + [destino_nombre]

        # ---- MAPA ----
        m = folium.Map(location=coord_origen, zoom_start=15, tiles="OpenStreetMap")
        for nombre_lugar, coord in lugares.items():
            emoji = obtener_emoji(nombre_lugar)
            folium.Marker(
                coord,
                popup=f"{emoji} {nombre_lugar}",
                icon=folium.Icon(color="green" if nombre_lugar not in [origen_nombre, destino_nombre] else ("blue" if nombre_lugar == origen_nombre else "red"),
                                 icon="info-sign")
            ).add_to(m)
        puntos = [(G.nodes[n]["y"], G.nodes[n]["x"]) for n in ruta]
        folium.PolyLine(puntos, color="#1976d2", weight=7, opacity=0.9).add_to(m)

        st.markdown(f'<div class="dist-box">🛣️ Distancia total: {distancia:.1f} metros</div>', unsafe_allow_html=True)
        st_folium(m, width=1500, height=520)

        # Pasos de la ruta
        if lugares_en_ruta:
            st.markdown(
                '<div class="ruta-pasos">🧭 <b>La ruta pasa por:</b><br>' +
                "<br>".join([f"{obtener_emoji(n)} {n}" for n in lugares_en_ruta]) +
                '</div>',
                unsafe_allow_html=True
            )
        else:
            st.info("La ruta no pasa por otros lugares principales de la lista.")
    except Exception as e:
        st.error("No se pudo encontrar una ruta entre los lugares seleccionados.")
        st.write(str(e))
