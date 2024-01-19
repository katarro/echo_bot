from botbuilder.core import ActivityHandler, TurnContext, MessageFactory
from botbuilder.schema import AttachmentData, ChannelAccount, Attachment, CardAction, ActionTypes, HeroCard
from dotenv import load_dotenv
import os
import aiohttp
import convertapi
load_dotenv()

# Configura tu clave secreta de ConvertAPI
convertapi.api_secret = os.getenv("API_SECRET")

class MyBot(ActivityHandler):

    async def on_message_activity(self, turn_context: TurnContext):
        if turn_context.activity.attachments and len(turn_context.activity.attachments) > 0:
            attachment = turn_context.activity.attachments[0]
            if attachment.content_type == "text/csv":
                await turn_context.send_activity("Recibido el archivo .csv")
                await self.process_csv_attachment(attachment, turn_context)
            else:
                await turn_context.send_activity("Por favor, envíame un archivo .csv.")
        else:
            await turn_context.send_activity("Por ahora solo puedo recibir archivos .csv.")



    async def convert_csv_to_xlsx(self, local_csv_path):
        print("Convirtiendo archivo .csv...")
        # Hacer la solicitud a ConvertAPI y obtener el resultado
        conversion_result = convertapi.convert(
            'xlsx', {
                'File': local_csv_path,
                'Delimiter': ','
            },
            from_format='csv'
        )
        
        print("Archivo convertido: " + conversion_result.file.url)
        return conversion_result.file.url

    async def download_file(self, url):
        print("Descargando archivo final...")
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    file_path = 'downloads/' + url.split('/')[-1]
                    with open(file_path, 'wb') as f:
                        f.write(await response.read())
                    return file_path

    async def _download_attachment_and_save(self, attachment: AttachmentData):
        print("Descargando archivo...")
        # Comprobar si el directorio de descargas existe, si no, crearlo
        download_folder = "downloads"
        if not os.path.exists(download_folder):
            os.makedirs(download_folder)

        # Extraer el nombre del archivo del URL
        file_name = attachment.name if attachment.name else attachment.content_url.split("/")[-1]
        file_path = os.path.join(download_folder, file_name)

        # Descargar el archivo
        async with aiohttp.ClientSession() as session:
            async with session.get(attachment.content_url) as response:
                if response.status == 200:
                    with open(file_path, "wb") as file:
                        file.write(await response.read())

        return file_path

    async def _send_excel_file(self, turn_context: TurnContext, file_url: str, file_name: str):
        # Crear una tarjeta con un botón de descarga
        card = HeroCard(
            title="Archivo Convertido",
            subtitle="Haz clic en el botón de abajo para descargar el archivo Excel.",
            buttons=[CardAction(
                type=ActionTypes.open_url,
                title="Descargar Excel",
                value=file_url
            )]
        )

        attachment = Attachment(
            content_type="application/vnd.microsoft.card.hero",
            content=card
        )

        await turn_context.send_activity(MessageFactory.attachment(attachment))



    async def on_members_added_activity(self, members_added: ChannelAccount, turn_context: TurnContext):
        for member_added in members_added:
            if member_added.id != turn_context.activity.recipient.id:
                await turn_context.send_activity("Bienvenido, enviame un archivo .csv.")

    async def process_csv_attachment(self, attachment: AttachmentData, turn_context: TurnContext):

        local_csv_path = await self._download_attachment_and_save(attachment)
        xlsx_url = await self.convert_csv_to_xlsx(local_csv_path)
        print("Archivo convertido: " + xlsx_url)

        if xlsx_url:
            local_xlsx_path = await self.download_file(xlsx_url)
            await turn_context.send_activity("Tu archivo ha sido convertido con éxito.")
            await self._send_excel_file(turn_context, xlsx_url, "converted.xlsx")
        else:
            await turn_context.send_activity("Hubo un problema al convertir el archivo, intenta de nuevo.")
