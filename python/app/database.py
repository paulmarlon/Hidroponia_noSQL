from cassandra.cluster import Cluster

def get_cassandra_session():
    # Estas son las IPs que confirmamos en el nodetool status
    contact_points = ['192.168.2.108', '192.168.2.100']
    
    try:
        # Definimos el cluster usando los puntos de contacto
        cluster = Cluster(contact_points)
        
        # Intentamos conectar al Keyspace
        session = cluster.connect('hidroponia_keyspace')
        return session
    except Exception as e:
        # Si falla, nos dirá exactamente por qué (IP, puerto o Keyspace)
        print(f"Error de conexión en PC 2: {e}")
        return None