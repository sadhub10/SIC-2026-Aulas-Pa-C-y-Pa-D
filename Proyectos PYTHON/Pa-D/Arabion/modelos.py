"""modelos.py - Clase Vehiculo de EcoTrace AI.

= Alan Aguilar

L1: Ajustado para seguir la tabla de modelos.py de la página "Stack y tareas" del Notion (atributos y métodos que usan datos.py, calculos.py, reportes.py y app.py).
"""


class Vehiculo:
    """Un carro del catálogo de Panamá (o el «otro modelo» que escribe el usuario)."""

    def __init__(self, marca, modelo, tipo, motor, combustible, consumo):
        self.marca = marca              # "Toyota"
        self.modelo = modelo            # "Corolla"
        self.tipo = tipo                # "Sedán" o "SUV"
        self.motor = motor              # tamaño del motor en litros, por ejemplo 2.0
        self.combustible = combustible  # "gasolina_91", "gasolina_95" o "diesel"
        self.consumo = consumo          # litros cada 100 km (L/100 km)

    def nombre(self):
        """Marca y modelo, por ejemplo «Toyota Corolla»."""
        return f"{self.marca} {self.modelo}"

    def costo_100km(self, precios):
        """Balboas que cuesta recorrer 100 km con el precio de su combustible."""
        return self.consumo * precios[self.combustible]

    def co2_100km(self, factores):
        """Kilos de CO2 cada 100 km. La gasolina 91 y 95 usan el factor de gasolina."""
        if self.combustible == "diesel":
            factor = factores["diesel"]
        else:
            factor = factores["gasolina"]
        return self.consumo * factor

    def a_diccionario(self):
        """Los datos del vehículo en un diccionario (para JSON y para armar tablas)."""
        return {
            "marca": self.marca,
            "modelo": self.modelo,
            "tipo": self.tipo,
            "motor": self.motor,
            "combustible": self.combustible,
            "consumo": self.consumo,
        }

    # método adaptado a los nuevos atributos
    def obtener_consumo(self):
        """Consumo combinado en L/100 km."""
        return self.consumo

    def mostrar_informacion(self):
        """Devuelve la ficha del vehículo como texto (en Streamlit se muestra con st.write)."""
        return (
            f"Marca: {self.marca}\n"
            f"Modelo: {self.modelo}\n"
            f"Tipo de vehículo: {self.tipo}\n"
            f"Motor: {self.motor} L\n"
            f"Combustible: {self.combustible}\n"
            f"Consumo combinado: {self.consumo} L/100 km"
        )
