from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from cassandra.cluster import Cluster
from datetime import datetime
import uvicorn

app = FastAPI(title="SIG@ - HidroponiaPro V1")

# Conexión a Cassandra
try:
    cluster = Cluster(['127.0.0.1'], port=9042)
    session = cluster.connect('hidroponia_store')
except Exception as e:
    print(f"[ERROR CASSANDRA] {e}")

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    return """
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <title>SIG@ - HidroponiaPro</title>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <style>
            :root { --bg: #0f172a; --card: #1e293b; --text: #f8fafc; --accent: #38bdf8; }
            body { font-family: 'Inter', sans-serif; background: var(--bg); color: var(--text); margin: 0; padding: 20px; }
            .header { text-align: center; margin-bottom: 30px; border-bottom: 1px solid #334155; padding-bottom: 15px; }
            .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(350px, 1fr)); gap: 20px; max-width: 1200px; margin: 0 auto; }
            .card { background: var(--card); padding: 25px; border-radius: 16px; border: 1px solid #334155; }
            .stat-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-top: 15px; }
            .stat-box { background: #0f172a; padding: 15px; border-radius: 12px; text-align: center; border: 1px solid #475569; }
            .val-text { font-size: 1.8em; font-weight: bold; color: var(--accent); }
            
            /* --- DISEÑO DE BARRA DE PROGRESO (SEMÁFORO) --- */
            .progress-container {
                width: 100%;
                height: 18px;
                background: linear-gradient(to right, 
                    #fbbf24 0%, #fbbf24 30%,    /* Amarillo: Bajo */
                    #4ade80 30%, #4ade80 80%,   /* Verde: Normal */
                    #f87171 80%, #f87171 100%   /* Rojo: Alto */
                );
                border-radius: 10px;
                margin: 10px 0;
                position: relative;
                overflow: hidden;
                border: 1px solid #1e293b;
            }
            .progress-pointer {
                position: absolute;
                right: 0;
                top: 0;
                bottom: 0;
                background: rgba(15, 23, 42, 0.85); /* Tapa el resto de la barra */
                transition: width 0.6s cubic-bezier(0.4, 0, 0.2, 1);
                border-left: 3px solid #fff;
            }
        </style>
    </head>
    <body>
        <div class="header">
            <h1 style="color: var(--accent); margin:0;">HIDROPONIAPRO V1</h1>
            <p style="color: #94a3b8;">Sistema de Gestión Académica - Monitoreo de Cultivos</p>
        </div>

        <div class="grid">
            <div class="card">
                <h3>Histórico de Sensores</h3>
                <canvas id="hidroChart"></canvas>
            </div>
            <div class="card">
                <h3>Estado de los Estratos</h3>
                <div id="diagnostico" class="stat-grid"></div>
            </div>
        </div>

        <script>
            const ctx = document.getElementById('hidroChart').getContext('2d');
            const myChart = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: ['Temperatura', 'Humedad', 'pH', 'Luz'],
                    datasets: [{
                        data: [0, 0, 0, 0],
                        backgroundColor: ['#38bdf8', '#4ade80', '#fbbf24', '#f87171'], 
                        borderRadius: 8
                    }]
                },
                options: {
                    scales: { y: { beginAtZero: true, max: 100, grid: { color: '#334155' } } },
                    plugins: { legend: { display: false } }
                }
            });

            async function update() {
                try {
                    const res = await fetch(`/data?t=${new Date().getTime()}`);
                    const data = await res.json();
                    const map = { 'Temperatura': 0, 'Humedad': 1, 'pH': 2, 'Luz': 3 };
                    let diagHtml = '';

                    data.forEach(item => {
                        if(map[item.id] !== undefined) {
                            const index = map[item.id];
                            let valVisual = item.valor;

                            // Ajuste de escala para que la barra se mueva más
                            if (item.id === 'Temperatura') {
                                // Si quieres que 50°C sea el 100% de la barra, multiplica por 2
                                valVisual = item.valor * 2; 
                            } else if (item.id === 'pH') {
                                valVisual = item.valor * 7.14;
                            }
                            
                            // Limitar a 100 para que no se salga de la barra
                            valVisual = Math.min(valVisual, 100);

                            myChart.data.datasets[0].data[index] = valVisual;
                            let pointerWidth = Math.max(0, 100 - valVisual);

                            diagHtml += `
                                <div class="stat-box">
                                    <small style="color:#94a3b8; font-weight:bold;">${item.id.toUpperCase()}</small><br>
                                    <span class="val-text">${item.valor}</span>
                                    <div class="progress-container">
                                        <div class="progress-pointer" style="width: ${pointerWidth}%"></div>
                                    </div>
                                    <div style="display: flex; justify-content: space-between; font-size: 0.7em; color: #64748b;">
                                        <span>MIN</span><span>OK</span><span>MAX</span>
                                    </div>
                                </div>`;
                        }
                    });
                    myChart.update();
                    document.getElementById('diagnostico').innerHTML = diagHtml;
                } catch (e) { console.error("Error actualizando dashboard:", e); }
            }
            setInterval(update, 2000);
            update(); // Carga inicial
        </script>
    </body>
    </html>
    """

@app.get("/data")
@app.get("/data")
def get_sensor_data():
    try:
        nombres = ["Temperatura", "Humedad", "pH", "Luz"]
        resultados = []
        for nombre in nombres:
            # Añadimos ORDER BY si tu tabla lo permite, o simplemente LIMIT 1 
            # para obtener la última partición escrita.
            query = f"SELECT sensor_id, valor FROM sensor_data WHERE sensor_id = '{nombre}' LIMIT 1"
            
            # Forzamos a que no use resultados cacheados del driver
            row = session.execute(query).one()
            
            if row:
                resultados.append({"id": row.sensor_id, "valor": round(row.valor, 2)})
            else:
                # Si no hay dato, enviamos 0 para notar que hay conexión pero no datos
                resultados.append({"id": nombre, "valor": 0})
        return resultados
    except Exception as e:
        print(f"Error en consulta: {e}")
        return []

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)