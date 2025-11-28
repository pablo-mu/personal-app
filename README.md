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

## 🏗️ Estructura del Proyecto y Principios de Diseño

El sistema sigue una **Arquitectura Hexagonal** para desacoplar responsabilidades:

- **Capa de Presentación**: UI con Dash.
- **Capa de Aplicación**: Lógica de negocio.
- **Capa de Dominio**: Entidades y reglas (SOLID, KISS, DRY).
- **Capa de Infraestructura**: Persistencia (SQLite).

### Principios Clave

- **SOLID**: Código flexible y mantenible.
- **KISS**: Simplicidad ante todo.
- **DRY**: Evitar duplicidad.
- **Seguridad de Tipos**: Tipado estático robusto.
- **Patrones**: Factory y Repository.

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
