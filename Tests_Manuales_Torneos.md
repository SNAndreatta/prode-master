# 🧪 Tests Manuales - Endpoints de Torneos

Este archivo contiene todos los casos de uso para probar los endpoints de torneos usando `curl`. Los tests están organizados por endpoint y incluyen casos exitosos y de error.

## 📋 Prerequisitos

1. **Servidor ejecutándose**: `python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload`
2. **Usuario registrado** (para endpoints que requieren autenticación)
3. **Token JWT válido** (obtenido del login)

---

## 🔐 1. Autenticación

### 1.1 Registrar Usuario
```bash
curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "username": "testuser",
    "password": "testpass123"
  }'
```

**Respuesta esperada**: `{"id": 1, "username": "testuser", "email": "test@example.com"}`

### 1.2 Login (Obtener Token)
```bash
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "testpass123"
  }'
```

**Respuesta esperada**: 
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**⚠️ IMPORTANTE**: Copia el `access_token` de la respuesta para usar en los siguientes tests.

---

## 🏆 2. Endpoints de Torneos

### 2.1 GET /tournaments - Obtener Torneos Públicos

#### 2.1.1 Obtener todos los torneos públicos
```bash
curl -X GET "http://localhost:8000/tournaments" \
  -H "accept: application/json"
```

**Respuesta esperada**: Lista de torneos públicos
```json
[
  {
    "id": 1,
    "name": "Mi Torneo",
    "description": "Descripción del torneo",
    "is_public": true,
    "creator_id": 1,
    "league_id": 39,
    "max_participants": 50,
    "created_at": "2025-10-20T22:00:00.000000",
    "updated_at": "2025-10-20T22:00:00.000000"
  }
]
```

#### 2.1.2 Filtrar torneos por liga
```bash
curl -X GET "http://localhost:8000/tournaments?league_id=39" \
  -H "accept: application/json"
```

**Respuesta esperada**: Solo torneos de la liga 39 (Premier League)

#### 2.1.3 Filtrar torneos por liga inexistente
```bash
curl -X GET "http://localhost:8000/tournaments?league_id=999" \
  -H "accept: application/json"
```

**Respuesta esperada**: Lista vacía `[]`

---

### 2.2 POST /tournaments - Crear Torneo

#### 2.2.1 Crear torneo público básico
```bash
curl -X POST "http://localhost:8000/tournaments" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer TU_TOKEN_AQUI" \
  -d '{
    "name": "Mi Primer Torneo",
    "description": "Un torneo de prueba para la Premier League",
    "league_id": 39,
    "is_public": true,
    "max_participants": 50
  }'
```

**Respuesta esperada**: Torneo creado
```json
{
  "id": 1,
  "name": "Mi Primer Torneo",
  "description": "Un torneo de prueba para la Premier League",
  "is_public": true,
  "creator_id": 1,
  "league_id": 39,
  "max_participants": 50,
  "created_at": "2025-10-20T22:00:00.000000",
  "updated_at": "2025-10-20T22:00:00.000000"
}
```

#### 2.2.2 Crear torneo privado
```bash
curl -X POST "http://localhost:8000/tournaments" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer TU_TOKEN_AQUI" \
  -d '{
    "name": "Torneo Privado",
    "description": "Solo para amigos",
    "league_id": 39,
    "is_public": false,
    "max_participants": 10
  }'
```

#### 2.2.3 Crear torneo sin descripción
```bash
curl -X POST "http://localhost:8000/tournaments" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer TU_TOKEN_AQUI" \
  -d '{
    "name": "Torneo Sin Descripción",
    "league_id": 39,
    "is_public": true,
    "max_participants": 100
  }'
```

#### 2.2.4 Crear torneo con valores por defecto
```bash
curl -X POST "http://localhost:8000/tournaments" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer TU_TOKEN_AQUI" \
  -d '{
    "name": "Torneo con Defaults",
    "league_id": 39
  }'
```

**Respuesta esperada**: Torneo con `is_public: true` y `max_participants: 100` por defecto

---

### 2.3 Casos de Error - POST /tournaments

#### 2.3.1 Sin autenticación
```bash
curl -X POST "http://localhost:8000/tournaments" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Torneo Sin Auth",
    "league_id": 39
  }'
```

**Respuesta esperada**: `401 Unauthorized`

#### 2.3.2 Token inválido
```bash
curl -X POST "http://localhost:8000/tournaments" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer token_invalido" \
  -d '{
    "name": "Torneo Token Inválido",
    "league_id": 39
  }'
```

**Respuesta esperada**: `401 Unauthorized`

#### 2.3.3 Liga inexistente
```bash
curl -X POST "http://localhost:8000/tournaments" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer TU_TOKEN_AQUI" \
  -d '{
    "name": "Torneo Liga Inexistente",
    "league_id": 999
  }'
```

**Respuesta esperada**: `404 Not Found` - "League with id 999 not found"

#### 2.3.4 Datos inválidos - Nombre vacío
```bash
curl -X POST "http://localhost:8000/tournaments" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer TU_TOKEN_AQUI" \
  -d '{
    "name": "",
    "league_id": 39
  }'
```

**Respuesta esperada**: `422 Unprocessable Entity` - Error de validación

#### 2.3.5 Datos inválidos - Max participants inválido
```bash
curl -X POST "http://localhost:8000/tournaments" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer TU_TOKEN_AQUI" \
  -d '{
    "name": "Torneo Max Inválido",
    "league_id": 39,
    "max_participants": 1
  }'
```

**Respuesta esperada**: `422 Unprocessable Entity` - Error de validación (mínimo 2)

---

### 2.4 GET /tournaments/my - Mis Torneos

#### 2.4.1 Obtener mis torneos
```bash
curl -X GET "http://localhost:8000/tournaments/my" \
  -H "Authorization: Bearer TU_TOKEN_AQUI"
```

**Respuesta esperada**: Lista de torneos creados por el usuario autenticado

#### 2.4.2 Sin autenticación
```bash
curl -X GET "http://localhost:8000/tournaments/my"
```

**Respuesta esperada**: `401 Unauthorized`

#### 2.4.3 Token inválido
```bash
curl -X GET "http://localhost:8000/tournaments/my" \
  -H "Authorization: Bearer token_invalido"
```

**Respuesta esperada**: `401 Unauthorized`

---

### 2.5 GET /tournaments/{tournament_id} - Obtener Torneo por ID

#### 2.5.1 Obtener torneo existente
```bash
curl -X GET "http://localhost:8000/tournaments/1" \
  -H "accept: application/json"
```

**Respuesta esperada**: Detalles del torneo
```json
{
  "id": 1,
  "name": "Mi Primer Torneo",
  "description": "Un torneo de prueba para la Premier League",
  "is_public": true,
  "creator_id": 1,
  "league_id": 39,
  "max_participants": 50,
  "created_at": "2025-10-20T22:00:00.000000",
  "updated_at": "2025-10-20T22:00:00.000000"
}
```

#### 2.5.2 Torneo inexistente
```bash
curl -X GET "http://localhost:8000/tournaments/999" \
  -H "accept: application/json"
```

**Respuesta esperada**: `404 Not Found` - "Tournament with id 999 not found"

#### 2.5.3 ID inválido
```bash
curl -X GET "http://localhost:8000/tournaments/abc" \
  -H "accept: application/json"
```

**Respuesta esperada**: `422 Unprocessable Entity` - Error de validación

---

## 🔍 3. Tests de Integración

### 3.1 Flujo Completo - Crear y Listar Torneos

#### Paso 1: Registrar usuario
```bash
curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "usuario@test.com",
    "username": "usuario",
    "password": "password123"
  }'
```

#### Paso 2: Hacer login
```bash
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "usuario@test.com",
    "password": "password123"
  }'
```

#### Paso 3: Crear torneo
```bash
curl -X POST "http://localhost:8000/tournaments" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer TU_TOKEN_AQUI" \
  -d '{
    "name": "Torneo de Integración",
    "description": "Test de flujo completo",
    "league_id": 39,
    "is_public": true,
    "max_participants": 25
  }'
```

#### Paso 4: Verificar en lista pública
```bash
curl -X GET "http://localhost:8000/tournaments"
```

#### Paso 5: Verificar en mis torneos
```bash
curl -X GET "http://localhost:8000/tournaments/my" \
  -H "Authorization: Bearer TU_TOKEN_AQUI"
```

#### Paso 6: Obtener torneo específico
```bash
curl -X GET "http://localhost:8000/tournaments/1"
```

---

## 📊 4. Tests de Rendimiento

### 4.1 Crear múltiples torneos
```bash
# Crear 5 torneos diferentes
for i in {1..5}; do
  curl -X POST "http://localhost:8000/tournaments" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer TU_TOKEN_AQUI" \
    -d "{
      \"name\": \"Torneo $i\",
      \"description\": \"Torneo número $i\",
      \"league_id\": 39,
      \"is_public\": true,
      \"max_participants\": 50
    }"
  echo "Torneo $i creado"
done
```

### 4.2 Listar torneos con filtro
```bash
# Probar diferentes filtros
curl -X GET "http://localhost:8000/tournaments?league_id=39"
curl -X GET "http://localhost:8000/tournaments?league_id=40"
curl -X GET "http://localhost:8000/tournaments"
```

---

## 🚨 5. Casos Edge

### 5.1 Nombres de torneo muy largos
```bash
curl -X POST "http://localhost:8000/tournaments" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer TU_TOKEN_AQUI" \
  -d '{
    "name": "Este es un nombre de torneo extremadamente largo que debería fallar la validación porque excede el límite de 100 caracteres permitidos",
    "league_id": 39
  }'
```

### 5.2 Descripción muy larga
```bash
curl -X POST "http://localhost:8000/tournaments" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer TU_TOKEN_AQUI" \
  -d '{
    "name": "Torneo Descripción Larga",
    "description": "Esta es una descripción extremadamente larga que debería fallar la validación porque excede el límite de 500 caracteres permitidos. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum. Sed ut perspiciatis unde omnis iste natus error sit voluptatem accusantium doloremque laudantium.",
    "league_id": 39
  }'
```

### 5.3 Max participants extremo
```bash
curl -X POST "http://localhost:8000/tournaments" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer TU_TOKEN_AQUI" \
  -d '{
    "name": "Torneo Max Extremo",
    "league_id": 39,
    "max_participants": 1001
  }'
```

---

## 📝 6. Notas Importantes

### 6.1 Variables de Entorno
- **URL Base**: `http://localhost:8000`
- **Puerto**: `8000` (ajustar si es diferente)
- **Token**: Reemplazar `TU_TOKEN_AQUI` con el token real obtenido del login

### 6.2 Códigos de Respuesta Esperados
- **200**: Éxito
- **201**: Creado exitosamente
- **400**: Bad Request (datos inválidos)
- **401**: Unauthorized (sin token o token inválido)
- **404**: Not Found (recurso no encontrado)
- **422**: Unprocessable Entity (error de validación)
- **500**: Internal Server Error (error del servidor)

### 6.3 Headers Importantes
- **Content-Type**: `application/json` (para POST)
- **Authorization**: `Bearer <token>` (para endpoints protegidos)
- **Accept**: `application/json` (opcional, para GET)

### 6.4 Validaciones Implementadas
- **Nombre**: 1-100 caracteres
- **Descripción**: Máximo 500 caracteres (opcional)
- **Max Participants**: 2-1000
- **League ID**: Debe existir en la base de datos
- **Token**: Debe ser válido y no expirado

---

## 🎯 7. Checklist de Tests

- [ ] ✅ Registrar usuario
- [ ] ✅ Hacer login y obtener token
- [ ] ✅ Crear torneo público
- [ ] ✅ Crear torneo privado
- [ ] ✅ Crear torneo con valores por defecto
- [ ] ✅ Listar torneos públicos
- [ ] ✅ Filtrar torneos por liga
- [ ] ✅ Obtener mis torneos
- [ ] ✅ Obtener torneo por ID
- [ ] ✅ Manejar errores de autenticación
- [ ] ✅ Manejar errores de validación
- [ ] ✅ Manejar liga inexistente
- [ ] ✅ Manejar torneo inexistente

---

**💡 Tip**: Guarda este archivo y úsalo como referencia rápida para probar todos los endpoints sin necesidad de escribir las URLs en el navegador.

---

## ✅ **Problema Resuelto: Error de Validación de DateTime**

**Problema**: Los endpoints devolvían error 500 con `ResponseValidationError` porque los campos `created_at` y `updated_at` eran objetos `datetime` pero el modelo Pydantic esperaba strings.

**Solución**: Se cambió el modelo `TournamentResponse` para aceptar objetos `datetime` directamente:
```python
class TournamentResponse(BaseModel):
    # ... otros campos ...
    created_at: datetime  # Cambiado de str a datetime
    updated_at: datetime  # Cambiado de str a datetime
```

**Resultado**: Los endpoints ahora funcionan correctamente y devuelven las fechas en formato ISO 8601 como strings en la respuesta JSON.
