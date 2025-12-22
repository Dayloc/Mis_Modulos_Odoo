cuadrados = [x**2 for x in range(5)]
print(cuadrados)

pares = [x for x in range(10) if x % 2 == 0]
print(pares)

impares = [x for x in range(100) if x%2 !=0]
print(impares)


etiquetas = ["par" if x % 2 == 0 else "impar" for x in range(5)]
# Resultado: ['par', 'impar', 'par', 'impar', 'par']
print (etiquetas)

