#ECUACIONES PARA EL CÁLCULO DE COSTOS Y EMISIONES DE VEHÍCULOS
# Ecuación 1: Kilómetros del mes y del año
def km_mes(km_dia, dias=22):
    total = km_dia * dias
    return total

# Ecuación 2: Litros que gasta
def litros(km, consumo):
    if consumo <= 0:
        raise ValueError("El consumo debe ser mayor que 0")
    total = (km * consumo) / 100
    return total

# Ecuación 3: Costo en balboas
def costo(litros, precio):
    if precio <= 0:
        raise ValueError("El precio debe ser mayor que 0")
    total = litros * precio
    return total

# Ecuación 4: CO₂ emitido
def co2(litros, factor):
    if factor <= 0:
        raise ValueError("El factor de emisión debe ser mayor que 0")
    total = litros * factor
    return total

# Ecuación 5: Ahorro al comparar dos modelos
def comparar(resumen_a, resumen_b):
    if resumen_a["costo_mes"] < 0 or resumen_b["costo_mes"] < 0:
        raise ValueError("Los costos mensuales deben ser mayores que 0")
    if resumen_a["co2_mes"] < 0 or resumen_b["co2_mes"] < 0:
        raise ValueError("Las emisiones mensuales deben ser mayores que 0")

    dif_costo_mes = abs(resumen_a["costo_mes"] - resumen_b["costo_mes"])
    dif_costo_anio = abs(resumen_a["costo_anio"] - resumen_b["costo_anio"])
    dif_co2_mes = abs(resumen_a["co2_mes"] - resumen_b["co2_mes"])

    if resumen_a["costo_mes"] < resumen_b["costo_mes"]:
        mas_barato = "A"
    else:
        mas_barato = "B"

    return {
        "mas_barato": mas_barato,
        "ahorro_mes": dif_costo_mes,
        "ahorro_anio": dif_costo_anio,
        "co2_evitado": dif_co2_mes,
    }

# Ecuación 6: «Otro modelo»: de km/L a L/100 km
def kml_a_l100(km_por_litro):
    if km_por_litro <= 0:
        raise ValueError("Los km por litro deben ser mayores que 0")
    total = 100 / km_por_litro
    return total


# Ranking: costo cada 100 km
def costo_100km(consumo, precio):
    if consumo <= 0 or precio <= 0:
        raise ValueError("El consumo y el precio deben ser mayores que 0")
    total = consumo * precio
    return total

# Ecuación 7: Variación porcentual (Historia 2021–2026)
def variacion(inicial, final):
    if inicial <= 0:
        raise ValueError("El valor inicial debe ser mayor que 0")
    total = ((final - inicial) / inicial) * 100
    return total

# Ecuación 8: Costo cada 100 km en un año
def costo_100km_anio(consumo_anio, precio_promedio_anio):
    if consumo_anio <= 0 or precio_promedio_anio <= 0:
        raise ValueError("El consumo y el precio deben ser mayores que 0")
    total = consumo_anio * precio_promedio_anio
    return total

# Resumen de un vehículo
def resumen(vehiculo, km_dia, dias, precios, factores):
    combustible = vehiculo.combustible

    if combustible not in precios:
        raise ValueError("No hay precio para el combustible: " + combustible)

    if combustible == "diesel":
        clave_factor = "diesel"
    else:
        clave_factor = "gasolina"

    km = km_mes(km_dia, dias)
    litros_mes = litros(km, vehiculo.consumo)
    costo_mes = costo(litros_mes, precios[combustible])
    co2_mes = co2(litros_mes, factores[clave_factor])

    return {
        "litros_mes": litros_mes,
        "costo_mes": costo_mes,
        "co2_mes": co2_mes,
        "costo_anio": costo_mes * 12,
        "co2_anio": co2_mes * 12,
    }



# PRUEBAS: tabla  de verificación

if __name__ == "__main__":

    # Vehículo de mentira, solo para probar
    class VehiculoPrueba:
        def __init__(self, consumo, combustible):
            self.consumo = consumo
            self.combustible = combustible

    # Compara un resultado con el valor oficial, con una tolerancia
    def verificar(nombre, valor, esperado, tolerancia=0.01):
        assert abs(valor - esperado) <= tolerancia, (
            nombre + ": obtuve " + str(valor) + " y esperaba " + str(esperado)
        )
        print("OK  " + nombre + " =", round(valor, 2))

    # Datos de la tabla 
    precios = {"gasolina_91": 1.102, "diesel": 1.434}
    factores = {"gasolina": 2.302, "diesel": 2.803}

    corolla = VehiculoPrueba(6.7, "gasolina_91")
    tucson = VehiculoPrueba(8.8, "gasolina_91")

    # Kilómetros: 40 km/día x 22 días 
    verificar("Km al mes", km_mes(40, 22), 880)

    # Toyota Corolla
    r_corolla = resumen(corolla, 40, 22, precios, factores)
    verificar("Corolla litros/mes", r_corolla["litros_mes"], 58.96)
    verificar("Corolla costo/mes", r_corolla["costo_mes"], 64.97)
    verificar("Corolla CO2/mes", r_corolla["co2_mes"], 135.7, 0.05)

    # Hyundai Tucson
    r_tucson = resumen(tucson, 40, 22, precios, factores)
    verificar("Tucson litros/mes", r_tucson["litros_mes"], 77.44)
    verificar("Tucson costo/mes", r_tucson["costo_mes"], 85.34)
    verificar("Tucson CO2/mes", r_tucson["co2_mes"], 178.3, 0.05)

    # Comparar Tucson vs Corolla
    comp = comparar(r_tucson, r_corolla)
    verificar("Diferencia de litros", r_tucson["litros_mes"] - r_corolla["litros_mes"], 18.48)
    verificar("Ahorro al mes", comp["ahorro_mes"], 20.36)
    verificar("CO2 evitado al mes", comp["co2_evitado"], 42.5, 0.05)
    assert comp["mas_barato"] == "B", "El más barato debía ser el Corolla (B)"
    print("OK  Más barato = Corolla")

    # Otro modelo: diésel, 10 km/L 
    consumo_otro = kml_a_l100(10)
    verificar("Otro modelo L/100 km", consumo_otro, 10)
    r_otro = resumen(VehiculoPrueba(consumo_otro, "diesel"), 40, 22, precios, factores)
    verificar("Otro modelo litros/mes", r_otro["litros_mes"], 88.00)
    verificar("Otro modelo costo/mes", r_otro["costo_mes"], 126.19)
    verificar("Otro modelo CO2/mes", r_otro["co2_mes"], 246.7, 0.05)

    # Costo cada 100 km del Corolla
    verificar("Corolla litros/100 km", litros(100, 6.7), 6.7)
    verificar("Corolla costo/100 km", costo_100km(6.7, 1.102), 7.38)
    verificar("Corolla CO2/100 km", co2(6.7, 2.302), 15.4, 0.05)

    # Historia 2021-2026
    verificar("Variación gasolina 91 (%)", variacion(0.737, 1.102), 49.5, 0.05)
    kicks_2021 = costo_100km_anio(7.2, 0.866)
    kicks_2026 = costo_100km_anio(7.4, 1.122)
    verificar("Kicks 2021 costo/100 km", kicks_2021, 6.23)
    verificar("Kicks 2026 costo/100 km", kicks_2026, 8.30)
    verificar("Kicks variación (%)", variacion(kicks_2021, kicks_2026), 33.2, 0.05)
    verificar("Variación CO2 promedio (%)", variacion(258.9, 252.4), -2.5, 0.05)

    # Validación: dividir entre 0 debe dar error
    try:
        kml_a_l100(0)
        raise AssertionError("kml_a_l100(0) debió dar error")
    except ValueError:
        print("OK  kml_a_l100(0) da error, como debe")

    print("\nTodas las pruebas pasaron.")