import hashlib

# Cambia "123" por la contraseña real que quieras encriptar
contrasena_plana = "123"

# Generamos el hash SHA-256
hash_seguro = hashlib.sha256(contrasena_plana.encode()).hexdigest()

print("Copia este código largo y pégalo en el campo 'pwd' de tu Firebase:")
print("-" * 50)
print(hash_seguro)
print("-" * 50)