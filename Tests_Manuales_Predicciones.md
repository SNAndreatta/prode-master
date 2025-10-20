# 🎯 Tests Manuales - Sistema de Predicciones

## 📋 **Resumen del Sistema**

El Sistema de Predicciones permite a los usuarios predecir resultados de partidos de fútbol. Las predicciones son **globales por usuario** - una sola predicción cuenta para todos los torneos en los que participa.

### **Características Principales:**
- ✅ Una predicción por usuario por partido
- ✅ Predicciones globales (aplican a todos los torneos)
- ✅ Bloqueo temporal (no se puede predecir después del inicio)
- ✅ Soporte para goles y penales
- ✅ Privacidad (solo predicciones de torneos compartidos)

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

### **1. POST /predictions - Crear/Actualizar Predicción**

#### **✅ Caso Exitoso - Crear Nueva Predicción:**
```bash
curl -X POST "http://localhost:8000/predictions" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "match_id": 1,
    "goals_home": 2,
    "goals_away": 1,
    "penalties_home": 4,
    "penalties_away": 3
  }'

# Respuesta esperada:
# {
#   "id": 1,
#   "user_id": 3,
#   "match_id": 1,
#   "goals_home": 2,
#   "goals_away": 1,
#   "penalties_home": 4,
#   "penalties_away": 3,
#   "created_at": "2025-10-20T23:30:00.000Z",
#   "updated_at": "2025-10-20T23:30:00.000Z"
# }
```

#### **✅ Caso Exitoso - Actualizar Predicción Existente:**
```bash
curl -X POST "http://localhost:8000/predictions" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "match_id": 1,
    "goals_home": 3,
    "goals_away": 0,
    "penalties_home": null,
    "penalties_away": null
  }'

# Respuesta esperada:
# {
#   "id": 1,
#   "user_id": 3,
#   "match_id": 1,
#   "goals_home": 3,
#   "goals_away": 0,
#   "penalties_home": null,
#   "penalties_away": null,
#   "created_at": "2025-10-20T23:30:00.000Z",
#   "updated_at": "2025-10-20T23:35:00.000Z"
# }
```

#### **❌ Caso de Error - Partido No Existe:**
```bash
curl -X POST "http://localhost:8000/predictions" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "match_id": 999,
    "goals_home": 2,
    "goals_away": 1
  }'

# Respuesta esperada:
# {
#   "detail": "Match with id 999 not found"
# }
```

#### **❌ Caso de Error - Partido Ya Iniciado:**
```bash
curl -X POST "http://localhost:8000/predictions" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "match_id": 2,
    "goals_home": 2,
    "goals_away": 1
  }'

# Respuesta esperada:
# {
#   "detail": "Cannot create prediction for a match that has started or finished"
# }
```

#### **❌ Caso de Error - Goles Negativos:**
```bash
curl -X POST "http://localhost:8000/predictions" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "match_id": 1,
    "goals_home": -1,
    "goals_away": 2
  }'

# Respuesta esperada:
# {
#   "detail": [
#     {
#       "type": "value_error",
#       "loc": ["body", "goals_home"],
#       "msg": "ensure this value is greater than or equal to 0",
#       "input": -1
#     }
#   ]
# }
```

#### **❌ Caso de Error - Sin Autenticación:**
```bash
curl -X POST "http://localhost:8000/predictions" \
  -H "Content-Type: application/json" \
  -d '{
    "match_id": 1,
    "goals_home": 2,
    "goals_away": 1
  }'

# Respuesta esperada:
# {
#   "detail": "Not authenticated"
# }
```

---

### **2. GET /predictions - Obtener Predicciones del Usuario**

#### **✅ Caso Exitoso - Todas las Predicciones:**
```bash
curl -X GET "http://localhost:8000/predictions" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "accept: application/json"

# Respuesta esperada:
# [
#   {
#     "id": 1,
#     "user_id": 3,
#     "match_id": 1,
#     "goals_home": 3,
#     "goals_away": 0,
#     "penalties_home": null,
#     "penalties_away": null,
#     "created_at": "2025-10-20T23:30:00.000Z",
#     "updated_at": "2025-10-20T23:35:00.000Z",
#     "match": {
#       "id": 1,
#       "round_id": 1,
#       "home_team_id": 1,
#       "away_team_id": 2,
#       "start_time": "2025-10-21T20:00:00.000Z",
#       "finished": false,
#       "result_goals_home": null,
#       "result_goals_away": null,
#       "result_penalties_home": null,
#       "result_penalties_away": null
#     }
#   }
# ]
```

#### **✅ Caso Exitoso - Filtrar por Ronda:**
```bash
curl -X GET "http://localhost:8000/predictions?round_id=1" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "accept: application/json"
```

#### **✅ Caso Exitoso - Filtrar por Liga:**
```bash
curl -X GET "http://localhost:8000/predictions?league_id=39" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "accept: application/json"
```

#### **✅ Caso Exitoso - Filtrar por Partido:**
```bash
curl -X GET "http://localhost:8000/predictions?match_id=1" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "accept: application/json"
```

---

### **3. DELETE /predictions/{match_id} - Eliminar Predicción**

#### **✅ Caso Exitoso - Eliminar Predicción:**
```bash
curl -X DELETE "http://localhost:8000/predictions/1" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json"

# Respuesta esperada:
# {
#   "message": "Prediction deleted successfully",
#   "match_id": 1
# }
```

#### **❌ Caso de Error - Predicción No Existe:**
```bash
curl -X DELETE "http://localhost:8000/predictions/999" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json"

# Respuesta esperada:
# {
#   "detail": "Prediction not found"
# }
```

#### **❌ Caso de Error - Partido Ya Iniciado:**
```bash
curl -X DELETE "http://localhost:8000/predictions/2" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json"

# Respuesta esperada:
# {
#   "detail": "Cannot delete prediction for a match that has started or finished"
# }
```

---

### **4. GET /predictions/stats - Estadísticas del Usuario**

#### **✅ Caso Exitoso - Obtener Estadísticas:**
```bash
curl -X GET "http://localhost:8000/predictions/stats" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "accept: application/json"

# Respuesta esperada:
# {
#   "total_predictions": 5,
#   "correct_predictions": 3,
#   "accuracy_percentage": 60.0,
#   "average_goals_predicted": 2.4,
#   "most_common_outcome": "win"
# }
```

---

### **5. GET /predictions/match/{match_id} - Predicciones de un Partido**

#### **✅ Caso Exitoso - Ver Predicciones de Partido:**
```bash
curl -X GET "http://localhost:8000/predictions/match/1" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "accept: application/json"

# Respuesta esperada:
# [
#   {
#     "id": 1,
#     "user_id": 3,
#     "match_id": 1,
#     "goals_home": 3,
#     "goals_away": 0,
#     "penalties_home": null,
#     "penalties_away": null,
#     "created_at": "2025-10-20T23:30:00.000Z",
#     "updated_at": "2025-10-20T23:35:00.000Z"
#   }
# ]
```

---

## 🔧 **Endpoints de Administración**

### **6. GET /admin/predictions/match/{match_id} - Ver Todas las Predicciones (Admin)**

#### **✅ Caso Exitoso - Admin Ve Todas las Predicciones:**
```bash
curl -X GET "http://localhost:8000/admin/predictions/match/1" \
  -H "Authorization: Bearer ADMIN_TOKEN" \
  -H "accept: application/json"

# Respuesta esperada:
# [
#   {
#     "id": 1,
#     "user_id": 3,
#     "username": "testuser",
#     "match_id": 1,
#     "goals_home": 3,
#     "goals_away": 0,
#     "penalties_home": null,
#     "penalties_away": null,
#     "created_at": "2025-10-20T23:30:00.000Z",
#     "updated_at": "2025-10-20T23:35:00.000Z",
#     "match": {
#       "id": 1,
#       "round_id": 1,
#       "home_team_id": 1,
#       "away_team_id": 2,
#       "start_time": "2025-10-21T20:00:00.000Z",
#       "finished": false,
#       "result_goals_home": null,
#       "result_goals_away": null,
#       "result_penalties_home": null,
#       "result_penalties_away": null
#     }
#   }
# ]
```

### **7. POST /admin/predictions/score - Calcular Puntuaciones (Admin)**

#### **✅ Caso Exitoso - Calcular Puntuaciones:**
```bash
curl -X POST "http://localhost:8000/admin/predictions/score" \
  -H "Authorization: Bearer ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "match_id": 1,
    "exact_score_points": 10,
    "correct_winner_points": 5,
    "penalty_bonus_points": 3
  }'

# Respuesta esperada:
# {
#   "match_id": 1,
#   "total_predictions": 5,
#   "scores_calculated": 5,
#   "exact_scores": 2,
#   "correct_winners": 3,
#   "penalty_bonuses": 1
# }
```

---

## 🔄 **Flujo de Prueba Completo**

### **Escenario: Predicción Completa de un Partido**

1. **Crear Predicción:**
```bash
curl -X POST "http://localhost:8000/predictions" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "match_id": 1,
    "goals_home": 2,
    "goals_away": 1,
    "penalties_home": 4,
    "penalties_away": 3
  }'
```

2. **Ver Predicción Creada:**
```bash
curl -X GET "http://localhost:8000/predictions?match_id=1" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "accept: application/json"
```

3. **Actualizar Predicción:**
```bash
curl -X POST "http://localhost:8000/predictions" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "match_id": 1,
    "goals_home": 3,
    "goals_away": 0,
    "penalties_home": null,
    "penalties_away": null
  }'
```

4. **Ver Estadísticas:**
```bash
curl -X GET "http://localhost:8000/predictions/stats" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "accept: application/json"
```

5. **Eliminar Predicción (antes del partido):**
```bash
curl -X DELETE "http://localhost:8000/predictions/1" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json"
```

---

## 📊 **Códigos de Estado HTTP**

| Código | Significado | Cuándo Ocurre |
|--------|-------------|---------------|
| 200 | OK | Operación exitosa |
| 201 | Created | Predicción creada exitosamente |
| 400 | Bad Request | Datos inválidos, partido bloqueado |
| 401 | Unauthorized | Token inválido o faltante |
| 403 | Forbidden | Sin permisos de administrador |
| 404 | Not Found | Predicción o partido no encontrado |
| 422 | Unprocessable Entity | Error de validación de datos |
| 500 | Internal Server Error | Error interno del servidor |

---

## 🛡️ **Reglas de Negocio**

### **Validaciones de Predicción:**
- ✅ Solo una predicción por usuario por partido
- ✅ No se puede predecir después del inicio del partido
- ✅ Los goles deben ser números enteros no negativos
- ✅ Los penales son opcionales
- ✅ Se puede actualizar antes del inicio del partido

### **Privacidad:**
- ✅ Los usuarios solo ven sus propias predicciones
- ✅ Solo se ven predicciones de otros usuarios en torneos compartidos
- ✅ Los administradores pueden ver todas las predicciones

### **Puntuación:**
- ✅ Puntos por resultado exacto
- ✅ Puntos por ganador correcto
- ✅ Bonificación por penales correctos
- ✅ Solo se calcula para partidos terminados

---

## 🔧 **Notas Técnicas**

### **Base de Datos:**
- Constraint único en `(user_id, match_id)`
- Relaciones cascade para eliminación automática
- Índices para optimizar consultas
- Validaciones a nivel de base de datos

### **Validaciones:**
- Verificación de existencia de partido
- Verificación de bloqueo temporal
- Validación de datos de entrada
- Prevención de duplicados

### **Logging:**
- Logs detallados para todas las operaciones
- Seguimiento de errores y excepciones
- Información de auditoría
- Métricas de rendimiento

---

## ✅ **Estado de Implementación**

- [x] Modelos de base de datos (Prediction, Match, Team)
- [x] Servicios de predicción
- [x] Endpoints de usuario
- [x] Endpoints de administración
- [x] Validaciones de negocio
- [x] Manejo de errores
- [x] Tests manuales
- [x] Documentación completa

**¡El Sistema de Predicciones está implementado y listo para usar!** 🎉
