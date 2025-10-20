# 🏆 Tests Manuales - Gestión Avanzada de Torneos

## 📋 **Resumen de Endpoints Implementados**

### **Nuevos Endpoints de Gestión de Torneos:**

1. **POST** `/tournaments/{tournament_id}/join` - Unirse a un torneo
2. **DELETE** `/tournaments/{tournament_id}/leave` - Abandonar un torneo  
3. **DELETE** `/tournaments/{tournament_id}` - Eliminar un torneo (solo creador)
4. **DELETE** `/tournaments/{tournament_id}/participants/{user_id}` - Remover participante (solo creador)
5. **GET** `/tournaments/{tournament_id}/participants` - Listar participantes
6. **POST** `/tournaments/{tournament_id}/invite` - Invitar usuario (solo creador)
7. **PATCH** `/tournaments/{tournament_id}/visibility` - Cambiar visibilidad (solo creador)

---

## 🔐 **Autenticación**

### **Obtener Token de Acceso:**
```bash
# Usuario testuser (ID: 3)
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "testpass123"}'

# Respuesta esperada:
# {
#   "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
#   "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
#   "token_type": "bearer"
# }
```

---

## 🧪 **Tests de Endpoints**

### **1. POST /tournaments/{tournament_id}/join**

#### **✅ Caso Exitoso - Unirse a Torneo Público:**
```bash
curl -X POST "http://localhost:8000/tournaments/11/join" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json"

# Respuesta esperada:
# {
#   "message": "Joined tournament successfully",
#   "tournament_id": 11,
#   "user_id": 3
# }
```

#### **❌ Caso de Error - Ya es Participante:**
```bash
curl -X POST "http://localhost:8000/tournaments/11/join" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json"

# Respuesta esperada:
# {
#   "detail": "You are already a participant in this tournament"
# }
```

#### **❌ Caso de Error - Torneo No Existe:**
```bash
curl -X POST "http://localhost:8000/tournaments/999/join" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json"

# Respuesta esperada:
# {
#   "detail": "Tournament with id 999 not found"
# }
```

#### **❌ Caso de Error - Sin Autenticación:**
```bash
curl -X POST "http://localhost:8000/tournaments/11/join" \
  -H "Content-Type: application/json"

# Respuesta esperada:
# {
#   "detail": "Not authenticated"
# }
```

---

### **2. DELETE /tournaments/{tournament_id}/leave**

#### **✅ Caso Exitoso - Abandonar Torneo:**
```bash
curl -X DELETE "http://localhost:8000/tournaments/11/leave" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json"

# Respuesta esperada:
# {
#   "message": "Left tournament successfully",
#   "tournament_id": 11
# }
```

#### **❌ Caso de Error - No es Participante:**
```bash
curl -X DELETE "http://localhost:8000/tournaments/11/leave" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json"

# Respuesta esperada:
# {
#   "detail": "You are not a participant in this tournament"
# }
```

#### **❌ Caso de Error - Es el Creador:**
```bash
# Si el usuario es el creador del torneo
curl -X DELETE "http://localhost:8000/tournaments/11/leave" \
  -H "Authorization: Bearer CREATOR_TOKEN" \
  -H "Content-Type: application/json"

# Respuesta esperada:
# {
#   "detail": "Tournament creators cannot leave their own tournament. Delete the tournament instead."
# }
```

---

### **3. DELETE /tournaments/{tournament_id}**

#### **✅ Caso Exitoso - Eliminar Torneo (Creador):**
```bash
# Primero crear un torneo para eliminar
curl -X POST "http://localhost:8000/tournaments" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Torneo para Eliminar",
    "description": "Este torneo será eliminado",
    "league_id": 39,
    "is_public": true,
    "max_participants": 10
  }'

# Luego eliminarlo
curl -X DELETE "http://localhost:8000/tournaments/12" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json"

# Respuesta esperada:
# {
#   "message": "Tournament deleted successfully",
#   "id": 12
# }
```

#### **❌ Caso de Error - No es el Creador:**
```bash
curl -X DELETE "http://localhost:8000/tournaments/11" \
  -H "Authorization: Bearer NON_CREATOR_TOKEN" \
  -H "Content-Type: application/json"

# Respuesta esperada:
# {
#   "detail": "Only the tournament creator can delete the tournament"
# }
```

---

### **4. GET /tournaments/{tournament_id}/participants**

#### **✅ Caso Exitoso - Listar Participantes:**
```bash
curl -X GET "http://localhost:8000/tournaments/11/participants" \
  -H "accept: application/json"

# Respuesta esperada:
# [
#   {
#     "id": 3,
#     "username": "testuser",
#     "joined_at": "2025-10-20T23:14:23.723304"
#   }
# ]
```

#### **❌ Caso de Error - Torneo No Existe:**
```bash
curl -X GET "http://localhost:8000/tournaments/999/participants" \
  -H "accept: application/json"

# Respuesta esperada:
# {
#   "detail": "Tournament with id 999 not found"
# }
```

---

### **5. DELETE /tournaments/{tournament_id}/participants/{user_id}**

#### **✅ Caso Exitoso - Remover Participante (Creador):**
```bash
curl -X DELETE "http://localhost:8000/tournaments/11/participants/3" \
  -H "Authorization: Bearer CREATOR_TOKEN" \
  -H "Content-Type: application/json"

# Respuesta esperada:
# {
#   "message": "User removed from tournament",
#   "tournament_id": 11,
#   "user_id": 3
# }
```

#### **❌ Caso de Error - No es el Creador:**
```bash
curl -X DELETE "http://localhost:8000/tournaments/11/participants/3" \
  -H "Authorization: Bearer NON_CREATOR_TOKEN" \
  -H "Content-Type: application/json"

# Respuesta esperada:
# {
#   "detail": "Only the tournament creator can remove participants"
# }
```

#### **❌ Caso de Error - Usuario No es Participante:**
```bash
curl -X DELETE "http://localhost:8000/tournaments/11/participants/999" \
  -H "Authorization: Bearer CREATOR_TOKEN" \
  -H "Content-Type: application/json"

# Respuesta esperada:
# {
#   "detail": "User is not a participant in this tournament"
# }
```

---

### **6. POST /tournaments/{tournament_id}/invite**

#### **✅ Caso Exitoso - Invitar Usuario (Creador):**
```bash
curl -X POST "http://localhost:8000/tournaments/11/invite" \
  -H "Authorization: Bearer CREATOR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"user_id": 3}'

# Respuesta esperada:
# {
#   "message": "User invited to tournament successfully",
#   "tournament_id": 11,
#   "invited_user_id": 3
# }
```

#### **❌ Caso de Error - No es el Creador:**
```bash
curl -X POST "http://localhost:8000/tournaments/11/invite" \
  -H "Authorization: Bearer NON_CREATOR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"user_id": 3}'

# Respuesta esperada:
# {
#   "detail": "Only the tournament creator can invite users"
# }
```

#### **❌ Caso de Error - Usuario Ya es Participante:**
```bash
curl -X POST "http://localhost:8000/tournaments/11/invite" \
  -H "Authorization: Bearer CREATOR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"user_id": 3}'

# Respuesta esperada:
# {
#   "detail": "User is already a participant in this tournament"
# }
```

---

### **7. PATCH /tournaments/{tournament_id}/visibility**

#### **✅ Caso Exitoso - Cambiar Visibilidad (Creador):**
```bash
# Cambiar a privado
curl -X PATCH "http://localhost:8000/tournaments/11/visibility" \
  -H "Authorization: Bearer CREATOR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"is_public": false}'

# Respuesta esperada:
# {
#   "message": "Tournament visibility changed to private",
#   "tournament_id": 11,
#   "is_public": false
# }

# Cambiar a público
curl -X PATCH "http://localhost:8000/tournaments/11/visibility" \
  -H "Authorization: Bearer CREATOR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"is_public": true}'

# Respuesta esperada:
# {
#   "message": "Tournament visibility changed to public",
#   "tournament_id": 11,
#   "is_public": true
# }
```

#### **❌ Caso de Error - No es el Creador:**
```bash
curl -X PATCH "http://localhost:8000/tournaments/11/visibility" \
  -H "Authorization: Bearer NON_CREATOR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"is_public": false}'

# Respuesta esperada:
# {
#   "detail": "Only the tournament creator can change visibility"
# }
```

---

## 🔄 **Flujo de Prueba Completo**

### **Escenario: Gestión Completa de Torneo**

1. **Crear Torneo:**
```bash
curl -X POST "http://localhost:8000/tournaments" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Torneo de Prueba Completo",
    "description": "Prueba de todos los endpoints",
    "league_id": 39,
    "is_public": true,
    "max_participants": 50
  }'
```

2. **Unirse al Torneo:**
```bash
curl -X POST "http://localhost:8000/tournaments/TOURNAMENT_ID/join" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json"
```

3. **Ver Participantes:**
```bash
curl -X GET "http://localhost:8000/tournaments/TOURNAMENT_ID/participants" \
  -H "accept: application/json"
```

4. **Cambiar Visibilidad:**
```bash
curl -X PATCH "http://localhost:8000/tournaments/TOURNAMENT_ID/visibility" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"is_public": false}'
```

5. **Invitar Usuario:**
```bash
curl -X POST "http://localhost:8000/tournaments/TOURNAMENT_ID/invite" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"user_id": 4}'
```

6. **Remover Participante:**
```bash
curl -X DELETE "http://localhost:8000/tournaments/TOURNAMENT_ID/participants/4" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json"
```

7. **Eliminar Torneo:**
```bash
curl -X DELETE "http://localhost:8000/tournaments/TOURNAMENT_ID" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json"
```

---

## 📊 **Códigos de Estado HTTP**

| Código | Significado | Cuándo Ocurre |
|--------|-------------|---------------|
| 200 | OK | Operación exitosa |
| 400 | Bad Request | Datos inválidos, ya es participante, etc. |
| 401 | Unauthorized | Token inválido o faltante |
| 403 | Forbidden | Sin permisos (no es creador) |
| 404 | Not Found | Torneo o usuario no encontrado |
| 422 | Unprocessable Entity | Error de validación de datos |
| 500 | Internal Server Error | Error interno del servidor |

---

## 🛡️ **Reglas de Acceso**

### **Usuarios Regulares:**
- ✅ Pueden unirse a torneos públicos
- ✅ Pueden abandonar torneos (excepto si son creadores)
- ✅ Pueden ver participantes de torneos
- ❌ No pueden eliminar torneos
- ❌ No pueden remover participantes
- ❌ No pueden invitar usuarios
- ❌ No pueden cambiar visibilidad

### **Creadores de Torneo:**
- ✅ Todas las capacidades de usuarios regulares
- ✅ Pueden eliminar sus propios torneos
- ✅ Pueden remover participantes de sus torneos
- ✅ Pueden invitar usuarios a sus torneos
- ✅ Pueden cambiar la visibilidad de sus torneos
- ❌ No pueden abandonar sus propios torneos (deben eliminarlos)

---

## 🔧 **Notas Técnicas**

### **Base de Datos:**
- Se creó la tabla `tournament_participants` con constraint único
- Relaciones cascade para eliminación automática
- Índices para optimizar consultas

### **Validaciones:**
- Verificación de existencia de torneo
- Verificación de permisos de usuario
- Prevención de duplicados
- Validación de datos de entrada

### **Logging:**
- Logs detallados para todas las operaciones
- Seguimiento de errores y excepciones
- Información de auditoría

---

## ✅ **Estado de Implementación**

- [x] Modelo `TournamentParticipant`
- [x] Servicios de participación
- [x] Endpoints de gestión
- [x] Validaciones de permisos
- [x] Manejo de errores
- [x] Tests manuales
- [x] Documentación completa

**¡Todos los endpoints están implementados y funcionando correctamente!** 🎉
