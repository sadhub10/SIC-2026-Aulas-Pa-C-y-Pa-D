import pandas as pd

# datos iniciales de las aves mas conocidas de panama
datos = {
    "Nombre": ["Tucán", "Guacamaya roja", "Colibrí", "Águila harpía", "Talingo"],
    "Nombre científico": ["Ramphastos sulfuratus", "Ara macao",
                          "Amazilia tzacatl", "Harpia harpyja",
                          "Quiscalus mexicanus"],
    "Hábitat": ["Bosque tropical", "Bosque tropical", "Jardines y bosques",
                "Selva tropical", "Zonas urbanas"],
    "Alimentación": ["Frutas", "Frutas y semillas", "Néctar",
                     "Pequeños animales", "Omnívora"],
    "Población": [15000, 12000, 25000, 5000, 40000]
}
#los valores de poblacion son inventados
aves = pd.DataFrame(datos)

#lista donde se guardan los avistamientos del usuario
avistamientos = []

while True:
    print("\n========== AVEPEDIA ==========")
    print("1. Mostrar aves")
    print("2. Buscar un ave")
    print("3. Registrar avistamiento")
    print("4. Ver mis avistamientos")
    print("5. Salir")
    print("==============================")
    opcion = input("Seleccione una opción: ")

    if opcion == "1":
        # mostramos el catalogo de aves
        print("\nCATÁLOGO DE AVES")
        print(aves.to_string(index=False))

    elif opcion == "2":
        # filtramos las aves según el nombre ingresado
        nombre = input("Ingrese el nombre del ave: ")

        resultado=aves[aves["Nombre"].str.contains(nombre, case=False)]

        if not resultado.empty:
            print("\nAve encontrada:")
            print(resultado.to_string(index=False))
        else:
            print("No se encontró el ave.")

    elif opcion == "3":
        #solicitar los datos del avistamiento
        print("\nREGISTRAR AVISTAMIENTO")

        nombre = input("Nombre del ave: ")
        fecha = input("Fecha del avistamiento: ")
        ubicacion = input("Ubicación: ")

        #organizar los datos en un diccionario
        registro = {
            "Nombre": nombre,
            "Fecha": fecha,
            "Ubicación": ubicacion
        }

        # agregamos el registro a la lista
        avistamientos.append(registro)

        print("\n¡Avistamiento registrado!")
        print("Ave:", nombre)
        print("Fecha:", fecha)
        print("Ubicación:", ubicacion)

    elif opcion == "4":
        # mostramos los avistamientos realizados
        if len(avistamientos) == 0:
            print("\nTodavía no tienes avistamientos.")
        else:
            print("\nMIS AVISTAMIENTOS")

            for registro in avistamientos:
                print("------------------------")
                print("Ave:", registro["Nombre"])
                print("Fecha:", registro["Fecha"])
                print("Ubicación:", registro["Ubicación"])

    elif opcion == "5":
        print("\nGracias por utilizar AvePedia.")
        break

    else:
        print("\nOpción inválida. Intente nuevamente.")
