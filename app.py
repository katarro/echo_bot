from flask import Flask, request, Response
import asyncio

from botbuilder.core import (
    BotFrameworkAdapterSettings,
    BotFrameworkAdapter,
    TurnContext
)
from botbuilder.schema import Activity

from bot import MyBot
from config import DefaultConfig

CONFIG = DefaultConfig()

# Crear el adaptador para el bot.
SETTINGS = BotFrameworkAdapterSettings(CONFIG.APP_ID, CONFIG.APP_PASSWORD)
ADAPTER = BotFrameworkAdapter(SETTINGS)

# Crear el bot.
BOT = MyBot()

# Inicializar Flask.
app = Flask(__name__)

# Catch-all para errores.
async def on_error(context: TurnContext, error: Exception):
    # Esta comprobación escribe los errores en la consola .vs. app insights.
    # NOTA: En el entorno de producción, deberías considerar registrar esto en Azure
    #       application insights.
    print(f"\n [on_turn_error] unhandled error: {error}")

    # Enviar un mensaje al usuario.
    await context.send_activity("The bot encountered an error or bug.")
    await context.send_activity(
        "To continue to run this bot, please fix the bot source code."
    )

# Asignar el manejador de errores al adaptador.
ADAPTER.on_turn_error = on_error

# Escuchar las solicitudes entrantes en /api/messages.
@app.route("/api/messages", methods=["POST"])
def messages():
    # Manejador principal de mensajes del bot.
    if "application/json" in request.content_type:
        body = request.json
    else:
        return Response(status=415)

    activity = Activity().deserialize(body)
    auth_header = (
        request.headers["Authorization"] if "Authorization" in request.headers else ""
    )

    # Ejecutar la lógica del bot en una tarea de asyncio.
    async def call_bot_adapter():
        try:
            response = await ADAPTER.process_activity(activity, auth_header, BOT.on_turn)
            if response:
                return Response(response.body, status=response.status)
            return Response(status=200)
        except Exception as exception:
            raise exception

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        task = loop.create_task(call_bot_adapter())
        loop.run_until_complete(task)
        return task.result()
    except Exception as exception:
        return Response(str(exception), status=500)

if __name__ == "__main__":
    # Ejecutar la aplicación en el puerto configurado para el servicio de App de Azure.
    app.run(debug=True, port=CONFIG.PORT)
