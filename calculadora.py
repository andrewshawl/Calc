import streamlit as st
import pandas as pd

# -------------------------------------------------------------------------
# CONSTANTES GLOBALES
# -------------------------------------------------------------------------
LOTES_A_UNIDADES = 100  # 1 lote = 100 unidades

# -------------------------------------------------------------------------
# FUNCIONES AUXILIARES
# -------------------------------------------------------------------------

def generar_precios_decrecientes(precio_inicial, precio_final, paso=5):
    """
    Genera una lista de precios decrecientes desde precio_inicial hasta precio_final en pasos de 'paso'.
    """
    if precio_final > precio_inicial:
        precio_inicial, precio_final = precio_final, precio_inicial
    return list(range(int(precio_inicial), int(precio_final) - 1, -paso))

def repartir_compras_por_promedio(precios, precio_objetivo):
    """
    Asigna lotes base para cada nivel de precio:
      - 1 lote si el precio está por encima del objetivo.
      - 5 lotes si el precio está por debajo del objetivo.
      - 0 lotes si el precio es igual al objetivo.

    Retorna un DataFrame con las asignaciones base.
    """
    data = []
    for p in precios:
        if p > precio_objetivo:
            lotes_base = 1
        elif p < precio_objetivo:
            lotes_base = 5
        else:
            lotes_base = 0  # No afecta el promedio
        data.append({"Precio": p, "Lotes_base": lotes_base})
    return pd.DataFrame(data)

def escalar_hasta_lotes(df_compras, lotes_deseados):
    """
    Escala los lotes base para que el total de lotes en el tramo sea igual a 'lotes_deseados'.
    Calcula el costo parcial y retorna el DataFrame escalado junto con el promedio resultante.
    """
    suma_base = df_compras['Lotes_base'].sum()
    if suma_base == 0:
        factor_escala = 0
    else:
        factor_escala = lotes_deseados / suma_base

    df_compras['Lotes'] = df_compras['Lotes_base'] * factor_escala
    df_compras['Costo parcial'] = df_compras['Precio'] * df_compras['Lotes'] * LOTES_A_UNIDADES

    return df_compras

def calcular_promedio_ponderado(costo_total, lotes_total):
    """
    Calcula el promedio ponderado dado el costo total y la cantidad total de lotes.
    """
    if lotes_total == 0:
        return 0
    return costo_total / (lotes_total * LOTES_A_UNIDADES)

def calcular_flotante(precio_actual, promedio_ponderado, lotes_total):
    """
    Calcula el flotante (ganancia/pérdida no realizada).
    """
    return (precio_actual - promedio_ponderado) * (lotes_total * LOTES_A_UNIDADES)

# -------------------------------------------------------------------------
# APLICACIÓN PRINCIPAL DE STREAMLIT
# -------------------------------------------------------------------------

def main():
    st.title("Calculadora de Compras en Tramos con Break-Even")

    # Entrada del usuario: Precio inicial
    precio_inicial = st.number_input(
        "Precio inicial del oro (p):",
        min_value=1.00,
        value=2700.00,
        step=5.00,
        format="%.2f"
    )

    # Botón para ejecutar el cálculo
    if st.button("Calcular Distribución en Tramos"):
        # Definir los tramos dinámicamente basado en el precio inicial
        tramos = [
            {
                "nombre": "Tramo 1",
                "inicio": precio_inicial,
                "fin": precio_inicial - 100,
                "lotes_deseados": 2 * 1.25,  # 2.5 lotes
                "break_even_objetivo": precio_inicial - 70
            },
            {
                "nombre": "Tramo 2",
                "inicio": precio_inicial - 100,
                "fin": precio_inicial - 200
                # No necesitamos 'lotes_deseados' ni 'break_even_objetivo' para Tramo 2
            },
            {
                "nombre": "Tramo 3",
                "inicio": precio_inicial - 200,
                "fin": precio_inicial - 300
                # No necesitamos 'lotes_deseados' ni 'break_even_objetivo' para Tramo 3
            }
        ]

        # Inicializar variables acumulativas
        transacciones_acumuladas = []
        costo_total_acumulado = 0
        lotes_total_acumulado = 0

        # Variables acumulativas para cálculos paso a paso
        costo_acumulado = 0
        lotes_acumulados = 0

        for tramo in tramos:
            # Generar precios para el tramo
            precios_tramo = generar_precios_decrecientes(tramo["inicio"], tramo["fin"], paso=5)
            
            if tramo["nombre"] == "Tramo 1":
                # Repartir compras por promedio objetivo
                df_base = repartir_compras_por_promedio(precios_tramo, tramo["break_even_objetivo"])
                
                # Escalar para cumplir con los lotes deseados en el tramo
                df_escalado = escalar_hasta_lotes(df_base, tramo["lotes_deseados"])
                
                # Añadir columna de tramo
                df_escalado['Tramo'] = tramo["nombre"]
                
                # Calcular lotes y costo acumulado paso a paso
                df_escalado['Lotes Acumulados'] = df_escalado['Lotes'].cumsum() + lotes_acumulados
                df_escalado['Costo Acumulado'] = df_escalado['Costo parcial'].cumsum() + costo_acumulado
                
                # Calcular break even (promedio ponderado) paso a paso
                df_escalado['Break Even'] = df_escalado['Costo Acumulado'] / (df_escalado['Lotes Acumulados'] * LOTES_A_UNIDADES)
                
                # Calcular flotante paso a paso usando el precio actual en cada fila
                df_escalado['Flotante'] = (df_escalado['Precio'] - df_escalado['Break Even']) * (df_escalado['Lotes Acumulados'] * LOTES_A_UNIDADES)
                
                # Guardar los lotajes del Tramo 1 para usarlos en Tramo 3
                lotajes_tramo1 = df_escalado[['Precio', 'Lotes']].set_index('Precio')['Lotes'].to_dict()
                
                # Actualizar acumulados para el siguiente tramo
                costo_acumulado = df_escalado['Costo Acumulado'].iloc[-1]
                lotes_acumulados = df_escalado['Lotes Acumulados'].iloc[-1]
                
                # Agregar al acumulado de transacciones
                transacciones_acumuladas.append(df_escalado)
            
            elif tramo["nombre"] == "Tramo 2":
                # Crear DataFrame personalizado para Tramo 2 según tus especificaciones
                data = []
                for p_tramo in precios_tramo:
                    if p_tramo > (precio_inicial - 175):
                        # Hasta llegar a p - 175, usa el lotaje base de 0.0568 * 1.3542
                        lotes_base = 0.0568 * 1.3542
                    elif p_tramo == (precio_inicial - 175):
                        # En p - 175, usa 0 lotes
                        lotes_base = 0
                    else:  # Desde p - 175 hasta p - 200, usa 0.568 lotes * 1.3542
                        lotes_base = 0.568 * 1.3542
                    data.append({"Precio": p_tramo, "Lotes": lotes_base})
                df_escalado = pd.DataFrame(data)
                
                # Calcular costo parcial
                df_escalado['Costo parcial'] = df_escalado['Precio'] * df_escalado['Lotes'] * LOTES_A_UNIDADES
                
                # Añadir columna de tramo
                df_escalado['Tramo'] = tramo["nombre"]
                
                # Calcular lotes y costo acumulado paso a paso
                df_escalado['Lotes Acumulados'] = df_escalado['Lotes'].cumsum() + lotes_acumulados
                df_escalado['Costo Acumulado'] = df_escalado['Costo parcial'].cumsum() + costo_acumulado
                
                # Calcular break even (promedio ponderado) paso a paso
                df_escalado['Break Even'] = df_escalado['Costo Acumulado'] / (df_escalado['Lotes Acumulados'] * LOTES_A_UNIDADES)
                
                # Calcular flotante paso a paso usando el precio actual en cada fila
                df_escalado['Flotante'] = (df_escalado['Precio'] - df_escalado['Break Even']) * (df_escalado['Lotes Acumulados'] * LOTES_A_UNIDADES)
                
                # Actualizar acumulados para el siguiente tramo
                costo_acumulado = df_escalado['Costo Acumulado'].iloc[-1]
                lotes_acumulados = df_escalado['Lotes Acumulados'].iloc[-1]
                
                # Agregar al acumulado de transacciones
                transacciones_acumuladas.append(df_escalado)
            
            elif tramo["nombre"] == "Tramo 3":
                # Crear DataFrame personalizado para Tramo 3 según tus especificaciones
                data = []
                for p_tramo in precios_tramo:
                    if (precio_inicial - 280) < p_tramo <= (precio_inicial - 200):
                        # Asignar 0.0568 lotes para precios entre p-200 y p-280
                        lotes_base = 0.0568
                    elif p_tramo == (precio_inicial - 280):
                        # En p - 280, usa 0 lotes
                        lotes_base = 0
                    else:  # Desde p - 200 hasta p - 300, usa 0.852 lotes
                        lotes_base = 0.852
                    # Multiplicar el lotaje por 1.7373
                    lotes_base *= 1.7373
                    data.append({"Precio": p_tramo, "Lotes": lotes_base})
                df_escalado = pd.DataFrame(data)
                
                # Calcular costo parcial
                df_escalado['Costo parcial'] = df_escalado['Precio'] * df_escalado['Lotes'] * LOTES_A_UNIDADES
                
                # Añadir columna de tramo
                df_escalado['Tramo'] = tramo["nombre"]
                
                # Calcular lotes y costo acumulado paso a paso
                df_escalado['Lotes Acumulados'] = df_escalado['Lotes'].cumsum() + lotes_acumulados
                df_escalado['Costo Acumulado'] = df_escalado['Costo parcial'].cumsum() + costo_acumulado
                
                # Calcular break even (promedio ponderado) paso a paso
                df_escalado['Break Even'] = df_escalado['Costo Acumulado'] / (df_escalado['Lotes Acumulados'] * LOTES_A_UNIDADES)
                
                # Calcular flotante paso a paso usando el precio actual en cada fila
                df_escalado['Flotante'] = (df_escalado['Precio'] - df_escalado['Break Even']) * (df_escalado['Lotes Acumulados'] * LOTES_A_UNIDADES)
                
                # Actualizar acumulados para el siguiente tramo
                costo_acumulado = df_escalado['Costo Acumulado'].iloc[-1]
                lotes_acumulados = df_escalado['Lotes Acumulados'].iloc[-1]
                
                # Agregar al acumulado de transacciones
                transacciones_acumuladas.append(df_escalado)
        
        # Concatenar todos los tramos
        df_final = pd.concat(transacciones_acumuladas, ignore_index=True)

        # Reorganizar columnas eliminando las que no son necesarias
        df_final = df_final[[
            'Tramo',
            'Precio',
            'Lotes',
            'Lotes Acumulados',
            'Break Even',
            'Flotante'
        ]]

        # Redondear valores para mejor visualización
        df_final['Precio'] = df_final['Precio'].round(2)
        df_final['Lotes'] = df_final['Lotes'].round(6)
        df_final['Lotes Acumulados'] = df_final['Lotes Acumulados'].round(6)
        df_final['Break Even'] = df_final['Break Even'].round(4)
        df_final['Flotante'] = df_final['Flotante'].round(2)

        # Mostrar resultados
        st.write("### Detalles de las Transacciones:")
        st.dataframe(df_final)

        # Mostrar break-even final y flotante total
        st.write(f"### Break-Even Final: {df_final['Break Even'].iloc[-1]:.4f}")
        st.write(f"### Flotante Total: {df_final['Flotante'].iloc[-1]:.2f}")

        # Validar que se hayan acumulado los lotes correctos
        st.write(f"### Total de Lotes Acumulados: {df_final['Lotes Acumulados'].iloc[-1]:.6f}")

# Ejecutar la aplicación
if __name__ == "__main__":
    main()
