import streamlit as st
import pandas as pd

# -------------------------------------------------------------------------
# CONSTANTES GLOBALES
# -------------------------------------------------------------------------
LOTES_A_UNIDADES = 100  # 1 lote = 100 unidades
PASO = 5  # Paso de precio ajustado a 5 unidades
TOTAL_UNIDADES = 120  # Total de unidades a cubrir
DIVISOR_LOTE = 1.5932  # Divisor para ajustar los lotajes

# -------------------------------------------------------------------------
# FUNCIONES AUXILIARES
# -------------------------------------------------------------------------

def generar_precios(precio_inicial, total_unidades, paso=5):
    """
    Genera una lista de precios decrecientes desde precio_inicial hasta precio_inicial - total_unidades
    con decrementos de 'paso' unidades.
    """
    numero_puntos = total_unidades // paso + 1  # +1 para incluir el precio final
    precios = [precio_inicial - i * paso for i in range(numero_puntos)]
    return precios

def asignar_lotes(precio_inicial, precios):
    """
    Asigna lotes basados en la diferencia de precio desde el precio inicial.
    """
    lotes = []
    for precio in precios:
        diferencia = precio_inicial - precio
        if 0 <= diferencia <= 15:
            lotes.append(0.5)
        elif diferencia == 20:
            lotes.append(0.0)
        elif diferencia in [25, 30]:
            lotes.append(2.0)
        elif 35 <= diferencia <= 55:
            if diferencia == 55:
                lotes.append(0.0)
            else:
                lotes.append(0.625)
        elif diferencia == 60:
            lotes.append(6.0)
        elif 65 <= diferencia <= 90:
            lotes.append(2.0)
        elif 91 <= diferencia <= 94:
            lotes.append(1.5)
        elif 95 <= diferencia <= 120:
            lotes.append(3.375)
        else:
            lotes.append(0.5)
    
    # Dividir todos los lotajes entre 1.5932
    lotes_ajustados = [lote / DIVISOR_LOTE for lote in lotes]
    return lotes_ajustados

def crear_dataframe(precios, lotes):
    """
    Crea un DataFrame con los precios y los lotes asignados.
    """
    df = pd.DataFrame({
        'Precio': precios,
        'Lotes': lotes
    })
    return df

def calcular_acumulados(df, precio_inicial):
    """
    Calcula los lotes acumulados, costo acumulado, break-even, flotante, puntos de salida y ganancia potencial.
    """
    df['Lotes Acumulados'] = df['Lotes'].cumsum()
    df['Costo Acumulado'] = (df['Precio'] * df['Lotes'] * LOTES_A_UNIDADES).cumsum()
    df['Break Even'] = df['Costo Acumulado'] / (df['Lotes Acumulados'] * LOTES_A_UNIDADES)
    df['Flotante'] = (df['Precio'] - df['Break Even']) * (df['Lotes Acumulados'] * LOTES_A_UNIDADES)
    # Agregar la columna 'Puntos de salida'
    df['Puntos de salida'] = abs(df['Precio'] - df['Break Even'])
    # Calcular la 'Ganancia Potencial' si el precio regresa al precio inicial
    df['Ganancia Potencial'] = (precio_inicial - df['Break Even']) * (df['Lotes Acumulados'] * LOTES_A_UNIDADES)
    return df

def validar_precio_final(df, precio_esperado):
    """
    Verifica que el último precio en el DataFrame sea igual al precio esperado.
    """
    ultimo_precio_calculado = df['Precio'].iloc[-1]
    if ultimo_precio_calculado != precio_esperado:
        st.error(f"Error: El último precio calculado es {ultimo_precio_calculado}, pero se esperaba {precio_esperado}.")
        return False
    return True

# -------------------------------------------------------------------------
# APLICACIÓN PRINCIPAL DE STREAMLIT
# -------------------------------------------------------------------------

def main():
    st.title("Calculadora")
    
    # Entrada del usuario: Precio inicial
    precio_inicial = st.number_input(
        "Precio inicial del oro (p):",
        min_value=1.00,
        value=2700.00,
        step=5.00,  # Paso ajustado a 5 unidades
        format="%.2f"
    )
    
    # Botón para ejecutar el cálculo
    if st.button("Calcular Distribución en Tramos"):
        # Generar lista de precios
        precios = generar_precios(precio_inicial, TOTAL_UNIDADES, PASO)
        
        # Asignar lotes según las reglas y ajustar
        lotes = asignar_lotes(precio_inicial, precios)
        
        # Verificar que las listas tengan la misma longitud
        if len(precios) != len(lotes):
            st.error("Error: Las listas de precios y lotes no tienen la misma longitud.")
        else:
            # Crear DataFrame
            df = crear_dataframe(precios, lotes)
            
            # Calcular acumulados (ahora pasamos 'precio_inicial' como parámetro)
            df = calcular_acumulados(df, precio_inicial)
            
            # Redondear valores para mejor visualización
            df['Precio'] = df['Precio'].round(2)
            df['Lotes'] = df['Lotes'].round(4)  # Más decimales para lotajes ajustados
            df['Lotes Acumulados'] = df['Lotes Acumulados'].round(4)
            df['Costo Acumulado'] = df['Costo Acumulado'].round(2)
            df['Break Even'] = df['Break Even'].round(2)
            df['Flotante'] = df['Flotante'].round(2)
            df['Puntos de salida'] = df['Puntos de salida'].round(2)
            df['Ganancia Potencial'] = df['Ganancia Potencial'].round(2)
            
            # Calcular precio esperado
            precio_esperado = precio_inicial - TOTAL_UNIDADES  # p - 120
            
            # Validar el precio final
            es_valido = validar_precio_final(df, precio_esperado)
            
            if es_valido:
                # Mostrar resultados
                st.write("### Detalles de las Transacciones:")
                st.dataframe(df)
                
                # Mostrar break-even final, flotante total y ganancia potencial final
                break_even_final = df['Break Even'].iloc[-1]
                flotante_total = df['Flotante'].iloc[-1]
                ganancia_potencial_total = df['Ganancia Potencial'].iloc[-1]
                total_lotes_acumulados = df['Lotes Acumulados'].iloc[-1]
                
                st.write(f"### Break-Even Final: {break_even_final:.2f}")
                st.write(f"### Flotante Total: {flotante_total:.2f}")
                st.write(f"### Ganancia Potencial Total: {ganancia_potencial_total:.2f}")
                st.write(f"### Total de Lotes Acumulados: {total_lotes_acumulados:.4f} lotes")
    
# Ejecutar la aplicación
if __name__ == "__main__":
    main()
