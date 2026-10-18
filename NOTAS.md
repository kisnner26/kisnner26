# notas del escritorio

el sitio vive en `docs/` y se publica con github pages en https://kisnner26.github.io/kisnner26/.
los svg del readme y `docs/snapshot.json` los regenera `scripts/generate.py` cada día (ver `.github/workflows/update.yml`).

## correo directo desde "escríbeme"

sin configurar nada, el botón de enviar abre el correo del visitante con el mensaje listo.
para que llegue directo: crear una clave gratis en web3forms.com con el correo de contacto y pegarla en `CONTACT.key` dentro de `docs/index.html`.

## atajos

| tecla | qué hace |
|---|---|
| tab | abre la vista flip 3d |
| 1 a 5 | abre proyectos, marea, tocar, escríbeme o el juego |
| a a l | en el juego revienta la burbuja de esa letra |
| esc | cierra el panel, el juego o el flip |
| ctrl + enter | envía el mensaje en "escríbeme" |

## secretos

- escribir `aero` cambia a noche y de vuelta a mediodía; `sol` fuerza mediodía
- el código konami hace llover peces
- doble clic sobre el agua hace saltar al delfín
- 45 segundos sin tocar nada activan el salvapantallas de pecera

## rendimiento

- el agua baja su resolución sola si los fotogramas tardan demasiado
- con "reducir movimiento" activo en el sistema se apagan hojas, medusas, delfín y parallax
