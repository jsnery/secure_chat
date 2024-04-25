from app.models.json_base import SecureChat, User
import os
from app import app
from flask import render_template, request, url_for, session, redirect
from flask import jsonify, make_response, flash, send_from_directory
from datetime import datetime
import pytz  # type: ignore
from random import randint, seed, shuffle
import glob
import re


def set_user(
        password: str,
        nickname: str,
        username='Privado',
        server_name='chat'
):
    if username == 'Privado':
        user = User(nickname=nickname, password=password)
        return user
    user = User(nickname=nickname, password=password,
                user=username, server_name=server_name)
    return user


def allowed_file(filename):
    ALLOWED_EXTENSIONS = {
        'png',
        'jpg',
        'jpeg',
        'gif',
        'webp',
        'avif',
        'heic',
        'mp4',
        'avi',
        'mov',
        'heif',
        'apk'
    }
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def allowed_profile(filename):
    ALLOWED_EXTENSIONS = {
        'png',
        'jpg',
        'jpeg'
    }
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def directory_gen(serve_name, type_):
    def encrypt(server, se_ed):
        server = list(server)
        seed(se_ed)
        shuffle(server)
        return ''.join(server)

    if type_ == 'img':
        result = f'./app/data/chat/{encrypt(serve_name, 40028922)}/img'
    if type_ == 'video':
        result = f'./app/data/chat/{encrypt(serve_name, 40028922)}/videos'
    if type_ == 'audio':
        result = f'./app/data/chat/{encrypt(serve_name, 40028922)}/audios'
    if type_ == 'others':
        result = f'./app/data/chat/{encrypt(serve_name, 40028922)}/others'

    if not os.path.exists(result):
        os.makedirs(result)

    return result


tz = pytz.timezone('America/Sao_Paulo')
hora_atual = datetime.now(tz).strftime('%H:%M')
app.secret_key = 'sfs6u-e0122ed66f'
app.config['PROFILE_FOLDER'] = './app/data/chat/.src/profiles'
extensoes_img = (
    '.png',
    '.jpg',
    '.jpeg',
    '.webp',
    '.avif',
    '.heic',
    '.heif',
    '.gif'
)


# Rota para a página de login
@app.route('/', methods=['GET', 'POST'])
def login():
    nickname2 = request.cookies.get('nickname')
    password = request.cookies.get('password')
    session['password_verified'] = False

    if nickname2 is not None and password is not None:
        usuario = set_user(password, nickname2)
        secure_chat = SecureChat(user=usuario)

        if secure_chat.user_login(usuario):
            session['username2'] = secure_chat.user_username_extract(usuario)
            session['id'] = secure_chat.user_id_extract(usuario)
            session['nickname'] = nickname2
            session['password'] = password
            session['usuario'] = usuario
            session['secure_chat'] = secure_chat
            usuario.user_server_name_extract
            # print(f"Usuario logado: {usuario.user}")
            return redirect(url_for('entrada'))

    if request.method == 'POST':
        nickname2 = request.form.get('nickname').lower()
        password = request.form.get('password')

        if nickname2 is None \
            or nickname2.isspace() \
                or password is None \
                or password.isspace():
            flash('Preencha todos os campos')
            return redirect(url_for('login'))

        usuario = set_user(password, nickname2)
        secure_chat = SecureChat(user=usuario)
        usuario.user = secure_chat.user_username_extract(usuario)
        if secure_chat.user_login(usuario):
            resp = make_response(redirect(url_for('entrada')))
            resp.set_cookie('nickname', nickname2)
            resp.set_cookie('password', password)
            session['username2'] = secure_chat.user_username_extract(usuario)
            session['id'] = secure_chat.user_id_extract(usuario)
            session['nickname'] = nickname2
            session['password'] = password
            session['usuario'] = usuario
            session['secure_chat'] = secure_chat
            usuario.user_server_name_extract
            # print(f"Usuario logado: {usuario.user}")
            return resp

        else:
            flash('Usuário ou senha incorretos')
            return redirect(url_for('login'))

    return render_template('home/login.html')


# API para login
@app.route('/<string:username>&<string:password>', methods=['GET'])
def login2(username, password):
    usuario = set_user(password, username.lower())
    secure_chat = SecureChat(user=usuario)
    usuario.user = secure_chat.user_username_extract(usuario)
    if secure_chat.user_login(usuario):
        session['username2'] = secure_chat.user_username_extract(usuario)
        session['id'] = secure_chat.user_id_extract(usuario)
        session['nickname'] = username
        session['password'] = password
        session['usuario'] = usuario
        session['secure_chat'] = secure_chat
        usuario.user_server_name_extract
        # print(f"Usuario logado: {usuario.user}")
        return redirect(url_for('entrada'))

    else:
        flash('Usuário ou senha incorretos')
        return redirect(url_for('login'))


# API para checar se o usuário existe
@app.route('/checar/<string:username>&<string:password>', methods=['GET'])
def checar(username, password):
    usuario = set_user(password, username.lower())
    secure_chat = SecureChat(user=usuario)
    usuario.user = secure_chat.user_username_extract(usuario)
    if secure_chat.user_login(usuario):
        return jsonify({'status': True})
    return jsonify({'status': False})


# Rota para a página de cadastro
@app.route('/cadastrar', methods=['GET', 'POST'])
def cadastrar():
    if request.method == 'POST':
        username = request.form.get('username').lower()
        nickname2 = request.form.get('nickname').lower()
        password = request.form.get('password')

        if nickname2 is None \
            or nickname2.isspace() \
                or password is None \
                or password.isspace() \
                or username is None \
                or username.isspace():
            flash('Preencha todos os campos')
            return redirect(url_for('cadastrar'))

        if len(password) < 6:
            flash('Senha deve ter 6 ou mais caracteres')
            return redirect(url_for('cadastrar'))

        if len(nickname2) < 6:
            flash('Nickname deve ter 6 ou mais caracteres')
            return redirect(url_for('cadastrar'))

        if username.isdigit() \
            or not username.isalpha() \
                or any(char.isdigit() for char in username):
            flash('Somente primeiro nome')
            return redirect(url_for('cadastrar'))

        usuario = set_user(
            password=password,
            nickname=nickname2,
            username=username
        )

        secure_chat = SecureChat(user=usuario)

        if secure_chat.user_exists(usuario):
            flash('Usuário já existe')
            return redirect(url_for('cadastrar'))

        secure_chat.user_register(usuario)
        secure_chat.post_profile_pic_url(usuario, 'default.jpg')
        return redirect(url_for('login'))

    return render_template('home/cadastro.html')


@app.route('/cadastro/<string:firstname>&<string:password>&<string:nickname>', methods=['GET'])  # noqa
def cadastro2(firstname, password, nickname):
    if nickname is None \
            or nickname.isspace() \
            or password is None \
            or password.isspace() \
            or firstname is None \
            or firstname.isspace():
        return jsonify({'status': False})

    if len(password) < 6:
        return jsonify({'status': False})

    if len(nickname) < 6:
        return jsonify({'status': False})

    if firstname.isdigit() \
        or not firstname.isalpha() \
            or any(char.isdigit() for char in firstname):
        return jsonify({'status': False})

    usuario = set_user(password, nickname, firstname)
    secure_chat = SecureChat(user=usuario)
    if secure_chat.user_exists(usuario):
        return jsonify({'status': False})
    secure_chat.user_register(usuario)
    secure_chat.post_profile_pic_url(usuario, 'default.jpg')
    return jsonify({'status': True})


# Rota para a página de entrada
@app.route('/entrada', methods=['GET', 'POST'])
def entrada():

    def get_friend_pic(user, id='default'):
        url = f'/chatx/.src/profiles/{id}.jpg'

        if secure_chat.get_profile_pic_url(user):
            return url
        else:
            return '/chatx/.src/profiles/default.jpg'

    usuario = set_user(
        session.get('password'),
        session.get('nickname'),
        session.get('username2')
    )
    usuario.user_server_name_extract
    # print(usuario.server_name)
    secure_chat = SecureChat(user=usuario)
    session['secure_chat'] = secure_chat
    amigos = usuario.get_friends
    lastmsg = usuario.get_private_room_last_message(usuario.nickname)
    print(lastmsg)
    # Se 'reads' não estiver definido, defina-o como uma lista vazia
    reads = [v['read'] for v in lastmsg.values() if v['whosend'] !=
             usuario.user] if lastmsg else []
    for i in reads:
        print(i)
    lastserver = usuario.get_last_server_name()
    username = session.get('username2')
    session['id2'] = secure_chat.user_id_extract(usuario)

    if secure_chat.get_profile_pic_url(usuario):
        profile_pic_url = f'/chatx/.src/profiles/{session['id2']}.jpg'
    else:
        profile_pic_url = '/chatx/.src/profiles/default.jpg'

    if request.method == 'POST':
        custom_username = request.form.get('custom_username')
        if custom_username is not None and custom_username != '':
            username = custom_username

        other_server_name = None

        try:
            other_server_name = request.form.get(
                'other_server_name').replace(' ', '_').lower()

            session['other_server_name'] = other_server_name
        except Exception:
            pass

        usuario.user = username

        def gerar_session():
            # print("estou aqui")
            session['username'] = username
            session['username3'] = username
            session['server_name2'] = usuario.server_name
            session['amigos'] = amigos

        if other_server_name is not None \
            and not other_server_name.isspace() \
                and other_server_name != 'chat' \
            and other_server_name != 'secure_chat':  # noqa
            # print("#" * 100)
            usuario.server_name = other_server_name

        else:
            flash('Nome de sala inválido')
            gerar_session()
            return redirect(url_for(
                'entrada',
                username=username,
                server_name=usuario.server_name,
                amigos=amigos,
                user_id=session['id2'],
                profile_pic_url=profile_pic_url,
                get_profile_pic_url=get_friend_pic,
                notificar=usuario.verificar_se_existe_nova_mensagem,
                lastmsg=lastmsg,
                lastserver=lastserver,
                reads=reads
            ))

        if other_server_name == '':
            usuario.user_server_name_extract
            other_server_name = usuario.server_name

        if len(other_server_name) < 6:
            flash('Sala deve ter mais de 6 caracteres')
            gerar_session()
            return redirect(url_for(
                'entrada',
                username=username,
                server_name=usuario.server_name,
                amigos=amigos,
                user_id=session['id2'],
                profile_pic_url=profile_pic_url,
                get_profile_pic_url=get_friend_pic,
                notificar=usuario.verificar_se_existe_nova_mensagem,
                lastmsg=lastmsg,
                lastserver=lastserver,
                reads=reads

            ))

        if secure_chat.is_user_valid(usuario):
            gerar_session()
            friend_name = request.form.get('friend_name')
            friend_nickname = request.form.get('friend_nickname')
            friend_id = request.form.get('friend_id')

            session['friend_name'] = friend_name
            session['friend_nickname'] = friend_nickname
            session['friend_id'] = friend_id
            usuario.save_last_server_name()
            return redirect(url_for(
                'chat',
                username=username,
                server_name=usuario.server_name,
                amigos=amigos,
                user_id=session['id2'],
                profile_pic_url=profile_pic_url,
                friend_name=friend_name,
                friend_nickname=friend_nickname,
                friend_id=friend_id,
                reads=reads
            ))

        else:
            return redirect(url_for('entrada'))
    print(f"Usuario logado: {username}")
    return render_template(
        'home/entrada.html',
        username=username,
        server_name=usuario.server_name,
        amigos=amigos,
        user_id=session['id2'],
        profile_pic_url=profile_pic_url,
        get_profile_pic_url=get_friend_pic,
        notificar=usuario.verificar_se_existe_nova_mensagem,
        lastmsg=lastmsg,
        lastserver=lastserver,
        reads=reads
    )


@app.route('/check_notifications', methods=['GET'])
def check_notifications():
    usuario = set_user(
        session.get('password'),
        session.get('nickname'),
        session.get('username2')
    )
    secure_chat = SecureChat(user=usuario)  # noqa
    private_room = request.args.get('private_room')
    # Substitua isso pela sua lógica para verificar notificações
    hasNotification = usuario.verificar_se_existe_nova_mensagem(private_room)

    return jsonify({'hasNotification': hasNotification})


@app.route('/entrada/changepassword', methods=['POST'])
def change_password():
    usuario = set_user(
        session.get('password'),
        session.get('nickname'),
        session.get('username2')
    )

    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    if new_password is not None and not new_password.isspace():
        if usuario.change_password(current_password, new_password):
            return redirect(url_for('login'))
        else:
            return '', 401

    return redirect(url_for('entrada'))


@app.route('/entrada/lastmsgcheck', methods=['GET'])
def check_msg():
    usuario = set_user(
        session.get('password'),
        session.get('nickname'),
        session.get('username2')
    )
    private_room = request.args.get('private_room')

    len_msg2 = usuario.verificar_lastmsg(private_room)

    if session.get('len_msg', False) < len_msg2:
        session['len_msg'] = len_msg2
        return jsonify({'status': True})

    return jsonify({'status': False})


# API para verificar se há notificações
@app.route('/check_notifications/<string:username>', methods=['GET'])
def check_notifications2(username):
    usuario = set_user(
        session.get('password'),
        username,
        session.get('username2')
    )
    secure = SecureChat(user=usuario)
    usuario.user = secure.user_username_extract(usuario)
    if usuario.get_private_room_read(username):
        return jsonify({'status': True})
    else:
        return jsonify({'status': False})


# Rota para logout
@app.route('/entrada/logout')
def logout():
    resp = make_response(redirect(url_for('login')))
    resp.set_cookie('nickname', '', expires=0)
    resp.set_cookie('password', '', expires=0)
    return resp


@app.route('/entrada/logout2')
def logout2():
    resp = make_response(redirect(url_for('appx')))
    resp.set_cookie('nickname', '', expires=0)
    resp.set_cookie('password', '', expires=0)
    return resp


@app.route('/app')
def appx():
    return render_template('home/app.html')


# Rota para o chat
@app.route('/chat', methods=['GET', 'POST'])
def chat():
    def check_message_youtube(message):
        if "class='respostas'" in message:
            return message
        if 'https://www.youtube.com/' in message or 'https://youtu.be/' in message:  # noqa
            youtube_regex = r'(?:https?://)?(?:www\.)?(?:youtube\.com/watch\?v=|youtu\.be/)([^&\n]+)'  # noqa
            youtube_url = re.findall(youtube_regex, message)
            # print(youtube_url)
            if youtube_url:
                # Extract the YouTube URL from the tuple
                youtube_url = ''.join(youtube_url[0])
                video_code = youtube_url.split('=')[-1]
                html = f"""
                <div class="youtube-video">
                    <iframe width="100%" height="180px" class='youtube-video' src="https://www.youtube.com/embed/{video_code}" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>
                </div>
                """  # noqa
                return html
        # print(message)
        if 'https://www.youtube.com/shorts/' in message:
            print(message)
            youtube_url = message.split('https://www.youtube.com/shorts/')[1]
            video_code = youtube_url
            # print(video_code)
            html = f"""
            <div class="youtube-shorts">
                <iframe width="100%" height="550px" class='youtube-shorts' src="https://www.youtube.com/embed/{video_code}" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>
            </div>
            """  # noqa
            return html
        if 'https://youtube.com/shorts/' in message:
            print(message)
            youtube_url = message.split('https://youtube.com/shorts/')[1]
            video_code = youtube_url
            # print(video_code)
            html = f"""
            <div class="youtube-shorts">
                <iframe width="100%" height="550px" src="https://www.youtube.com/embed/{video_code}" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>
            </div>
            """  # noqa
            return html
        return message

    try:
        def get_friend_pic(user, id):
            url = f'/chatx/.src/profiles/{id}.jpg'

            if secure_chat.get_profile_pic_url(user):
                return url
            else:
                return '/chatx/.src/profiles/default.jpg'

        # friend_nickname = session.get('friend_nickname')
        # friend_id = session.get('friend_id')
        usuario = set_user(
            session.get('password'),
            session.get('nickname'),
            session.get('username2'),
            server_name=session['server_name2']
        )

        session['server_file'] = usuario.server_name

        secure_chat = SecureChat(user=usuario)
        filename = session.get('filename2')
        photos = []
        videos = []
        data = None
        if request.is_json:
            data = request.get_json()
        for file in os.listdir(directory_gen(usuario.server_name, 'img')):
            if file.lower().endswith(extensoes_img):
                photos.append(file)

        for file in os.listdir(directory_gen(usuario.server_name, 'video')):
            if file.lower().endswith(('.mp4', '.webm')):
                videos.append(file)

        mensagens = secure_chat.get_chat_messages
        username = session.get('username3')
        if request.method == 'POST':
            message = request.form.get('message')
            try:
                message = request.form['message']

            except Exception:
                if data:
                    message = data.get('message')

            if message and not message.isspace():
                try:
                    message = check_message_youtube(message)
                    secure_chat.add_message(message, username)
                except Exception as e:
                    print(f"Error: {e}")  # Debug print
                return ('', 204)
        return render_template(
            'chat/chat.html',
            mensagens=mensagens,
            photos=photos,
            videos=videos,
            filename=filename,
            username=request.args.get('username'),
            server_name=request.args.get('server_name'),
            amigos=request.args.get('amigos'),
            user_id=request.args.get('user_id'),
            profile_pic_url=request.args.get('profile_pic_url'),
            get_profile_pic_url=get_friend_pic,
            friend_name=request.args.get('friend_name'),
            friend_nickname=request.args.get('friend_nickname'),
            friend_id=request.args.get('friend_id'),
            reads=request.args.get('reads')
        )
    except Exception as e:
        app.logger.error(f"Erro ao processar a solicitação: {e}")
        print(f"Erro ao processar a solicitação: {e}")
        raise


# Retorna as mensagens do chat
@app.route('/chat/messages', methods=['GET', 'POST'])
def chat_messages():

    def checar_apagada(message):
        if '<span class="deletedx1"><i class="material-icons block">block</i> <em>Mensagem apagada</em></span>' not in message:  # noqa
            return True
        return False

    def message_type_check(message) -> bool:
        if "<img" not in message:
            if "<video" not in message:
                if "<audio" not in message:
                    if "<button" not in message:
                        if "class='respostas'" not in message:
                            if 'class="youtube-video"' not in message:
                                if 'class="youtube-shorts"' not in message:
                                    return True
        return False

    def message_type_check_txt(message: dict[str], original_message):
        try:
            if "<img" in original_message:
                return f"<span class='respostax1'>Imagem enviada {message['dia']} {message['hora']} por {message['username'].capitalize()}</span>"  # noqa
            if "<video" in original_message:
                return f"<span class='respostax1'>Vídeo enviado {message['dia']} {message['hora']} por {message['username'].capitalize()}</span>"  # noqa
            if "<audio" in original_message:
                return f"<span class='respostax1'>Áudio enviado {message['dia']} {message['hora']} por {message['username'].capitalize()}</span>"  # noqa
            if "<button" in original_message:
                return f"<span class='respostax1'>Arquivo enviado {message['dia']} {message['hora']} por {message['username'].capitalize()}</span>"  # noqa
            if "class='respostas'" in original_message:
                return f"<span class='respostax1'>Resposta enviada {message['dia']} {message['hora']} por {message['username'].capitalize()}</span>"  # noqa
            if 'class="youtube-shorts"' in original_message:
                return f"<span class='respostax1'>Shorts enviado {message['dia']} {message['hora']} por {message['username'].capitalize()}</span>"  # noqa
            if 'class="youtube-video"' in original_message:
                return f"<span class='respostax1'>Vídeo enviado {message['dia']} {message['hora']} por {message['username'].capitalize()}</span>"  # noqa
        except Exception:
            if "<img" in original_message:
                return f"<span class='respostax1'>Imagem enviada às {message['hora']} por {message['username'].capitalize()}</span>"  # noqa
            if "<video" in original_message:
                return f"<span class='respostax1'>Vídeo enviado às {message['hora']} por {message['username'].capitalize()}</span>"  # noqa
            if "<audio" in original_message:
                return f"<span class='respostax1'>Áudio enviado às {message['hora']} por {message['username'].capitalize()}</span>"  # noqa
            if "<button" in original_message:
                return f"<span class='respostax1'>Arquivo enviado às {message['hora']} por {message['username'].capitalize()}</span>"  # noqa
            if "class='respostas'" in original_message:
                return f"<span class='respostax1' >Resposta enviada às {message['hora']} por {message['username'].capitalize()}</span>"  # noqa
            if 'class="youtube-shorts"' in original_message:
                return f"<span class='respostax1'>Shorts enviado às {message['hora']} por {message['username'].capitalize()}</span>"  # noqa
            if 'class="youtube-video"' in original_message:
                return f"<span class='respostax1'>Vídeo enviado às {message['hora']} por {message['username'].capitalize()}</span>"  # noqa

    def hour_user_status(message_dict: dict[str], read, type):
        if type == "sent":
            try:
                return f"{message_dict['dia']} {message_dict['hora']} - {message_dict['username'].capitalize()}{read}  "  # noqa
            except Exception:
                return f"{message_dict['hora']} - {message_dict['username'].capitalize()}{read}  "  # noqa

        if type == "received":
            try:
                return f"{message_dict['username'].capitalize()} - {message_dict['dia']} {message_dict['hora']}"  # noqa
            except Exception:
                return f"  {message_dict['username'].capitalize()} - {message_dict['hora']}"  # noqa

    usuario = set_user(
        session.get('password'),
        session.get('nickname'),
        session.get('username2'),
        server_name=session['server_name2']
    )

    secure_chat = SecureChat(user=usuario)
    # usr = usuario.user
    user3 = session.get('username3')
    try:
        # print(secure_chat.get_chat_messages)
        messages = secure_chat.get_chat_messages(usuario)

    except Exception:
        return render_template('home/login.html')
    messages_html = ''
    for message in messages:
        # print(type(message), message)
        if 'message' in message and isinstance(message['message'], str):
            original_message = message['message'] if 'Respondendo para:' not in message['message'] else message['message'].split('Respondendo para:')[1]  # noqa

        read_status = f'''<svg class="read-status" xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 60 40">
                            <path d="M10 20 l10 10 l20 -20" stroke="#D3D3D3" stroke-width="3" fill="none" />
                            <path d="M10 20 l10 10 l20 -20" stroke="#D3D3D3" stroke-width="3" fill="none" transform="translate(20, 0)" />
                        </svg>'''  # noqa
        if 'read' in message and message['read']:
            read_status = f'''<svg class="read-status" xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 60 40">
                                <path d="M10 20 l10 10 l20 -20" stroke="#00FFFF" stroke-width="3" fill="none" />
                                <path d="M10 20 l10 10 l20 -20" stroke="#00FFFF" stroke-width="3" fill="none" transform="translate(20, 0)" />
                            </svg>'''  # noqa

        # print(f'{message['username']}: {message['message']}')

        messages_html += f'''
            <body>  
                {f'''
                <div class="chat-container messagesent">
                    <div class="msgsend" style="font-size: 17px;">{original_message}</div>
                    <div style="display: flex; justify-content: space-between;">
                        <div>
                            {f'''<button class="btn transparent showhid2-button" style="height: 16px; line-height: 9px; padding: 0 2px; box-shadow: none;">
                                <i class="material-icons" style="font-size: 16px; color: #ffffff;">chevron_left</i>
                            </button>''' if checar_apagada(original_message) else ''}
                            {f'''<button class="btn transparent reply-button" style="height: 16px; line-height: 9px; padding: 0 2px; box-shadow: none; display:none;">
                                <i class="material-icons" style="font-size: 16px; color: #ffffff;">reply</i>
                            </button>'''}
                            {f'''<button class="btn transparent deletemsg-button" user-id="{message['id']}" style="height: 16px; line-height: 9px; padding: 0 0px; box-shadow: none; display:none;">
                                <i class="material-icons" style="font-size: 16px; color: #ffffff;">delete_forever</i>
                            </button>''' if message['username'] == user3 else ''}
                        </div>
                        <div class="datamsg1" style="font-size: 10px;">
                            <b>{hour_user_status(message, read_status, "sent")}</b>
                        </div>
                    </div>
                    <form method="POST" action="/chat/reply" class="reply-form formreply" style="display: none;">
                        <div class="center-container" style="color: #ffffff; display: flex;">
                            <input type="hidden" name="original_message" value="<div class='respostas'>{f'''<b>{message['username'].capitalize()}</b><br> {original_message}''' if message_type_check(original_message) else message_type_check_txt(message, original_message)}</div>">
                            <input type="hidden" name="message_id" value="{message['id']}">
                            <input class="formreplytext" type="text" id="message" name="message" required autocomplete="off">
                            <button class="btn transparent formreplysubmit" type="submit" name="action" style=""><i class="material-icons">send</i></button>
                        </div>
                    </form>
                    ''' if message['username'] == user3 else f'''
                <div class="chat-container messagereceived">
                    <div class="msgreceive" style="font-size: 17px;">{original_message}</div>
                    <div style="display: flex; justify-content: space-between; font-size: 10px;">
                        <b>   {hour_user_status(message, read_status, "received")}</b>
                        <div>
                            {f'''<button class="btn transparent deletemsg-button" user-id="{message['id']}" style="height: 18px; line-height: 9px; padding: 0 0px; box-shadow: none; display:none;">
                                <i class="material-icons" style="font-size: 16px; color: #ffffff;">delete_forever</i>
                            </button>''' if message['username'] == user3 else ''}
                            {f'''<button class="btn transparent reply-button" style="height: 18px; line-height: 9px; padding: 0 0px; box-shadow: none; display:none;">
                                <i class="material-icons" style="font-size: 16px; color: #ffffff;">reply</i>
                            </button>'''}
                            {f'''<button class="btn transparent showhid-button" style="height: 18px; line-height: 9px; padding: 0 0px; box-shadow: none;">
                                <i class="material-icons" style="font-size: 16px; color: #ffffff;">chevron_right</i>
                            </button>''' if checar_apagada(original_message) else ''}
                        </div>
                    </div>
                    <form method="POST" action="/chat/reply" class="reply-form formreply2" style="display: none;">
                        <div class="center-container" style="color: #ffffff; display: flex;">
                            <input type="hidden" name="original_message" value="<div class='respostas'>{f'''<b>{message['username'].capitalize()}</b><br> {original_message}''' if message_type_check(original_message) else message_type_check_txt(message, original_message)}</div>" style="display: inline-block;">
                            <input type="hidden" name="message_id" value="{message['id']}" style="display: inline-block;">
                            <input class="formreplytext" type="text" id="message" name="message" required autocomplete="off" style="color: #000000; height: 30px; display: inline-block;">
                            <button class="btn transparent formreplysubmit" type="submit" name="action" style="box-shadow: none; display: inline-block; color: #ffffff;"><i class="material-icons">send</i></button>
                        </div>
                    </form>
                    '''}
                </div>
                <script>
                    $(document).ready(function() {{
                        $('.messagesent .msgsend').each(function() {{
                            var html = $(this).html().trim();
                            if (html == '<span class="deletedx1"><i class="material-icons block">block</i> <em>Mensagem apagada</em></span>') {{
                                $(this).parent().css('margin-left', '40%');
                            }}
                        }});
                    }});
                </script>
                <script>
                    $(document).ready(function() {{
                        $('.messagereceived .msgreceive').each(function() {{
                            var html = $(this).html().trim();
                            if (html == '<span class="deletedx1"><i class="material-icons block">block</i> <em>Mensagem apagada</em></span>') {{
                                $(this).parent().css('margin-right', '40%');
                            }}
                        }});
                    }});
                </script>
            </body>'''  # noqa
    return messages_html


@app.route('/entrada/lastmsg', methods=['GET'])
def atualizar_mensagens():
    def get_friend_pic(user, id='default'):
        url = f'/chatx/.src/profiles/{id}.jpg'

        if secure_chat.get_profile_pic_url(user):
            return url
        else:
            return '/chatx/.src/profiles/default.jpg'

    usuario = set_user(
        session.get('password'),
        session.get('nickname'),
        session.get('username2')
    )
    secure_chat = SecureChat(user=usuario)
    amigos = usuario.get_friends
    lastmsg = usuario.get_private_room_last_message(usuario.nickname)
    # print(lastmsg)
    username = session.get('username2')
    usuario.user_server_name_extract

    if secure_chat.get_profile_pic_url(usuario):
        profile_pic_url = f'/chatx/.src/profiles/{session['id2']}.jpg'
    else:
        profile_pic_url = '/chatx/.src/profiles/default.jpg'

    lastmsg = usuario.get_private_room_last_message(session.get('nickname'))
    return render_template(
        'home/auto/lastmsg.html',
        username=username,
        server_name=usuario.server_name,
        amigos=amigos,
        user_id=session['id2'],
        get_profile_pic_url=get_friend_pic,
        lastmsg=lastmsg,
        profile_pic_url=profile_pic_url)


@app.route('/entrada/friendupdate', methods=['GET'])
def friend_update():
    def get_friend_pic(user, id='default'):
        url = f'/chatx/.src/profiles/{id}.jpg'

        if secure_chat.get_profile_pic_url(user):
            return url
        else:
            return '/chatx/.src/profiles/default.jpg'

    usuario = set_user(
        session.get('password'),
        session.get('nickname'),
        session.get('username2')
    )
    secure_chat = SecureChat(user=usuario)
    amigos = usuario.get_friends
    lastmsg = usuario.get_private_room_last_message(usuario.nickname)
    username = session.get('username2')
    usuario.user_server_name_extract

    if secure_chat.get_profile_pic_url(usuario):
        profile_pic_url = f'/chatx/.src/profiles/{session['id2']}.jpg'
    else:
        profile_pic_url = '/chatx/.src/profiles/default.jpg'

    lastmsg = usuario.get_private_room_last_message(session.get('nickname'))
    return render_template(
        'home/auto/friendupdate.html',
        username=username,
        server_name=usuario.server_name,
        amigos=amigos,
        user_id=session['id2'],
        get_profile_pic_url=get_friend_pic,
        lastmsg=lastmsg,
        profile_pic_url=profile_pic_url)


# Adicionar amigo
@app.route('/entrada/add_friend', methods=['POST'])
def add_friend():
    # Criar uma instância do usuário
    usuario = set_user(
        session.get('password'),
        session.get('nickname'),
        session.get('username2')
    )

    # Obter o nome de usuário do amigo do corpo da solicitação
    friend_username = request.form.get('friend_username')

    # Adicionar o amigo
    usuario.add_friend(friend_username)
    # print(friend_username)

    # Retornar uma resposta de sucesso
    return '', 204


@app.route('/entrada/lastservercheck', methods=['GET'])
def check_server():
    def get_friend_pic(user, id='default'):
        url = f'/chatx/.src/profiles/{id}.jpg'

        if secure_chat.get_profile_pic_url(user):
            return url
        else:
            return '/chatx/.src/profiles/default.jpg'

    usuario = set_user(
        session.get('password'),
        session.get('nickname'),
        session.get('username2')
    )
    secure_chat = SecureChat(user=usuario)
    amigos = usuario.get_friends
    lastmsg = usuario.get_private_room_last_message(usuario.nickname)
    lastserver = usuario.get_last_server_name()
    username = session.get('username2')
    usuario.user_server_name_extract

    if secure_chat.get_profile_pic_url(usuario):
        profile_pic_url = f'/chatx/.src/profiles/{session['id2']}.jpg'
    else:
        profile_pic_url = '/chatx/.src/profiles/default.jpg'

    lastmsg = usuario.get_private_room_last_message(session.get('nickname'))
    return render_template(
        'home/auto/lastserver.html',
        username=username,
        server_name=usuario.server_name,
        amigos=amigos,
        user_id=session['id2'],
        get_profile_pic_url=get_friend_pic,
        lastmsg=lastmsg,
        lastserver=lastserver,
        profile_pic_url=profile_pic_url)


# Responder mensagem
@app.route('/chat/reply', methods=['POST'])
def reply():
    usuario = set_user(
        session.get('password'),
        session.get('nickname'),
        session.get('username2'),
        server_name=session['server_name2']
    )

    secure_chat = SecureChat(user=usuario)
    username = session.get('username3')
    original_message = request.form.get('original_message', '')
    user_message = request.form.get('message', '')
    full_message = original_message + ' ' + user_message
    try:
        secure_chat.add_message(full_message, username)
    except Exception as e:
        print(f"Error: {e}")  # Debug print
    # Retorna uma resposta vazia com status code 204 (No Content)
    return ('', 204)


# Deletar todas as mensagens e arquivos da conversa
@app.route('/chat/delete_all', methods=['POST'])
def delete_all():
    usuario = set_user(
        session.get('password'),
        session.get('nickname'),
        session.get('username2'),
        server_name=session['server_name2']
    )

    servidor_name = session.get('server_file')

    folders = [
        directory_gen(servidor_name, 'img'),
        directory_gen(servidor_name, 'video'),
        directory_gen(servidor_name, 'others'),
        directory_gen(servidor_name, 'audio')
    ]

    for folder in folders:
        files = glob.glob(os.path.join(folder, '*'))
        for file in files:
            os.remove(file)

    secure_chat = SecureChat(user=usuario)
    secure_chat.delete_db('delete')
    return '', 204  # No Content


@app.route('/chat/delete', methods=['POST'])
def delete():
    usuario = set_user(
        session.get('password'),
        session.get('nickname'),
        session.get('username2'),
        server_name=session['server_name2']
    )

    secure_chat = SecureChat(user=usuario)
    message_id = request.form.get('message_id')
    # print(f"Message ID: {message_id}")
    secure_chat.delete_message(message_id)
    return redirect(url_for('chat'))


# Responsavel pelo upload e envio de arquivos
@app.route('/chat/upload', methods=['POST'])
def upload_file():
    servidor_name = session.get('server_file')
    photo = request.files['photo']
    _, ext = os.path.splitext(photo.filename)
    filename = f'{randint(1, 9999999)}{ext}'
    if 'photo' in request.files:
        photo = request.files['photo']
        if not allowed_file(filename):
            return redirect(url_for('chat'))

        if ext.lower() in extensoes_img:
            photo.save(os.path.join(directory_gen(servidor_name, 'img'), filename))  # noqa
            session['filename2'] = filename
            return jsonify({'filename': filename})
        elif ext.lower() in ('.mp4', '.webm'):
            photo.save(os.path.join(directory_gen(servidor_name, 'video'), filename))  # noqa
            session['filename2'] = filename
            return jsonify({'filename': filename})
        else:
            photo.save(os.path.join(directory_gen(servidor_name, 'others'), filename))  # noqa
            session['filename2'] = filename
            return jsonify({'filename': filename})

    return redirect(url_for('chat'))


# Responsavel pelo upload e envio de arquivos de áudio
@app.route('/chat/audio', methods=['POST'])
def audio_record():
    servidor_name = session.get('server_file')
    hora_e_data = datetime.now(tz).strftime('%d-%m-%Y_%H-%M-%S')
    file = request.files['file']
    _, ext = os.path.splitext(file.filename)
    filename = f'{hora_e_data}_{randint(11111, 99999)}{ext}'
    file.save(os.path.join(directory_gen(servidor_name, 'audio'), filename))
    return filename  # Retorne o nome do arquivo aqui


# Responsavel pelo envio da foto de perfil
@app.route('/entrada/upload_profile_picture', methods=['POST'])
def upload_profile_picture():
    usuario = set_user(
        session.get('password'),
        session.get('nickname'),
        session.get('username2')
    )
    print(f'Usuário: {usuario}')  # Debug

    secure_chat = SecureChat(user=usuario)
    if 'photo' in request.files:
        photo = request.files['photo']
        _, ext = os.path.splitext(photo.filename)
        print(f'Extensão do arquivo: {ext}')  # Debug

        user_id = session.get('id2')  # Obter o ID do usuário da sessão
        print(f'ID do usuário: {user_id}')  # Debug

        if user_id is None:
            return redirect(url_for('login'))

        filename = f'{user_id}{ext}'
        print(f'Nome do arquivo: {filename}')  # Debug

        if not allowed_profile(filename):
            return redirect(url_for('entrada'))

        # Salvar o arquivo com o novo nome
        photo.save(os.path.join(
            app.config['PROFILE_FOLDER'], f'{user_id}.jpg'))

        secure_chat.post_profile_pic_url(usuario, f'{user_id}.jpg')

        return redirect(url_for('entrada'))

    return redirect(url_for('entrada'))  # Redireciona para a rota de chat


# Remover amigo
@app.route('/entrada/remove_id', methods=['POST'])
def remove_sala():
    # Criar uma instância do usuário
    usuario = set_user(
        session.get('password'),
        session.get('nickname'),
        session.get('username2')
    )

    metodo = request.form.get('metodo')
    id = request.form.get('id')
    if metodo == 'room':
        usuario.delete_one_last_server_name(id)
        return '', 204
    elif metodo == 'friend':
        usuario.delete_friend(id)
        return '', 204
    elif metodo == 'chat':
        usuario.delete_msg_do_private_room(id)
        return '', 204

    # Retornar uma resposta de sucesso
    return redirect(url_for('entrada'))


# Solicita senha para abrir pagina de contatos
@app.route('/entrada/solicitar_senha', methods=['POST'])
def solicitar_senha():
    if session.get('password_verified', False):
        return jsonify({'password': True})

    user_password = session.get('password')
    password = request.form.get('password')

    if user_password == password:
        session['password_verified'] = False
        return jsonify({'password': True})

    if user_password == '':
        return jsonify({'password': False})

    return jsonify({'password': False})


@app.route('/chat/encrypt_server_name', methods=['GET', 'POST'])
def encrypt_server_name():
    def encrypt(server, se_ed):
        server = list(server)
        seed(se_ed)
        shuffle(server)
        return ''.join(server)

    servidor_name = request.form.get('server_name')
    print(f"Servidor: {servidor_name}")
    encryptedServer = encrypt(servidor_name, 40028922)
    return jsonify(encryptedServer=encryptedServer)


@app.route('/chatx/<path:filename>')
def custom_static(filename):
    return send_from_directory('data/chat', filename)
