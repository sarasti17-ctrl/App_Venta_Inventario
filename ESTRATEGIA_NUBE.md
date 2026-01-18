# ☁️ Estrategia de Despliegue en la Nube

Para que el sistema **Sarasti** esté disponible desde cualquier lugar (no solo en la red local), necesitamos migrar tres componentes clave:

## 1. El Código (Control de Versiones)
Necesitamos subir el código a **GitHub**.
*   **Qué hacer**: Crear un repositorio privado en GitHub y subir todos los archivos (excepto `.venv` y `.streamlit/secrets.toml`).
*   **Nota**: El archivo `.gitignore` debe asegurar que las contraseñas locales no se suban.

## 2. La Base de Datos (Cloud DB)
Tu base de datos MariaDB actual vive en tu computadora. Necesitamos una en la nube.
*   **Opción A (Recomendada)**: **Clever Cloud**. Ofrece instancias de MySQL/MariaDB muy fáciles de configurar y con planes gratuitos o muy económicos.
*   **Opción B**: **AWS RDS**. Ideal si buscas máxima escalabilidad, aunque es más complejo de configurar.
*   **Migración**: Exportaríamos tu base de datos actual (SQL) e importaríamos los 623 materiales a la nueva base de datos en la nube.

## 3. El Servidor de la App (Hosting)
*   **Opción A (Gratis)**: **Streamlit Community Cloud**. Es la forma oficial y más rápida. Se conecta directamente a tu GitHub.
*   **Opción B (Profesional)**: **Railway** o **Render**. Son plataformas muy estables donde la app siempre estará "despierta" y lista.

## 🔒 Seguridad y Configuración
Los datos sensibles que hoy están en `secrets.toml` se deben configurar en el panel de control de la nube como **Variables de Entorno**. Así, nadie podrá ver tus contraseñas aunque tengan acceso al código.

---

### 🚀 ¿Cuál es el siguiente paso?
Si decides avanzar, el primer paso sería crear una cuenta en GitHub y una en un proveedor de bases de datos nube (como Clever Cloud). Yo puedo guiarte paso a paso en la configuración de cada uno.
