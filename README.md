# gemini-storybook-creation

  **Author**: Haizea Rumayor Lazkano
-   **Last update**: October 2025

------------------------------------------------------------------------


##  Ejecución

Para construir y ejecutar el contenedor:

CONOCIDO

```bash
docker build -t gemini-storybook-creator .
docker run -it --rm -v /mnt/c/SABBATIC/Codigo/gemini-storybook-integration/results:/usr/local/app/output -e OUTPUT_DIR=/usr/local/app/output -e KNOWN=1 -e NAME='Estibalitz Arrillaga Monge' -e COMPANY='TRANSOVA NORTE S.L.' -e FUNCTION='CFO/Chief/Director' -e AREA='Departamento Dirección/Presidencia' -e EVENT='Dirfcon' -e PLACE='Madrid' --env-file .env gemini-storybook-creator
```

NO CONOCIDO
```bash
docker build -t gemini-storybook-creator .
docker run -it --rm -v /mnt/c/SABBATIC/Codigo/gemini-storybook-integration/results:/usr/local/app/output -e OUTPUT_DIR=/usr/local/app/output -e KNOWN=0 -e NAME='Estibalitz Arrillaga Monge' -e COMPANY='TRANSOVA NORTE S.L.' -e EVENT='Dirfcon' -e PLACE='Madrid' --env-file .env gemini-storybook-creator
```

