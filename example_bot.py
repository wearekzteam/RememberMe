import discord
from discord.ext import commands 
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db

from dotenv import load_dotenv
import os
import datetime
import asyncio

load_dotenv()


firebase_DatabaseUrl = os.getenv('firebase_DatabaseUrl')
firebase_type = os.getenv('firebase_type')
firebase_project_id = os.getenv('firebase_project_id')
firebase_private_key_id = os.getenv('firebase_private_key_id')
firebase_private_key = os.getenv('firebase_private_key')
firebase_client_email = os.getenv('firebase_client_email')
firebase_client_id = os.getenv('firebase_client_id')
firebase_auth_uri = os.getenv('firebase_auth_uri')
firebase_token_uri = os.getenv('firebase_token_uri')
firebase_auth_provider_x509_cert_url = os.getenv('firebase_auth_provider_x509_cert_url')
firebase_client_x509_cert_url = os.getenv('firebase_client_x509_cert_url')
firebase_universe_domain = os.getenv('firebase_universe_domain')


firebase_config = {
    "type":firebase_type,
    "project_id":firebase_project_id,
    "private_key_id":firebase_private_key_id,
    "private_key":firebase_private_key,
    "client_email":firebase_client_email,
    "client_id":firebase_client_id,
    "auth_uri":firebase_auth_uri,
    "token_uri":firebase_token_uri,
    "auth_provider_x509_cert_url":firebase_auth_provider_x509_cert_url,
    "client_x509_cert_url":firebase_client_x509_cert_url,
    "universe_domain":firebase_universe_domain,
}


cred = credentials.Certificate(firebase_config)
firebase_admin.initialize_app(cred, {
    'databaseURL' : firebase_DatabaseUrl
})

token = os.getenv('TOKEN')

intents = discord.Intents.default()
intents.typing = True
intents.presences = True
intents.members = True
intents.message_content = True

PREFIX ='!'

bot = commands.Bot(command_prefix='!', description="General Discord Bot", intents=intents)

notas = {}

@bot.event
async def on_ready() :
    print("I am alive!")

#######################################################################
### Notas        ######################################################
#######################################################################

def obtener_siguiente_id(user_ref):
    notas = user_ref.get()
    if notas is None:
        return 1
    else:
        return max(int(nota_id) for nota_id in notas.keys()) + 1

@bot.command()
async def crearnota(ctx, nombre, *, contenido):
    user_ref = db.reference(f'notas/{ctx.author.id}')
    notas = user_ref.get()
    
    if notas is None:
        new_id = 1
    else:
        ids = [int(nota_id) for nota_id in notas.keys() if nota_id.isdigit()]
        new_id = max(ids, default=0) + 1
    
    nueva_nota = {'nombre': nombre, 'contenido': contenido}
    user_ref.child(str(new_id)).set(nueva_nota)
    await ctx.send(f'Nota "{nombre}" creada con éxito (ID: {new_id}).')

@bot.command()
async def vernota(ctx, id_nota):
    user_ref = db.reference(f'notas/{ctx.author.id}')
    notas = user_ref.get()

    if notas:
        nota = notas.get(id_nota)
        if nota:
            nombre = nota.get('nombre', 'Nombre no disponible')
            contenido = nota.get('contenido', 'Contenido no disponible')
            await ctx.send(f'**ID: {id_nota}**\n**Nombre:**\n{nombre}\n**Descripción:**\n{contenido}')
        else:
            await ctx.send(f'**La nota con ID {id_nota} no existe.**')
    else:
        await ctx.send('No tienes notas.')



# Comando para editar una nota
@bot.command()
async def editarnota(ctx, nombre, *, contenido):
    ref = db.reference(f'notas/{ctx.author.id}/{nombre}')
    nota = ref.get()
    
    if nota:
        ref.update({'contenido': contenido})
        await ctx.send(f'**Nota "{nombre}" editada con éxito. Nuevo contenido:\n{contenido}**')
    else:
        await ctx.send(f'La nota "{nombre}" no existe.')

# Comando para eliminar una nota
@bot.command()
async def eliminarnota(ctx, nombre):
    ref = db.reference(f'notas/{ctx.author.id}/{nombre}')
    if ref.get():
        ref.delete()
        await ctx.send(f'Nota "{nombre}" eliminada con éxito.')
    else:
        await ctx.send(f'La nota "{nombre}" no existe.')

@bot.command()
async def listarnotas(ctx):
    user_ref = db.reference(f'notas/{ctx.author.id}')
    notas = user_ref.get()

    if notas:
        notas_list = '\n'.join([f'**ID: {nota_id}**\n**Nombre:** {nota.get("nombre", "Sin nombre")}' for nota_id, nota in notas.items() if nota_id.isdigit()])
        await ctx.send('**Notas:**\n' + notas_list)
    else:
        await ctx.send('**No tienes notas.**')

#######################################################################
### Recordatorio ######################################################
#######################################################################

def obtener_siguiente_id(user_ref):
    recordatorios = user_ref.get()
    if recordatorios is None:
        return 1
    else:
        ids = [int(recordatorio_id) for recordatorio_id in recordatorios.keys() if recordatorio_id.isdigit()]
        return max(ids, default=0) + 1


@bot.command()
async def recordatorio(ctx, tiempo, *, mensaje):
    try:
        formato_fecha = '%Y-%m-%d %H:%M'
        tiempo = datetime.datetime.strptime(tiempo, formato_fecha)
        tiempo_actual = datetime.datetime.now()

        if tiempo > tiempo_actual:
            diferencia = (tiempo - tiempo_actual).total_seconds()

            user_ref = db.reference(f'recordatorios/{ctx.author.id}')
            new_id = obtener_siguiente_id(user_ref)
            nuevo_recordatorio = {'tiempo': tiempo.strftime(formato_fecha), 'mensaje': mensaje}
            user_ref.child(str(new_id)).set(nuevo_recordatorio)

            await asyncio.sleep(diferencia)

            await ctx.send(f'Recordatorio para {ctx.author.mention}: {mensaje}')
        else:
            await ctx.send('El tiempo debe ser en el futuro.')
    except ValueError:
        await ctx.send(f'El formato de tiempo debe ser: {formato_fecha}')


bot.run(token, reconnect=True)