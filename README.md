# Prode Master

## Stack
- Node.js
- TypeScript
- Express
- Prisma ORM
- SQLite
- fluentd (para los logs)
- API-Football

## Requisitos
- make (sistema de construcción)
- python y pip (ultimas versiones en lo posible, sino chequear en caso de error)

## Ejecución del servidor backend

### Entorno
```bash
python -m venv env
```
#### Activación en Unix / Terminal git bash
```bash
source env/bin/activate
```

#### Activación en Windows
cmd
```cmd
env\Scripts\activate
```

powershell
```powershell
.\env\Scripts\Activate.ps1
```

### Comandos Make
Instalación y ejecución
```bash
make install
make run
```

La aplicación estará disponible en http://localhost:6767

## Testing
```bash
pytest -v tests
```
