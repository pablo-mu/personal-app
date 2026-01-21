# 💰 Sistema de Finanzas Personales

> Propuesta de Proyecto y Documentación

![Status](https://img.shields.io/badge/Status-En%20Desarrollo-yellow)
![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![License](https://img.shields.io/badge/License-Proprietary-red)

Este repositorio contiene la propuesta de proyecto y la documentación para un sistema de finanzas personales. El objetivo es desarrollar una aplicación eficiente para la gestión de finanzas, incluyendo seguimiento de ingresos, gastos, presupuestos y metas.

---

## 📖 Descripción del Proyecto

El proyecto es una **app de finanzas personales** desarrollada con **Python, FastAPI, Dash y SQLite**.

Se busca construir un código limpio, modular y escalable siguiendo principios como **SOLID, KISS, DRY** y **Arquitectura Hexagonal**.

### Enfoque

1. **Fase Inicial**: Sistema de contabilidad de partida doble para un único usuario.
2. **Expansión**: Múltiples usuarios, integración bancaria, simulaciones financieras y migración a PostgreSQL o nubes personales.

## ✨ Características Principales (Fase Inicial)

- 🏦 **Gestión de cuentas**: Crear, editar y eliminar cuentas.
- 📝 **Registro de transacciones**: Control de ingresos y gastos (Partida Doble).
- 🏷️ **Categorías personalizables**: Organización flexible.
- 🔄 **Gestión de Bizums/Devoluciones**: Ajustes de movimientos sin falsear gastos/ingresos.
- 📊 **Reportes financieros**: Balances y resúmenes básicos.
- 🖥️ **Interfaz UI**: Web amigable con Dash.
- 🔒 **Seguridad**: Protección básica de datos.

## 🛠️ Tecnologías Utilizadas

| Categoría | Tecnología |
|-----------|------------|
| **Lenguaje** | Python 🐍 |
| **Backend** | FastAPI ⚡ |
| **Frontend** | Dash 📊 |
| **Base de Datos** | SQLite (Provisional) 🗄️ |
| **Control de Versiones** | Git & GitHub 🐙 |
| **Documentación** | Markdown & Sphinx 📄 |

## 🏗️ Arquitectura y Flujo de la Aplicación

El sistema sigue una **Arquitectura Hexagonal (Ports & Adapters)** estricta. El objetivo es que el núcleo de la aplicación (Dominio) no dependa de nada externo (Base de datos, UI, Frameworks).

### 📂 Estructura de Carpetas y Responsabilidades

La estructura de `src/` refleja directamente las capas de la arquitectura:

#### 1. `src/domain/` (El Núcleo)
*   **Qué es:** El corazón del negocio. Aquí viven las reglas que no cambian aunque cambiemos la base de datos o la web.
*   **Contenido:**
    *   `models.py`: Entidades (`Account`, `Transaction`). Son objetos puros (dataclasses).
    *   `value_objects.py`: Objetos inmutables como `Money`.
    *   `exceptions.py`: Errores de negocio (`AccountAlreadyExistsError`).
*   **Regla:** No importa nada de otras capas. Solo librerías estándar de Python.

#### 2. `src/application/` (El Orquestador)
*   **Qué es:** La capa que "hace que las cosas pasen". Conecta la UI con el Dominio y la Infraestructura.
*   **Contenido:**
    *   `ports.py`: **Interfaces (Contratos)**. Define *qué* necesitamos (ej: `AbstractAccountRepository`), pero no *cómo* se hace.
    *   `services/`: Lógica de casos de uso (ej: `AccountService`). Recibe peticiones, valida y llama a los puertos.
    *   `dtos.py`: **Data Transfer Objects**. Estructuras de datos para comunicarse con el mundo exterior (UI).
*   **Regla:** Solo importa de `domain`.

#### 3. `src/infrastructure/` (Los Detalles)
*   **Qué es:** Implementaciones concretas de los puertos definidos en Aplicación.
*   **Contenido:**
    *   `persistence/models.py`: Modelos de SQLAlchemy (Tablas de BD).
    *   `persistence/repositories/`: Implementación real de los repositorios (ej: `SQLAlchemyAccountRepository`). Aquí ocurre la magia de SQL.
*   **Regla:** Depende de `domain` (para devolver entidades) y `application` (para implementar interfaces).

#### 4. `src/ui/` (La Entrada)
*   **Qué es:** Lo que ve el usuario. En este caso, Dash.
*   **Contenido:**
    *   `views/`: Componentes visuales y callbacks.
*   **Regla:** Usa los Servicios de la capa de Aplicación para obtener datos. Nunca llama a la BD directamente.

---

### 🔄 Flujo de una Petición (Ejemplo: Buscar Cuentas)

Para entender cómo se orquesta todo, sigamos el viaje de una búsqueda desde que el usuario hace clic hasta que ve los resultados.

1.  **UI (Mundo Exterior)**:
    *   El usuario escribe "Ahorro" en el buscador de Dash (`ui`).
    *   Se crea un **DTO** de entrada: `AccountFilterDTO(name_contains="Ahorro")`.

2.  **Servicio (Traductor)**:
    *   La vista llama a `AccountService.list_accounts(filters=dto)`.
    *   El servicio **traduce** el DTO (objeto de aplicación) a `AccountSearchCriteria` (objeto de dominio).
    *   *¿Por qué?* Para que el repositorio no dependa de la UI/DTOs.

3.  **Repositorio (Infraestructura)**:
    *   El servicio llama a `repository.search(criteria)`.
    *   La implementación (`SQLAlchemyAccountRepository`) traduce el criterio de dominio a una consulta SQL (`SELECT * FROM accounts WHERE ...`).
    *   La BD devuelve filas crudas.
    *   El repositorio convierte esas filas a Entidades de Dominio (`Account`) y las devuelve.

4.  **Retorno (Respuesta)**:
    *   El servicio recibe la lista de `Account`.
    *   El servicio las convierte a `AccountOutputDTO` (JSON-friendly).
    *   La UI recibe los DTOs y pinta la tabla.

### Principios Clave Aplicados

- **Inversión de Dependencias (DIP)**: Los módulos de alto nivel (Aplicación) no dependen de los de bajo nivel (Infraestructura). Ambos dependen de abstracciones (Puertos).
- **Separación de Intereses**: La UI no sabe de SQL. El Dominio no sabe de HTTP/HTML.
- **DTO vs Entidad**: Usamos DTOs para entrada/salida y Entidades para lógica interna.

## 📅 Fases de Desarrollo

- [ ] **Fase 1**: Funcionalidades básicas (Cuentas, Transacciones, Reportes).
- [ ] **Fase 2**: Mejora de UI/UX.
- [ ] **Fase 3**: Funcionalidades avanzadas (Multi-usuario, Bancos).
- [ ] **Fase 4**: Optimización y migración a PostgreSQL.
- [ ] **Fase 5**: Análisis avanzado y simulaciones.
- [ ] **Fase 6**: Sincronización en la nube.

## 🤝 Contribuciones

Actualmente cerrado a contribuciones externas.

## ⚖️ Licencia

### Personal — No comercial — No transferible

Copyright (c) 2025 [Pablo Muñoz Alcaide]

> ⚠️ Este repositorio y su contenido son de carácter personal. Queda prohibida la reproducción, distribución o uso comercial sin autorización escrita.
